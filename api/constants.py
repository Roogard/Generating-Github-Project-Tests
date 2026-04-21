"""Status-string constants shared across models, routes, and pipeline persistence."""
from enum import StrEnum


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE    = "done"
    ERROR   = "error"


class TestType(StrEnum):
    WHITEBOX = "whitebox"
    BLACKBOX = "blackbox"
