"""Test-execution runtimes.

A `Runtime` is a thin abstraction over "where pytest runs." Local mode shells
out via subprocess against a uv venv (or sys.executable as fallback). Docker
mode runs commands inside a stateless `docker run --rm` against a base image
with the host's per-run tempdir mounted at /work.

Either way, callers (test_runner, oracle) build a command, hand it to
`runtime.exec(...)`, and receive a `RuntimeResult` they can introspect
uniformly. Path translation between host and container is the runtime's
responsibility — callers always pass host paths.
"""
from src.runtime.base import Runtime, RuntimeResult
from src.runtime.local import LocalRuntime
from src.runtime.docker import DockerRuntime
from src.runtime.swtbench import SwtBenchRuntime, instance_image_name
from src.runtime.factory import build_runtime, RuntimeMode

__all__ = [
    "Runtime", "RuntimeResult", "LocalRuntime", "DockerRuntime",
    "SwtBenchRuntime", "instance_image_name",
    "build_runtime", "RuntimeMode",
]
