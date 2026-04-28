"""Runtime abstract base class + result type.

A Runtime owns the host-side scratch directory (`host_root`) and is
responsible for:

  - exposing a Python interpreter at `python_bin` (whichever path is correct
    for the runtime — host venv path for local, container venv path for
    docker)
  - running commands via `exec(cmd, cwd, ...)`
  - installing Python packages via `install_python_deps(...)`
  - allocating tempfile paths under `host_root` so the runtime sees them
    even when commands run inside a container
  - cleaning up via `shutdown()`

Path translation: callers always pass host paths. `translate(host_path)`
returns the path the running command should use. For LocalRuntime that's
identity. For DockerRuntime it's `host_root` → `/work` rebasing.
"""
from __future__ import annotations

import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RuntimeResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


class Runtime(ABC):
    """Per-run scratch + execution environment. One instance per pipeline run."""

    def __init__(self, host_root: str):
        self.host_root = os.path.abspath(host_root)
        os.makedirs(self.host_root, exist_ok=True)
        # Subdir for tempfiles (json reports, coverage data) — guaranteed to
        # exist inside the mounted volume so the running process can write
        # there and the host can read the result back.
        self._tmp_dir = os.path.join(self.host_root, "_runtime_tmp")
        os.makedirs(self._tmp_dir, exist_ok=True)

    # ── abstract: subclasses MUST implement ─────────────────────────────────

    @property
    @abstractmethod
    def python_bin(self) -> str:
        """Path to the Python interpreter to use for `python -m pytest` etc.

        For LocalRuntime this is a host path. For DockerRuntime it is a
        container path (since commands execute inside the container).
        """

    @abstractmethod
    def install_python_deps(self, packages: list[str], *, timeout: int | None = None) -> RuntimeResult:
        """Install Python packages into the runtime's venv. Packages may
        include host paths (e.g. a cloned repo dir) — implementations are
        responsible for translating them to runtime paths.
        """

    @abstractmethod
    def exec(
        self,
        cmd: list[str],
        *,
        cwd: str | None = None,
        timeout: int | None = None,
        env: dict | None = None,
    ) -> RuntimeResult:
        """Run a command. `cwd` is a host path; the runtime translates it.
        Strings inside `cmd` that look like host paths under host_root are
        translated automatically.
        """

    # ── concrete: shared helpers ────────────────────────────────────────────

    def translate(self, host_path: str) -> str:
        """Default identity. Overridden by DockerRuntime."""
        return host_path

    def tempfile_path(self, suffix: str = "") -> str:
        """Allocate a unique path inside the runtime-visible scratch area.

        The caller can write to / read from this path on the host side; if
        the running command also writes to it (after translation), both
        sides see the same file. Returns a HOST path — caller should
        translate before handing to a command via runtime.exec.
        """
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self._tmp_dir)
        os.close(fd)
        return path

    def shutdown(self) -> None:
        """Override for resource cleanup (LocalRuntime venv, Docker
        containers if any are kept alive). Default is no-op.
        """

    # ── per-exec preamble state ────────────────────────────────────────────
    #
    # Two knobs the oracle / test_runner can flip to make each exec see a
    # particular state of /testbed. No-ops on runtimes whose source lives
    # on a writable mount (Local, generic Docker user-repo path) — those
    # runtimes mutate the shared volume directly. Only SwtBenchRuntime
    # overrides because its source is baked into the image at /testbed
    # and every `docker run --rm` is stateless.

    def set_active_patch(self, container_patch_path: str | None) -> None:
        """Subsequent execs apply this patch inside /testbed before running."""

    def set_active_test_file(self, host_path: str | None,
                              container_path: str | None = None) -> None:
        """Subsequent execs copy `host_path` (host) into `container_path`
        (in-image) before running. Lets pytest see the test file under
        `/testbed/<name>` so rootdir resolution picks up repo-level
        conftest.py / pyproject.toml. Pass None for host_path to clear.
        """

    def in_image_test_file_path(self) -> str | None:
        """If the runtime relocates the test file (SwtBench), return where it
        lands inside the runtime. Otherwise None (caller uses translate())."""
        return None
