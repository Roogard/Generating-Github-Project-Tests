"""Runtime selection.

Default is Docker when the daemon is reachable AND the image exists; falls
back to LocalRuntime otherwise. Override via env var `GGPT_RUNTIME` set to
either `docker` or `local`. Image name override via `GGPT_DOCKER_IMAGE`.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from enum import StrEnum

from src.runtime.base import Runtime
from src.runtime.docker import DockerRuntime
from src.runtime.local import LocalRuntime


_DEFAULT_IMAGE = "ggpt-runtime"


class RuntimeMode(StrEnum):
    DOCKER = "docker"
    LOCAL = "local"


def _docker_available(image: str) -> bool:
    """Return True if `docker` is on PATH AND the daemon responds AND the
    image exists locally. We deliberately don't auto-pull; users opt into
    Docker by building the image first."""
    if not shutil.which("docker"):
        return False
    try:
        # 60s — a cold Docker Desktop daemon can take 20-30s for its first command.
        r = subprocess.run(["docker", "image", "inspect", image],
                           capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


def build_runtime(
    host_root: str,
    *,
    install_deps: bool = True,
    mode: RuntimeMode | None = None,
) -> Runtime:
    """Construct the right runtime for this run.

    Resolution order:
      1. Explicit `mode` argument (caller forces docker / local)
      2. `GGPT_RUNTIME` env var
      3. Docker if image is built and daemon is reachable
      4. Local fallback
    """
    image = os.environ.get("GGPT_DOCKER_IMAGE", _DEFAULT_IMAGE)

    if mode is None:
        env_mode = (os.environ.get("GGPT_RUNTIME") or "").strip().lower()
        if env_mode == "docker":
            mode = RuntimeMode.DOCKER
        elif env_mode == "local":
            mode = RuntimeMode.LOCAL

    if mode == RuntimeMode.DOCKER:
        return DockerRuntime(host_root, image=image, install_deps=install_deps)
    if mode == RuntimeMode.LOCAL:
        return LocalRuntime(host_root, install_deps=install_deps)

    # Auto-detect.
    if _docker_available(image):
        print(f"  [runtime] using DockerRuntime (image={image!r})")
        return DockerRuntime(host_root, image=image, install_deps=install_deps)
    print(f"  [runtime] using LocalRuntime (docker image {image!r} not found; "
          f"set GGPT_RUNTIME=docker after `docker build -f Dockerfile.runtime -t {image} .`)")
    return LocalRuntime(host_root, install_deps=install_deps)
