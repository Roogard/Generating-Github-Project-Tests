"""Input adapter dispatcher.

Two sources after the issue-driven pivot:
  - 'swtbench' → SwtBenchAdapter
  - 'repo'     → RepoAdapter (requires issue_text)

Both yield issue-scoped tasks. The 'single' (function-scoped) source is gone.
"""
from __future__ import annotations

from src.inputs.base import InputAdapter, PRESETS, force_rmtree
from src.inputs.repo import RepoAdapter
from src.inputs.swtbench import SwtBenchAdapter


def build_adapter(source: str, *, cfg: dict, request) -> InputAdapter:
    """Construct the right adapter from the unified RunRequest body.

    `request` is the Pydantic body from `api/routes.py`. We pull only the
    fields each adapter needs.
    """
    if source == "repo":
        if not getattr(request, "repo_url", None):
            raise ValueError("source='repo' requires repo_url")
        if not getattr(request, "issue_text", None):
            raise ValueError("source='repo' requires issue_text — the agent is issue-driven")
        return RepoAdapter(
            repo_url=request.repo_url,
            issue_text=request.issue_text,
            issue_title=getattr(request, "issue_title", "") or "",
            hints_text=getattr(request, "hints_text", "") or "",
            cfg=cfg,
            preset=request.preset,
            install_deps=getattr(request, "install_deps", True),
        )
    if source == "swtbench":
        if not getattr(request, "dataset", None):
            raise ValueError("source='swtbench' requires dataset")
        return SwtBenchAdapter(
            cfg=cfg,
            dataset=request.dataset,
            preset=request.preset,
            instance_limit=getattr(request, "instance_limit", None),
            instance_ids=getattr(request, "instance_ids", None),
            use_official_images=getattr(request, "use_official_images", True),
        )
    raise ValueError(f"Unknown source: {source!r}. Expected 'repo' or 'swtbench'")


__all__ = ["build_adapter", "InputAdapter", "PRESETS", "force_rmtree",
           "RepoAdapter", "SwtBenchAdapter"]
