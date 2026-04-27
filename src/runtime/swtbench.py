"""SwtBenchRuntime — uses an official per-instance Docker image.

Each SWE-bench Lite instance has a pre-built image at
`swebench/sweb.eval.x86_64.<instance_id_with_underscores>:latest` containing:

  - The repo cloned at `/testbed` at the right `base_commit`
  - A conda env with the era-correct Python, numpy, etc., already installed
  - The repo installed in editable mode

We reuse DockerRuntime for plumbing (mount, exec, path translation) but
override several things to make /testbed the effective working tree:

  1. The image is per-instance, not the generic `ggpt-runtime`.
  2. When a caller's `cwd` matches the host clone (`host_root/_repo`), we
     translate it to `/testbed` so pytest discovers `/testbed/conftest.py`,
     `/testbed/pyproject.toml`, etc.
  3. Each `docker run --rm` is stateless. To make pytest see our test
     file / gold patch INSIDE /testbed, we wrap every command with a
     bash preamble that copies/applies the requested state into /testbed
     before exec'ing the real command. Two hooks compose:
       - set_active_patch     → `git apply <patch>` inside /testbed
       - set_active_test_file → copies host test file → /testbed/<name>
     Without these, host-side writes against `host_root/_repo` are a
     PARALLEL clone the in-image pytest never sees.
  4. The image's `python` (on PATH inside the conda env) is the right
     interpreter, so we skip our venv build and `pip install` test deps
     into a derived image that's cached locally.
"""
from __future__ import annotations

import os
import shlex
import subprocess

from src.runtime.docker import DockerRuntime, _CONTAINER_ROOT


_TESTBED = "/testbed"
# Stable in-image location for the harness-generated test file. Lives at
# the /testbed root so pytest's rootdir resolution finds repo-level
# conftest.py / pyproject.toml on the way up.
_IN_IMAGE_TEST_FILE = "/testbed/test_ggpt_agent.py"


def instance_image_name(instance_id: str) -> str:
    """Map a SWE-bench instance_id to the official Docker image tag.

    `astropy__astropy-12907` → `swebench/sweb.eval.x86_64.astropy_1776_astropy-12907:latest`.
    The `__` → `_1776_` substitution is the SWE-bench convention for encoding
    the double-underscore separator that Docker tags can't include.
    """
    encoded = instance_id.replace("__", "_1776_")
    return f"swebench/sweb.eval.x86_64.{encoded}:latest"


class SwtBenchRuntime(DockerRuntime):
    def __init__(self, host_root: str, instance_id: str, *, install_deps: bool = True):
        image = instance_image_name(instance_id)
        # install_deps=False to skip our venv build — the image's own python
        # already has the era-correct env (conda).
        super().__init__(host_root, image=image, install_deps=False)
        self.instance_id = instance_id
        # `_repo` matches our convention from swtbench.py — host-side clone
        # parallel to /testbed. We map it onto /testbed so callers passing
        # cwd=repo_dir land in the right place.
        self._testbed_aliases = {
            os.path.normpath(os.path.join(self.host_root, "_repo")): _TESTBED,
        }
        # Two preamble hooks. None ⇒ no-op for that hook this exec.
        self._active_patch: str | None = None  # in-image path of patch file
        self._active_test_file: tuple[str, str] | None = None  # (host_path, in_image_path)
        if install_deps:
            self._ensure_derived_image()

    # ── overrides ───────────────────────────────────────────────────────────

    @property
    def python_bin(self) -> str:
        # The official SWT-Bench images install deps into a conda env named
        # `testbed`. The base image's PATH does NOT include that env unless
        # a login shell sources `/etc/profile.d/conda.sh`. With `docker run
        # <image> python ...` (no shell), `python` resolves to
        # /opt/miniconda3/bin/python (the BASE conda Python, missing pytest
        # and the repo's deps), which silently fails collection with
        # "No module named pytest". Use the env's python directly.
        return "/opt/miniconda3/envs/testbed/bin/python"

    def translate(self, host_path: str) -> str:
        """Override DockerRuntime's mount-relative translation.

        For host paths under one of `_testbed_aliases`, return the
        corresponding `/testbed/...` path so pytest cwd / PYTHONPATH point
        at the image's installed source. Other paths fall through to the
        base translation (`/work/...`).
        """
        host_path_norm = os.path.normpath(os.path.abspath(host_path))
        for host_alias, in_image in self._testbed_aliases.items():
            if host_path_norm == host_alias:
                return in_image
            prefix = host_alias + os.sep
            if host_path_norm.startswith(prefix):
                rel = host_path_norm[len(prefix):].replace(os.sep, "/")
                return f"{in_image}/{rel}"
        # Test file gets a special-case override — callers ask for the in-image
        # location via translate() so pytest's rootdir resolution lands inside
        # /testbed, not in /work/out where repo-level configs aren't visible.
        if self._active_test_file is not None:
            host_test, _in_image = self._active_test_file
            if os.path.normpath(os.path.abspath(host_test)) == host_path_norm:
                return _in_image
        return super().translate(host_path)

    def in_image_test_file_path(self) -> str | None:
        return self._active_test_file[1] if self._active_test_file else None

    # ── derived-image build ─────────────────────────────────────────────────

    def _derived_image_tag(self) -> str:
        """Tag for the per-instance image with our test-runner extras baked in."""
        encoded = self.instance_id.replace("__", "_1776_")
        return f"ggpt-swt-{encoded}:v2"

    def _ensure_derived_image(self) -> None:
        """Build a derived image FROM the official one with our test-runner
        deps (pytest-json-report, pytest-timeout) pre-installed. Cached:
        skips the build if the tag exists locally.
        """
        base_image = self.image  # currently the official sweb tag
        derived = self._derived_image_tag()

        # Skip if already built. 60s timeout because a cold Docker daemon
        # (Desktop just started) can take 20-30s to respond to its very
        # first command — 10s would falsely flag an unresponsive daemon.
        check = subprocess.run(
            ["docker", "image", "inspect", derived],
            capture_output=True, text=True, timeout=60,
        )
        if check.returncode == 0:
            self.image = derived
            return

        print(f"  [swtbench] building derived image {derived} (one-time, ~30s)")
        # Use the conda env's pip directly. Pinning matters: pytest-json-report
        # is sensitive to pytest version; let pip resolve constraints against
        # whatever pytest the image has.
        dockerfile = (
            f"FROM {base_image}\n"
            f"RUN /opt/miniconda3/envs/testbed/bin/pip install --no-cache-dir "
            f"pytest-json-report pytest-timeout >/dev/null 2>&1 || "
            f"/opt/miniconda3/envs/testbed/bin/pip install --no-cache-dir "
            f"pytest-json-report pytest-timeout\n"
        )
        r = subprocess.run(
            ["docker", "build", "-t", derived, "-"],
            input=dockerfile, capture_output=True, text=True, timeout=900,
        )
        if r.returncode != 0:
            tail = (r.stderr or r.stdout).strip().splitlines()[-8:]
            raise RuntimeError(
                f"derived image build failed: " +
                " | ".join(line.strip() for line in tail)
            )
        self.image = derived

    # ── preamble hooks ──────────────────────────────────────────────────────

    def set_active_patch(self, container_patch_path: str | None) -> None:
        self._active_patch = container_patch_path

    def set_active_test_file(self, host_path: str | None,
                              container_path: str | None = None) -> None:
        if host_path is None:
            self._active_test_file = None
            return
        in_image = container_path or _IN_IMAGE_TEST_FILE
        self._active_test_file = (os.path.abspath(host_path), in_image)

    # ── exec wrapping ──────────────────────────────────────────────────────

    def _build_preamble(self, cwd: str) -> list[str]:
        """Bash commands to run BEFORE the user's command, in order:
          1. Copy the active test file into /testbed/<name> (pytest visible)
          2. Apply the active patch via `git apply` inside /testbed
        Each `docker run --rm` is stateless, so both must be re-issued
        every exec.
        """
        steps: list[str] = []
        if self._active_test_file is not None:
            host_path, in_image = self._active_test_file
            in_work = self.translate_via_super(host_path)
            in_image_dir = os.path.dirname(in_image) or "/"
            steps.append(f"mkdir -p {shlex.quote(in_image_dir)}")
            steps.append(f"cp {shlex.quote(in_work)} {shlex.quote(in_image)}")
        if self._active_patch is not None:
            steps.append(f"cd /testbed")
            steps.append(
                f"git apply --whitespace=nowarn {shlex.quote(self._active_patch)}"
            )
        if steps:
            steps.append(f"cd {shlex.quote(cwd)}")
        return steps

    def translate_via_super(self, host_path: str) -> str:
        """Plain DockerRuntime translation (always /work/...), bypassing our
        /testbed-alias rewrite. Used inside the preamble for `cp` source
        paths — the SOURCE always lives in /work/<rel>, never in /testbed.
        """
        return DockerRuntime.translate(self, host_path)

    def _docker_run(self, cmd, *, cwd=_CONTAINER_ROOT, timeout=None, env=None):
        preamble = self._build_preamble(cwd)
        if not preamble:
            return super()._docker_run(cmd, cwd=cwd, timeout=timeout, env=env)
        inner = " ".join(shlex.quote(c) for c in cmd)
        wrapped = " && ".join(preamble) + f" && exec {inner}"
        return super()._docker_run(["bash", "-c", wrapped],
                                    cwd=cwd, timeout=timeout, env=env)
