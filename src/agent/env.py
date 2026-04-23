"""TestGenEnv — the agent's sandbox for one function-under-test.

Holds:
  - the target function + repo state
  - the single test file the agent edits
  - turn counter + max_turns
  - benchmark_context (never exposed to the agent) for oracle-stability checks
  - history of (action, args, observation) for telemetry

Exposes tool_* methods that return compact strings for the agent to read, and
a summary() that aggregates metrics for DB persistence. All buggy↔fixed file
swaps happen inside tool_check_oracle_stability and summary — the agent never
sees the fixed source or the fixed file path.
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from src.test_runner import run_tests as _pytest_run, measure_coverage as _pytest_cov


_LONGREPR_CAP = 300


def _strip_relative_imports(code: str) -> str:
    return "\n".join(
        line for line in code.splitlines()
        if not re.match(r'^\s*(from\s+\.|\bimport\s+\.)', line)
    )


def _compact_run(result: dict) -> str:
    passed = len(result.get("passed", []))
    failed_names = result.get("failed", [])
    error_names = result.get("errors", [])
    lines = [f"{passed} passed, {len(failed_names)} failed, {len(error_names)} errors"]
    for i, name in enumerate(failed_names):
        detail = (result.get("failure_details") or [None] * (i + 1))[i] or {}
        longrepr = (detail.get("longrepr") or "").strip()
        if len(longrepr) > _LONGREPR_CAP:
            longrepr = longrepr[:_LONGREPR_CAP] + "...[truncated]"
        lines.append(f"- {name}: FAILED — {longrepr}")
    for i, name in enumerate(error_names):
        detail = (result.get("error_details") or [None] * (i + 1))[i] or {}
        longrepr = (detail.get("longrepr") or "").strip()
        if len(longrepr) > _LONGREPR_CAP:
            longrepr = longrepr[:_LONGREPR_CAP] + "...[truncated]"
        lines.append(f"- {name}: ERROR — {longrepr}")
    return "\n".join(lines)


def _compact_coverage(cov: dict, fn_source: str, fn_start_line: int) -> str:
    if cov.get("error"):
        return f"coverage error: {cov['error']}"
    pct = cov.get("coverage_pct", 0.0)
    uncovered = cov.get("uncovered_lines", []) or []
    if not uncovered:
        return f"coverage: {pct:.0f}% — all lines covered"
    src_lines = fn_source.splitlines()
    shown = []
    for lineno in uncovered[:15]:
        idx = lineno - fn_start_line
        src = src_lines[idx].rstrip() if 0 <= idx < len(src_lines) else ""
        shown.append(f"  L{lineno}: {src}")
    more = f" (+{len(uncovered) - 15} more)" if len(uncovered) > 15 else ""
    return f"coverage: {pct:.0f}%\nuncovered lines{more}:\n" + "\n".join(shown)


def _name_only(test_nodeid: str) -> str:
    return test_nodeid.split("::")[-1]


class TestGenEnv:
    """One instance per target function. Lifetime = one run_agent() call."""

    def __init__(
        self,
        fn: dict,
        *,
        repo_dir: str,
        test_dir: str,
        python_bin: str | None = None,
        timeout: int = 60,
        max_turns: int = 4,
        benchmark_context: dict | None = None,
        examples_dir: Path | None = None,
    ):
        self.fn = fn
        self.repo_dir = repo_dir
        self.test_dir = test_dir
        self.python_bin = python_bin
        self.timeout = timeout
        self.max_turns = max_turns
        self.benchmark_context = benchmark_context
        self.examples_dir = examples_dir or (Path(__file__).parent / "examples" / "golden")

        os.makedirs(test_dir, exist_ok=True)
        conftest = os.path.join(test_dir, "conftest.py")
        if not os.path.isfile(conftest):
            with open(conftest, "w", encoding="utf-8") as f:
                f.write(f"import sys; sys.path.insert(0, {repr(os.path.abspath(repo_dir))})\n")

        self.test_file_path = os.path.join(test_dir, "test_agent.py")
        self.turn = 0
        self.done = False
        self.finish_reason: str | None = None
        self.history: list[dict] = []
        self.last_run: dict | None = None
        self.last_cov: dict | None = None
        self.silent_turns = 0  # for loop termination when agent stops calling tools

    # ── public driver API ────────────────────────────────────────────────

    def reset(self) -> str:
        """Return the initial observation shown to the agent."""
        fn = self.fn
        import_path = fn["file_path"].replace("\\", "/").replace("/", ".").replace(".py", "")
        if fn.get("class_name"):
            import_line = f"from {import_path} import {fn['class_name']}  # `{fn['name']}` is a method on `{fn['class_name']}`"
        else:
            import_line = f"from {import_path} import {fn['name']}"

        mode_note = (
            "**Benchmark mode:** `check_oracle_stability` is available. "
            "Call it before `finish` to verify no tests are F→F spurious."
            if self.benchmark_context else
            "**Standalone mode:** no oracle available; focus on coverage + non-brittle assertions."
        )

        parts = [
            f"# Target: `{fn['name']}`",
            f"**File:** `{fn['file_path']}`  (lines {fn['start_line']}–{fn['end_line']})",
            f"**Import (use exactly):** `{import_line}`",
            "",
            mode_note,
            "",
            f"**Budget:** up to {self.max_turns} tool-call turns. Call `finish` when satisfied.",
            "",
            "## Function source",
            f"```python\n{fn['source']}\n```",
        ]
        if fn.get("spec"):
            parts.append("\n## Repo README (excerpt)")
            parts.append(fn["spec"][:1500])
        if fn.get("callees"):
            parts.append("\n## Internal helpers (context — DO NOT test these directly)")
            for c in fn["callees"]:
                parts.append(f"```python\n{c['source']}\n```")
        return "\n".join(parts)

    def step(self, tool_name: str, args: dict) -> str:
        """Dispatch one tool call. Returns the observation string.

        The turn counter lives on the LLM-call loop, not here — batched tool
        calls in one LLM response share a turn.
        """
        handler = getattr(self, f"tool_{tool_name}", None)
        if handler is None:
            obs = f"ERROR: unknown tool '{tool_name}'. Available: view_function, view_coverage, run_tests, check_oracle_stability, search_similar_tests, view_golden_example, write_test_file, finish."
        else:
            try:
                obs = handler(**(args or {}))
            except TypeError as e:
                obs = f"ERROR calling {tool_name}: {e}"
            except Exception as e:
                obs = f"ERROR in {tool_name}: {type(e).__name__}: {e}"
        self.history.append({"turn": self.turn, "tool": tool_name, "args": args, "observation_preview": obs[:400]})
        return obs

    def is_done(self) -> bool:
        return self.done or self.turn >= self.max_turns

    # ── tools (called from src/agent/tools.py) ───────────────────────────

    def tool_view_function(self) -> str:
        fn = self.fn
        src_lines = fn["source"].splitlines()
        start = fn.get("start_line", 1)
        numbered = "\n".join(f"{start + i:4d}  {ln}" for i, ln in enumerate(src_lines))
        out = [f"# {fn['name']}  ({fn['file_path']})", "```python", numbered, "```"]
        if fn.get("callees"):
            out.append("\n# Internal helpers (context only, do not test)")
            for c in fn["callees"]:
                out.append(f"```python\n{c['source']}\n```")
        return "\n".join(out)

    def tool_run_tests(self) -> str:
        if not os.path.isfile(self.test_file_path):
            return "ERROR: no test file yet. Call write_test_file first."
        result = _pytest_run(
            self.test_file_path, self.repo_dir,
            timeout=self.timeout, python_bin=self.python_bin,
        )
        self.last_run = result
        return _compact_run(result)

    def tool_view_coverage(self) -> str:
        if not os.path.isfile(self.test_file_path):
            return "ERROR: no test file yet. Call write_test_file first."
        cov = _pytest_cov(
            self.test_file_path, self.fn, self.repo_dir,
            timeout=self.timeout, python_bin=self.python_bin,
        )
        self.last_cov = cov
        return _compact_coverage(cov, self.fn.get("source", ""), self.fn.get("start_line", 1))

    def tool_check_oracle_stability(self) -> str:
        if not self.benchmark_context:
            return "ERROR: oracle stability is only available in benchmark mode."
        if not os.path.isfile(self.test_file_path):
            return "ERROR: no test file yet. Call write_test_file first."

        ctx = self.benchmark_context
        buggy_src = ctx["buggy_path"]
        fixed_src = ctx["fixed_path"]
        target = ctx["target_path"]

        # 1. Run on buggy (current state — ensure it is the buggy version)
        shutil.copy(buggy_src, target)
        buggy_result = _pytest_run(
            self.test_file_path, self.repo_dir,
            timeout=self.timeout, python_bin=self.python_bin,
        )
        buggy_passed = {_name_only(n) for n in buggy_result.get("passed", [])}
        buggy_failed = {_name_only(n) for n in buggy_result.get("failed", [])}

        # 2. Swap in fixed, run again
        shutil.copy(fixed_src, target)
        fixed_result = _pytest_run(
            self.test_file_path, self.repo_dir,
            timeout=self.timeout, python_bin=self.python_bin,
        )
        fixed_passed = {_name_only(n) for n in fixed_result.get("passed", [])}
        fixed_failed = {_name_only(n) for n in fixed_result.get("failed", [])}

        # 3. Restore buggy so the agent continues iterating against it
        shutil.copy(buggy_src, target)

        # 4. Label each test
        all_names = buggy_passed | buggy_failed | fixed_passed | fixed_failed
        f2p = f2f = p2p = p2f = 0
        lines = []
        for name in sorted(all_names):
            if name in buggy_failed and name in fixed_passed:
                label = "F→P (DETECTS BUG — keep)"
                f2p += 1
            elif name in buggy_failed and name in fixed_failed:
                label = "F→F (SPURIOUS — delete or weaken)"
                f2f += 1
            elif name in buggy_passed and name in fixed_passed:
                label = "P→P (stable neutral)"
                p2p += 1
            elif name in buggy_passed and name in fixed_failed:
                label = "P→F (REGRESSION — remove)"
                p2f += 1
            else:
                label = "?"
            lines.append(f"- {name}: {label}")

        self.last_run = buggy_result  # keep last_run pointing at buggy (agent's working state)
        summary = f"Oracle stability: F→P={f2p}  F→F={f2f}  P→F={p2f}  P→P={p2p}"
        hint = ""
        if f2f or p2f:
            hint = "\nRevise: delete/replace F→F tests; investigate P→F regressions."
        elif f2p:
            hint = "\nGood — you have detections and no spurious tests. You may finish."
        return summary + "\n\n" + "\n".join(lines) + hint

    def tool_search_similar_tests(self, query: str = "", k: int = 3) -> str:
        if not query.strip():
            return "ERROR: query is required."
        try:
            from src.vectordb import retrieve_examples
            examples = retrieve_examples(query, n_results=max(1, min(k, 5)))
        except Exception as e:
            return f"ERROR: vectordb unavailable: {e}"
        if not examples:
            return "No similar examples found in memory."
        out = [f"{len(examples)} example(s) from memory:"]
        for i, ex in enumerate(examples, 1):
            out.append(f"\n### Example {i}: `{ex['fn_name']}`  (passed={ex.get('passed', 0)})")
            out.append(f"```python\n{ex['fn_source']}\n```")
            out.append(f"Tests:\n```python\n{ex['test_code']}\n```")
        return "\n".join(out)

    def tool_view_golden_example(self, name: str = "") -> str:
        if not self.examples_dir.is_dir():
            return "No golden examples installed."
        if not name:
            available = sorted(p.name for p in self.examples_dir.iterdir() if p.is_dir())
            if not available:
                return "No golden examples installed."
            return "Available golden examples (call with name=<one of these>):\n" + "\n".join(f"- {n}" for n in available)
        folder = self.examples_dir / name
        if not folder.is_dir():
            return f"ERROR: no golden example named '{name}'. Call view_golden_example() with no args to list."
        fn_path = folder / "function.py"
        tests_path = folder / "test_agent.py"
        notes_path = folder / "notes.md"
        out = [f"# Golden example: {name}"]
        if notes_path.is_file():
            out.append(notes_path.read_text(encoding="utf-8"))
        if fn_path.is_file():
            out.append(f"\n## Function\n```python\n{fn_path.read_text(encoding='utf-8')}\n```")
        if tests_path.is_file():
            out.append(f"\n## Tests\n```python\n{tests_path.read_text(encoding='utf-8')}\n```")
        return "\n".join(out)

    def tool_write_test_file(self, code: str = "") -> str:
        if not code or not code.strip():
            return "ERROR: code is required."
        code = _strip_relative_imports(code)
        # Strip markdown fences if the LLM included them despite instructions
        m = re.match(r"^```(?:python)?\n(.*?)```\s*$", code.strip(), re.DOTALL)
        if m:
            code = m.group(1)
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(code)
        n_lines = len(code.splitlines())
        return f"wrote {n_lines} lines to {os.path.basename(self.test_file_path)}"

    def tool_finish(self, reason: str = "") -> str:
        self.done = True
        self.finish_reason = reason or "(none)"
        return f"session terminated. reason: {self.finish_reason}"

    # ── final accounting (called by pipeline after run_agent returns) ────

    def summary(self) -> dict:
        """Compute final metrics for DB persistence.

        In benchmark mode this does a fresh oracle pass on the final test file
        so metrics reflect what the agent actually shipped, not what it last
        inspected mid-loop. Always measures coverage on the final file.
        """
        out: dict = {
            "test_file_path": self.test_file_path if os.path.isfile(self.test_file_path) else "",
            "test_code": "",
            "turns_used": self.turn,
            "finish_reason": self.finish_reason,
            "history": self.history,
        }
        if os.path.isfile(self.test_file_path):
            out["test_code"] = Path(self.test_file_path).read_text(encoding="utf-8")

        # Final test run (always on current state — buggy in benchmark mode)
        final_run = None
        if os.path.isfile(self.test_file_path):
            final_run = _pytest_run(
                self.test_file_path, self.repo_dir,
                timeout=self.timeout, python_bin=self.python_bin,
            )
        out["final_run"] = final_run or {}
        out["tests_passed"] = len((final_run or {}).get("passed", []))
        out["tests_failed"] = len((final_run or {}).get("failed", []))
        out["tests_errored"] = len((final_run or {}).get("errors", []))
        out["tests_run"] = out["tests_passed"] + out["tests_failed"] + out["tests_errored"]

        # Coverage
        if os.path.isfile(self.test_file_path):
            cov = _pytest_cov(
                self.test_file_path, self.fn, self.repo_dir,
                timeout=self.timeout, python_bin=self.python_bin,
            )
            out["coverage"] = cov
            out["coverage_pct"] = cov.get("coverage_pct") if not cov.get("error") else None
        else:
            out["coverage"] = {}
            out["coverage_pct"] = None

        # SWT-bench oracle transitions (benchmark mode only)
        if self.benchmark_context and os.path.isfile(self.test_file_path):
            ctx = self.benchmark_context
            buggy_src = ctx["buggy_path"]
            fixed_src = ctx["fixed_path"]
            target = ctx["target_path"]

            shutil.copy(buggy_src, target)
            buggy_result = _pytest_run(
                self.test_file_path, self.repo_dir,
                timeout=self.timeout, python_bin=self.python_bin,
            )
            buggy_passed = {_name_only(n) for n in buggy_result.get("passed", [])}
            buggy_failed = {_name_only(n) for n in buggy_result.get("failed", [])}

            shutil.copy(fixed_src, target)
            fixed_result = _pytest_run(
                self.test_file_path, self.repo_dir,
                timeout=self.timeout, python_bin=self.python_bin,
            )
            fixed_passed = {_name_only(n) for n in fixed_result.get("passed", [])}
            fixed_failed = {_name_only(n) for n in fixed_result.get("failed", [])}

            shutil.copy(buggy_src, target)  # leave in buggy state

            f2p = len(buggy_failed & fixed_passed)
            f2f = len(buggy_failed & fixed_failed)
            p2p = len(buggy_passed & fixed_passed)
            p2f = len(buggy_passed & fixed_failed)

            out["metrics"] = {
                "f2p": f2p, "f2f": f2f, "p2f": p2f, "p2p": p2p,
                "detected": f2p > 0,
                "resolved": f2p > 0 and f2f == 0 and p2f == 0,
                "golden": f2p > 0 and f2f == 0,
                "patch_applied": True,
            }
            # Overwrite buggy-side test counts with the authoritative buggy-run
            out["tests_passed"] = len(buggy_passed)
            out["tests_failed"] = len(buggy_failed)
            out["final_run"] = buggy_result
        else:
            out["metrics"] = {
                "f2p": 0, "f2f": 0, "p2f": 0, "p2p": 0,
                "detected": False, "resolved": False, "golden": False,
                "patch_applied": False,
            }

        return out
