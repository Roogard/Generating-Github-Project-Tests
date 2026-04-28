"""Post-hoc graders.

Graders run AFTER `run_agent` returns, never inside the harness loop. They
read the final test file produced by the agent and grade it against
ground-truth signal carried on the `AgentTask` (e.g. `gold_patch` for the
SWT-Bench F→P oracle).
"""
from src.graders.oracle import grade_with_oracle

__all__ = ["grade_with_oracle"]
