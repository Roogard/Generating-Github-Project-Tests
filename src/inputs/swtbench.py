"""SwtBenchAdapter — turn a HuggingFace SWE-Bench dataset row into a RunBatch.

One batch per HF instance. Each batch contains exactly one task — issue +
repo. The agent localizes the relevant code itself via tools.

Adapter responsibilities, per instance:
  1. Clone the repo at `base_commit` into `host_root/_repo`
  2. Build a SwtBenchRuntime against the official sweb image
  3. Build the AgentTask carrying issue_text, issue_title, hints_text, gold_patch

Repos that don't use plain pytest (django/sympy/sphinx) are skipped via
`_UNSUPPORTED_REPOS` — those need per-repo test framework dispatch which
isn't wired yet.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Iterator

from src.inputs.base import InputAdapter, PRESETS
from src.logging import get_logger
from src.runtime.swtbench import SwtBenchRuntime
from src.types import AgentTask, RunBatch


logger = get_logger(__name__)


_HF_DATASETS = {
    "swtbench_lite":     "princeton-nlp/SWE-bench_Lite",
    "swtbench_verified": "princeton-nlp/SWE-bench_Verified",
}

# Repos we deliberately skip:
#   django/django, sympy/sympy, sphinx-doc/sphinx — don't use plain pytest.
#       Their canonical test commands (runtests.py / bin/test / tox) need
#       per-repo dispatch the runner doesn't have.
#   pytest-dev/pytest — pytest-on-pytest. Bugs live in pytest's collection /
#       fixture / parametrize machinery; the agent has to construct tests
#       that exercise pytest's internals from inside pytest, which is
#       structurally hard. On the full Lite run this repo produced 1/17
#       resolved with 23 F→F — a structural floor, not a tunable one.
_UNSUPPORTED_REPOS = {
    "django/django",
    "sympy/sympy",
    "sphinx-doc/sphinx",
    "pytest-dev/pytest",
}


def _load_dataset(dataset: str) -> list[dict]:
    if dataset not in _HF_DATASETS:
        raise ValueError(f"Unknown dataset: {dataset}. Expected one of {list(_HF_DATASETS)}")
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise RuntimeError(
            "The `datasets` package is required. Install with: pip install datasets"
        ) from e
    ds = load_dataset(_HF_DATASETS[dataset], split="test")
    return [dict(row) for row in ds]


def _clone_at(repo: str, commit: str, dest: str) -> None:
    """Clone github.com/<repo> at <commit>. Full history (not depth=1) so
    `git apply -R` downstream has the context it needs.
    """
    url = f"https://github.com/{repo}.git"
    subprocess.run(["git", "clone", "--quiet", url, dest], check=True)
    subprocess.run(["git", "-C", dest, "checkout", "--quiet", commit], check=True)


def _issue_title(problem_statement: str) -> str:
    for line in (problem_statement or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:200]
    return ""


class SwtBenchAdapter(InputAdapter):
    """One batch per HF instance, each containing one issue-driven task."""

    source = "swtbench"

    def __init__(
        self,
        *,
        cfg: dict,
        dataset: str = "swtbench_lite",
        preset: str = "default",
        instance_limit: int | None = None,
        instance_ids: list[str] | None = None,
        use_official_images: bool = True,
    ):
        if dataset not in _HF_DATASETS:
            raise ValueError(f"Unknown dataset: {dataset}")
        self.cfg = cfg
        self.preset_cfg = PRESETS.get(preset, PRESETS["default"])
        self.preset = preset
        self.dataset = dataset
        self.instance_limit = instance_limit
        self.instance_ids = set(instance_ids) if instance_ids else None
        self.use_official_images = use_official_images

    def iter_batches(self) -> Iterator[RunBatch]:
        logger.info("swtbench.dataset_load", dataset=_HF_DATASETS[self.dataset], split="test")
        rows = _load_dataset(self.dataset)
        if self.instance_ids:
            rows = [r for r in rows if r.get("instance_id") in self.instance_ids]
        if self.instance_limit:
            rows = rows[: self.instance_limit]

        logger.info("swtbench.batch_start",
                    dataset=self.dataset,
                    instances=len(rows),
                    max_llm_calls=self.preset_cfg["max_llm_calls"],
                    turn_cap=self.preset_cfg.get("agentic_turn_cap", 6),
                    official_images=self.use_official_images)

        for i, row in enumerate(rows, 1):
            logger.info("swtbench.instance", index=i, total=len(rows),
                        instance_id=row.get("instance_id"))
            yield from self._batch_for_instance(row)

    def _batch_for_instance(self, row: dict) -> Iterator[RunBatch]:
        instance_id = row["instance_id"]
        repo = row["repo"]
        base_commit = row["base_commit"]
        gold_patch = row.get("patch") or ""
        problem_statement = row.get("problem_statement") or ""
        hints_text = row.get("hints_text") or ""

        logger.info("swtbench.instance_setup",
                    instance_id=instance_id, repo=repo, base_commit=base_commit[:7])

        run_metadata = {
            "repo_url": f"swtbench:{instance_id}",
            "mode": "swtbench",
            "dataset": self.dataset,
            "benchmark_id": instance_id,
            "provider": self.cfg.get("provider"),
            "model": self.cfg.get("model"),
            "preset": self.preset,
        }

        # ── Skip cases yield empty batches with metadata so the runner
        # ── persists a clear ERROR Run row.
        if not gold_patch or not problem_statement:
            run_metadata["_skip_reason"] = "missing patch or problem_statement"
            yield RunBatch(run_metadata=run_metadata, tasks=[])
            return

        if repo in _UNSUPPORTED_REPOS:
            run_metadata["_skip_reason"] = (
                f"unsupported_test_framework: {repo} uses a non-pytest test "
                f"runner (see MAP_REPO_TO_TEST_FRAMEWORK in the SWT-Bench "
                f"reference harness). Plain pytest produces meaningless P→P "
                f"results because the repo's test framework is never invoked."
            )
            yield RunBatch(run_metadata=run_metadata, tasks=[])
            return

        # One per-instance host_root. Repo lives at host_root/_repo so the
        # runtime mount sees both clone and tests under one path.
        host_root = tempfile.mkdtemp(prefix=f"ggpt-swt-{instance_id}-")
        repo_dir = os.path.join(host_root, "_repo")
        runtime = None
        try:
            _clone_at(repo, base_commit, repo_dir)

            if self.use_official_images:
                logger.info("swtbench.official_image_pull", instance_id=instance_id)
                runtime = SwtBenchRuntime(host_root, instance_id, install_deps=True)
            else:
                # Generic ggpt-runtime — only works for repos that build cleanly
                # against Python 3.12 (not the typical SWT-Bench case).
                from src.inputs.repo import _setup_runtime as _generic_setup
                runtime, _ = _generic_setup(host_root, repo_dir, install_deps=True)

            instance_output = os.path.join(host_root, "out")
            os.makedirs(instance_output, exist_ok=True)

            run_metadata.update({
                "_host_root": host_root,
                "runtime": runtime,
            })

            task = AgentTask(
                source="swtbench",
                label=instance_id,
                instance_id=instance_id,
                dataset=self.dataset,
                repo_dir=repo_dir,
                runtime=runtime,
                issue_text=problem_statement,
                issue_title=_issue_title(problem_statement),
                hints_text=hints_text,
                gold_patch=gold_patch,
                cfg=self.cfg,
                out_dir=instance_output,
                timeout=self.preset_cfg["timeout"],
                max_llm_calls=self.preset_cfg["max_llm_calls"],
                agentic_turn_cap=self.preset_cfg.get("agentic_turn_cap", 6),
                per_test_timeout=self.preset_cfg.get("per_test_timeout"),
            )
            yield RunBatch(run_metadata=run_metadata, tasks=[task])
        except Exception as e:
            logger.error("swtbench.instance_setup_error",
                         err_type=type(e).__name__, err=str(e))
            run_metadata["_skip_reason"] = f"setup_error: {type(e).__name__}: {e}"
            run_metadata["_host_root"] = host_root
            run_metadata["runtime"] = runtime
            yield RunBatch(run_metadata=run_metadata, tasks=[])
