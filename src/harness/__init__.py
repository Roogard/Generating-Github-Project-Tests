"""Harness package — per-task state, pytest feedback, and the pipeline.

Imports preserved for back-compat with the pre-split harness.py:

  from src.harness import HarnessContext, Feedback, BudgetExhausted, run_harness

The package is internally split into:

  state.py     — HarnessContext, BudgetExhausted, write_test_file, read_test_file
  feedback.py  — Feedback, build_feedback
  pipeline.py  — run_harness, finalize
"""
from src.harness.feedback import Feedback, build_feedback
from src.harness.pipeline import finalize, run_harness
from src.harness.state import (
    BudgetExhausted,
    HarnessContext,
    read_test_file,
    write_test_file,
)

__all__ = [
    "BudgetExhausted",
    "Feedback",
    "HarnessContext",
    "build_feedback",
    "finalize",
    "read_test_file",
    "run_harness",
    "write_test_file",
]
