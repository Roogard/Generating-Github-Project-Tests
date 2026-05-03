"""LocalRuntime — runs commands as host subprocesses.

Mirrors the legacy `_setup_run_env` behavior: build a uv venv inside the
run's host_root if uv is available, otherwise fall back to the server's
sys.executable (with a warning). Used when Docker is unavailable or when
the user explicitly opts out via GGPT_RUNTIME=local.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

from src.logging import get_logger
from src.runtime.base import Runtime, RuntimeResult


logger = get_logger(__name__)


class LocalRuntime(Runtime):
    def __init__(self, host_root: str, *, install_deps: bool = True):
        super().__init__(host_root)
        self._uv = shutil.which("uv")
        self._venv_dir: str | None = None
        self._python_bin: str = sys.executable

        if install_deps and self._uv:
            venv_dir = os.path.join(self.host_root, ".venv")
            r = subprocess.run([self._uv, "venv", venv_dir, "--quiet"],
                               capture_output=True, text=True)
            if r.returncode == 0:
                self._venv_dir = venv_dir
                self._python_bin = os.path.join(
                    venv_dir,
                    "Scripts" if os.name == "nt" else "bin",
                    "python.exe" if os.name == "nt" else "python",
                )
            else:
                logger.warning("runtime_local.uv_venv_failed",
                               stderr=r.stderr.strip()[:200],
                               fallback=sys.executable)
        elif install_deps and not self._uv:
            logger.warning("runtime_local.no_uv",
                           interpreter=sys.executable,
                           note="no per-run isolation")

    @property
    def python_bin(self) -> str:
        return self._python_bin

    def install_python_deps(self, packages: list[str], *, timeout: int | None = None) -> RuntimeResult:
        if not packages:
            return RuntimeResult(returncode=0, stdout="", stderr="")
        if self._uv:
            cmd = [self._uv, "pip", "install", "--python", self._python_bin, "--quiet", *packages]
        else:
            cmd = [self._python_bin, "-m", "pip", "install", "--quiet", *packages]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return RuntimeResult(returncode=r.returncode, stdout=r.stdout, stderr=r.stderr)
        except subprocess.TimeoutExpired:
            return RuntimeResult(returncode=-1, stdout="", stderr=f"install timed out after {timeout}s",
                                 timed_out=True)

    def exec(
        self,
        cmd: list[str],
        *,
        cwd: str | None = None,
        timeout: int | None = None,
        env: dict | None = None,
    ) -> RuntimeResult:
        try:
            r = subprocess.run(
                cmd,
                cwd=cwd, env=env or None,
                capture_output=True, text=True, timeout=timeout,
            )
            return RuntimeResult(returncode=r.returncode, stdout=r.stdout, stderr=r.stderr)
        except subprocess.TimeoutExpired:
            return RuntimeResult(returncode=-1, stdout="", stderr=f"command timed out after {timeout}s",
                                 timed_out=True)

    def shutdown(self) -> None:
        if self._venv_dir and os.path.isdir(self._venv_dir):
            shutil.rmtree(self._venv_dir, ignore_errors=True)
