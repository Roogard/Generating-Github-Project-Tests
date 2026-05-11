"""DockerRuntime — runs commands inside `docker run --rm` against a base image.

The harness's per-run host_root is bind-mounted at /work inside the
container. A venv lives at /work/.venv (host-visible at <host_root>/.venv)
so packages persist across stateless `docker run --rm` invocations.

Path translation: any host path under host_root becomes /work/<rel> inside
the container. Cross-mount paths are passed through unchanged (caller's
responsibility to keep paths under the mount).

Defaults to image `ggpt-runtime` — built from `Dockerfile.runtime`. Override
via env var `GGPT_DOCKER_IMAGE`.
"""
from __future__ import annotations

import os
import shlex
import subprocess

from src.logging import get_logger
from src.runtime.base import Runtime, RuntimeResult


logger = get_logger(__name__)

_CONTAINER_ROOT = "/work"
_VENV_REL = ".venv"


class DockerRuntime(Runtime):
    def __init__(
        self,
        host_root: str,
        *,
        image: str = "ggpt-runtime",
        install_deps: bool = True,
    ):
        super().__init__(host_root)
        self.image = image
        self._venv_built = False

        if install_deps:
            # Build the venv inside the mounted volume so it persists across
            # subsequent stateless docker-run invocations. With `docker run
            # --rm`, anything installed into the container's site-packages
            # is discarded the moment the command exits — so without this
            # venv on the mount, `pip install` writes to oblivion and the
            # next `docker run` for pytest finds nothing installed. There
            # is no useful fallback here: fail loud.
            r = self._docker_run(
                ["python", "-m", "venv", f"{_CONTAINER_ROOT}/{_VENV_REL}"],
                cwd=_CONTAINER_ROOT, timeout=60,
            )
            if r.returncode == 0:
                self._venv_built = True
            else:
                logger.error("runtime_docker.venv_build_failed",
                             returncode=r.returncode,
                             timed_out=r.timed_out,
                             stdout_tail=(r.stdout or "").strip()[-500:],
                             stderr_tail=(r.stderr or "").strip()[-500:])
                raise RuntimeError(
                    f"Docker venv build failed (returncode={r.returncode}, "
                    f"timed_out={r.timed_out}). With `docker run --rm` the "
                    "venv MUST live on the mounted volume — there is no "
                    "viable fallback. Common causes: (1) the harness's "
                    "subprocess was killed by an external reloader (e.g. "
                    "uvicorn --reload watching the project root — exclude "
                    "eval_output/ or use --reload-dir api --reload-dir src); "
                    "(2) the Docker daemon went away mid-call. "
                    f"stderr_tail={(r.stderr or '').strip()[-300:]!r}"
                )

    def translate(self, host_path: str) -> str:
        host_root_norm = self.host_root.replace("\\", "/").rstrip("/")
        host_path_abs = os.path.abspath(host_path).replace("\\", "/")
        if host_path_abs == host_root_norm:
            return _CONTAINER_ROOT
        prefix = host_root_norm + "/"
        if host_path_abs.startswith(prefix):
            rel = host_path_abs[len(prefix):]
            return f"{_CONTAINER_ROOT}/{rel}"
        return host_path  # outside the mount — caller's problem

    @property
    def python_bin(self) -> str:
        # Container path. Falls back to system python if venv build failed.
        if self._venv_built:
            return f"{_CONTAINER_ROOT}/{_VENV_REL}/bin/python"
        return "python"

    def install_python_deps(self, packages: list[str], *, timeout: int | None = None) -> RuntimeResult:
        if not packages:
            return RuntimeResult(returncode=0, stdout="", stderr="")
        translated = [self._maybe_translate(p) for p in packages]
        cmd = [self.python_bin, "-m", "pip", "install", "--quiet", *translated]
        return self._docker_run(cmd, cwd=_CONTAINER_ROOT, timeout=timeout)

    def exec(
        self,
        cmd: list[str],
        *,
        cwd: str | None = None,
        timeout: int | None = None,
        env: dict | None = None,
    ) -> RuntimeResult:
        c_cmd = [self._maybe_translate(c) if isinstance(c, str) else c for c in cmd]
        c_cwd = self.translate(cwd) if cwd else _CONTAINER_ROOT
        return self._docker_run(c_cmd, cwd=c_cwd, timeout=timeout, env=env)

    def shutdown(self) -> None:
        # `docker run --rm` cleans up containers automatically; the venv lives
        # inside host_root which the caller (pipeline) removes via rmtree.
        pass

    def _maybe_translate(self, value: str) -> str:
        # Translate only strings that look like absolute host paths under the
        # mount. Avoids munging argv flags (`-q`, `--no-header`, ...) or
        # values that just happen to contain slashes.
        if not isinstance(value, str):
            return value
        if not os.path.isabs(value):
            return value
        return self.translate(value)

    def _docker_run(
        self,
        cmd: list[str],
        *,
        cwd: str = _CONTAINER_ROOT,
        timeout: int | None = None,
        env: dict | None = None,
    ) -> RuntimeResult:
        host_root_mount = self.host_root.replace("\\", "/")
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{host_root_mount}:{_CONTAINER_ROOT}",
            "-w", cwd,
        ]
        if env:
            for k, v in env.items():
                docker_cmd += ["-e", f"{k}={v}"]
        docker_cmd += [self.image, *cmd]

        try:
            r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
            return RuntimeResult(returncode=r.returncode, stdout=r.stdout, stderr=r.stderr)
        except subprocess.TimeoutExpired:
            # The container will linger briefly until docker reaps it; --rm
            # handles eventual cleanup.
            return RuntimeResult(
                returncode=-1, stdout="",
                stderr=f"docker exec timed out after {timeout}s; cmd={shlex.join(cmd)[:200]}",
                timed_out=True,
            )
        except FileNotFoundError:
            return RuntimeResult(
                returncode=-1, stdout="",
                stderr="`docker` not on PATH. Install Docker Desktop or set GGPT_RUNTIME=local.",
            )
