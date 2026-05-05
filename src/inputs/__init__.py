"""Input adapter package.

After the issue-driven pivot — and the move of run-creation off the webapp
and into the GitHub Action (src/action_entrypoint.py) — only the issue-text
RepoAdapter is wired up here. The SWT-Bench batch adapter and the
build_adapter dispatcher were dropped along with the webapp's submit forms.
"""
from __future__ import annotations

from src.inputs.base import InputAdapter, PRESETS, force_rmtree
from src.inputs.repo import RepoAdapter


__all__ = ["InputAdapter", "PRESETS", "force_rmtree", "RepoAdapter"]
