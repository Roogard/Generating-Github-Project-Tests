"""Runtime selection.

Default is Docker when the daemon is reachable AND the image exists; falls
back to LocalRuntime otherwise. Override via env var `GGPT_RUNTIME` set to
either `docker` or `local`. Image name override via `GGPT_DOCKER_IMAGE`.
Both env vars are read by `src.config` at import time.
"""
from __future__ import annotations

import shutil
import subprocess
from enum import StrEnum

from src import config
from src.logging import get_logger
from src.runtime.base import Runtime
from src.runtime.docker import DockerRuntime
from src.runtime.local import LocalRuntime


logger = get_logger(__name__)


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
      2. `config.RUNTIME` (from env var GGPT_RUNTIME)
      3. Docker if image is built and daemon is reachable
      4. Local fallback
    """
    image = config.DOCKER_IMAGE

    if mode is None:
        if config.RUNTIME == "docker":
            mode = RuntimeMode.DOCKER
        elif config.RUNTIME == "local":
            mode = RuntimeMode.LOCAL

    if mode == RuntimeMode.DOCKER:
        return DockerRuntime(host_root, image=image, install_deps=install_deps)
    if mode == RuntimeMode.LOCAL:
        return LocalRuntime(host_root, install_deps=install_deps)

    # Auto-detect.
    if _docker_available(image):
        logger.info("runtime.select", kind="docker", image=image)
        return DockerRuntime(host_root, image=image, install_deps=install_deps)
    logger.info("runtime.select", kind="local", reason="docker_image_not_found",
                image_hint=image)
    return LocalRuntime(host_root, install_deps=install_deps)
