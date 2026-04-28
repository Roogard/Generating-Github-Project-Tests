"""RepoAdapter — turn (GitHub URL, issue text) into a RunBatch.

Issue-driven: the user supplies a repo and an issue describing a bug. The
adapter clones the repo at HEAD, builds a runtime, and yields one task —
the agent localizes the relevant code itself via tools.

Adapter responsibilities:
  1. Clone repo at HEAD into `host_root/_repo`
  2. Build a Runtime (Local or Docker) and install deps
  3. Build the AgentTask carrying the issue + tools-ready repo
"""
from __future__ import annotations

import os
import subprocess
from typing import Iterator

from dotenv import load_dotenv

from src.inputs.base import InputAdapter, PRESETS, force_rmtree
from src.runtime.factory import build_runtime
from src.types import AgentTask, RunBatch


def _clone_repo(url: str, target_dir: str) -> None:
    subprocess.run(["git", "clone", "--depth=1", url, target_dir], check=True)


load_dotenv()


_BASE_TEST_PKGS = ["pytest", "pytest-json-report", "pytest-timeout", "coverage"]
# Common requirements-file names in priority order. We pick the first that
# exists; users with multiple should put their primary in `requirements.txt`.
_REQUIREMENTS_FALLBACKS = (
    "requirements-dev.txt", "requirements_dev.txt",
    "requirements-test.txt", "requirements_test.txt",
    "requirements.txt",
)


def _detect_install_targets(repo_dir: str) -> list[str]:
    """pip-install argument list for an arbitrary user repo.

    Strategy:
      1. setup.py / pyproject.toml present → `pip install -e <repo_dir>`
      2. Append `-r requirements*.txt` for the most-specific file present
      3. Neither → return [] (caller skips install)

    Returns absolute paths. Relative paths leak Windows backslashes through
    to commands run inside Linux containers, where pip then misparses them
    as malformed requirement specs.
    """
    repo_dir = os.path.abspath(repo_dir)
    targets: list[str] = []
    if (os.path.isfile(os.path.join(repo_dir, "setup.py")) or
            os.path.isfile(os.path.join(repo_dir, "pyproject.toml"))):
        targets.extend(["-e", repo_dir])
    for name in _REQUIREMENTS_FALLBACKS:
        path = os.path.join(repo_dir, name)
        if os.path.isfile(path):
            targets.extend(["-r", path])
            break
    return targets


def _setup_runtime(host_root: str, repo_dir: str, *, install_deps: bool):
    """Build a Runtime and install test deps + the repo. Returns
    `(runtime, install_result)`. Caller must call `runtime.shutdown()`.
    """
    runtime = build_runtime(host_root, install_deps=install_deps)
    install_result = None
    if install_deps:
        pkgs = list(_BASE_TEST_PKGS) + _detect_install_targets(repo_dir)
        install_result = runtime.install_python_deps(pkgs, timeout=600)
        if install_result.returncode != 0:
            tail = install_result.stderr.strip().splitlines()[-8:]
            print(f"  [repo-adapter] runtime deps install FAILED (rc={install_result.returncode}):")
            for line in tail:
                print(f"    {line[:200]}")
    return runtime, install_result


def _issue_title(issue_text: str) -> str:
    for line in (issue_text or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:200]
    return ""


class RepoAdapter(InputAdapter):
    """Adapter for plain GitHub-URL inputs. Requires an issue."""

    source = "repo"

    def __init__(
        self,
        repo_url: str,
        *,
        issue_text: str,
        cfg: dict,
        preset: str = "default",
        issue_title: str = "",
        hints_text: str = "",
        install_deps: bool = True,
        output_dir: str = "eval_output",
    ):
        if not issue_text or not issue_text.strip():
            raise ValueError("RepoAdapter requires non-empty issue_text — the agent is issue-driven")
        self.repo_url = repo_url
        self.issue_text = issue_text
        self.issue_title = issue_title or _issue_title(issue_text)
        self.hints_text = hints_text or ""
        self.cfg = cfg
        self.preset_cfg = PRESETS.get(preset, PRESETS["default"])
        self.preset = preset
        self.install_deps = install_deps
        self.output_dir = output_dir

    def iter_batches(self) -> Iterator[RunBatch]:
        project_name = self.repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        run_dir = os.path.abspath(os.path.join(self.output_dir, project_name))
        os.makedirs(run_dir, exist_ok=True)
        repo_dir = os.path.join(run_dir, "_repo")

        # Idempotent clone — Windows holds read-only attrs on .git pack files
        # that defeat ignore_errors=True. force_rmtree chmods them out.
        force_rmtree(repo_dir)
        print(f"\nCloning {self.repo_url}...")
        _clone_repo(self.repo_url, repo_dir)

        print("Building runtime ...")
        runtime, install_result = _setup_runtime(
            run_dir, repo_dir, install_deps=self.install_deps,
        )

        run_metadata = {
            "repo_url": self.repo_url,
            "mode": "repo",
            "provider": self.cfg.get("provider"),
            "model": self.cfg.get("model"),
            "preset": self.preset,
            "output_dir": run_dir,
            "runtime": runtime,
        }

        if install_result is not None and install_result.returncode != 0:
            tail = (install_result.stderr or install_result.stdout).strip().splitlines()[-12:]
            err_msg = "Repo dependencies failed to install:\n" + "\n".join(tail)
            run_metadata["_install_error"] = err_msg
            yield RunBatch(run_metadata=run_metadata, tasks=[])
            return

        task = AgentTask(
            source="repo",
            label=f"{project_name}: {self.issue_title[:80]}",
            repo_dir=repo_dir,
            runtime=runtime,
            issue_text=self.issue_text,
            issue_title=self.issue_title,
            hints_text=self.hints_text,
            gold_patch=None,  # plain repo runs have no gold patch → no oracle grading
            cfg=self.cfg,
            out_dir=run_dir,
            timeout=self.preset_cfg["timeout"],
            max_llm_calls=self.preset_cfg["max_llm_calls"],
            agentic_turn_cap=self.preset_cfg.get("agentic_turn_cap", 6),
            per_test_timeout=self.preset_cfg.get("per_test_timeout"),
        )
        yield RunBatch(run_metadata=run_metadata, tasks=[task])
