"""Agentic tools used by Generate / Improve.

Five read-only-ish tools, modeled on SWE-Agent's Agent-Computer Interface:

  read_file(path, start, end)        100-line window with line numbers
  search_in_repo(pattern, glob)      file list (no contents — SWE-Agent finding)
  search_in_file(path, pattern)      line+context matches inside one file
  list_dir(path)                     dir listing
  run_generated_tests()              pytest on ctx.test_file_path

`write_file` is intentionally NOT exposed — the harness keeps ownership of
ctx.test_file_path. The agentic loop's final-answer turn carries the test
code as plain text and the harness writes it via ctx.write_test_file().

Path safety: every relative path resolves under ctx.repo_dir. Absolute paths
that escape ctx.repo_dir are rejected.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from langchain_core.tools import StructuredTool

from src.harness.context import HarnessContext


_DEFAULT_WINDOW = 100
_MAX_FILE_BYTES = 200_000  # cap any one read at ~200KB so tool output doesn't blow context
_SEARCH_RESULT_CAP = 50    # max files / matches returned per call
_SKIP_DIR_NAMES = {".git", "__pycache__", "node_modules", "venv", ".venv",
                   "dist", "build", ".tox", ".mypy_cache", ".pytest_cache"}


# ── Path resolution / safety ────────────────────────────────────────────────

def _resolve_under(repo_dir: str, path: str) -> Path | None:
    """Resolve `path` (relative or absolute) and return it only if it sits
    under repo_dir. Returns None if it escapes — caller should refuse.
    """
    repo = Path(repo_dir).resolve()
    p = Path(path)
    target = (p if p.is_absolute() else repo / p).resolve()
    try:
        target.relative_to(repo)
    except ValueError:
        return None
    return target


# ── Tool implementations (take HarnessContext, return string for tool message) ─

def _read_file(ctx: HarnessContext, path: str,
               start_line: int = 1, end_line: int | None = None) -> str:
    target = _resolve_under(ctx.repo_dir, path)
    if target is None:
        return f"ERROR: {path!r} resolves outside the repo. Use a path under the repo root."
    if not target.is_file():
        return f"ERROR: {path!r} is not a file (or doesn't exist)."

    try:
        size = target.stat().st_size
        if size > _MAX_FILE_BYTES:
            return (f"ERROR: {path!r} is {size} bytes (>{_MAX_FILE_BYTES}). "
                    f"Use start_line/end_line to read a specific window.")
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"ERROR reading {path!r}: {e}"

    lines = text.splitlines()
    total = len(lines)
    if start_line < 1:
        start_line = 1
    if end_line is None:
        end_line = min(start_line + _DEFAULT_WINDOW - 1, total)
    end_line = min(end_line, total)
    if start_line > total:
        return f"{path} has {total} lines; start_line={start_line} is past EOF."

    window = lines[start_line - 1:end_line]
    width = len(str(end_line))
    body = "\n".join(f"{n:{width}d}  {ln}" for n, ln in enumerate(window, start=start_line))
    suffix = f"\n... ({total - end_line} more lines below)" if end_line < total else ""
    return f"{path} (lines {start_line}-{end_line} of {total}):\n{body}{suffix}"


def _search_in_repo(ctx: HarnessContext, pattern: str, glob: str = "*.py") -> str:
    """Return a deduplicated list of file paths whose contents match `pattern`.

    Output deliberately omits match contents — SWE-Agent's design finding:
    "succinctly list the matches by simply listing each file." Reduces clutter
    so the agent can pick which file to read with read_file.
    """
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"ERROR: invalid regex {pattern!r}: {e}"

    repo = Path(ctx.repo_dir).resolve()
    matched: list[str] = []
    truncated = False

    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIR_NAMES and not d.startswith(".")]
        for name in files:
            if not Path(name).match(glob):
                continue
            full = Path(root) / name
            try:
                with full.open("r", encoding="utf-8", errors="replace") as f:
                    if any(rx.search(line) for line in f):
                        rel = full.relative_to(repo).as_posix()
                        matched.append(rel)
                        if len(matched) >= _SEARCH_RESULT_CAP:
                            truncated = True
                            break
            except OSError:
                continue
        if truncated:
            break

    if not matched:
        return f"No files matching glob={glob!r} contain pattern {pattern!r}."
    suffix = f"\n... (truncated at {_SEARCH_RESULT_CAP})" if truncated else ""
    return f"{len(matched)} file(s) match:\n" + "\n".join(matched) + suffix


def _search_in_file(ctx: HarnessContext, path: str, pattern: str) -> str:
    target = _resolve_under(ctx.repo_dir, path)
    if target is None:
        return f"ERROR: {path!r} resolves outside the repo."
    if not target.is_file():
        return f"ERROR: {path!r} is not a file (or doesn't exist)."

    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"ERROR: invalid regex {pattern!r}: {e}"

    matches: list[str] = []
    try:
        with target.open("r", encoding="utf-8", errors="replace") as f:
            for n, line in enumerate(f, start=1):
                if rx.search(line):
                    matches.append(f"{n:>5}  {line.rstrip()}")
                    if len(matches) >= _SEARCH_RESULT_CAP:
                        matches.append(f"... (truncated at {_SEARCH_RESULT_CAP})")
                        break
    except OSError as e:
        return f"ERROR reading {path!r}: {e}"

    if not matches:
        return f"No matches for {pattern!r} in {path}."
    return f"{path} matches for {pattern!r}:\n" + "\n".join(matches)


def _list_dir(ctx: HarnessContext, path: str = ".") -> str:
    target = _resolve_under(ctx.repo_dir, path)
    if target is None:
        return f"ERROR: {path!r} resolves outside the repo."
    if not target.is_dir():
        return f"ERROR: {path!r} is not a directory (or doesn't exist)."

    entries = []
    try:
        for child in sorted(target.iterdir()):
            name = child.name
            if name in _SKIP_DIR_NAMES or name.startswith("."):
                continue
            tag = "[dir]" if child.is_dir() else "[file]"
            entries.append(f"  {tag}  {name}")
    except OSError as e:
        return f"ERROR listing {path!r}: {e}"

    if not entries:
        return f"{path} is empty (or only contains hidden/skipped entries)."
    return f"{path}/:\n" + "\n".join(entries)


def _run_generated_tests(ctx: HarnessContext) -> str:
    """Run pytest on ctx.test_file_path. Returns a compact summary —
    pass/fail/error counts and short failure tracebacks. NEVER tells the agent
    "you can stop now" — final-answer decision stays with the agent."""
    from src.test_runner import run_tests as _pytest_run

    if not os.path.isfile(ctx.test_file_path):
        return ("ERROR: no test file written yet. Emit your candidate as the "
                "final assistant message and the harness will write+run it.")

    result = _pytest_run(
        ctx.test_file_path, ctx.repo_dir, ctx.runtime,
        timeout=ctx.timeout, per_test_timeout=ctx.per_test_timeout,
    )
    passed = result.get("passed", [])
    failed = result.get("failed", [])
    errored = [n for n in result.get("errors", []) if not n.startswith("__")]

    lines = [f"PASS {len(passed)}  FAIL {len(failed)}  ERROR {len(errored)}"]
    for fd in (result.get("failure_details") or [])[:5]:
        nodeid = fd.get("nodeid", "?").split("::")[-1]
        rep = (fd.get("longrepr") or "").strip().splitlines()
        head = rep[0] if rep else ""
        tail = rep[-1] if len(rep) > 1 else ""
        lines.append(f"  FAIL {nodeid}: {head[:200]}")
        if tail and tail != head:
            lines.append(f"        {tail[:200]}")
    for ed in (result.get("error_details") or [])[:3]:
        nodeid = ed.get("nodeid", "?").split("::")[-1]
        head = ((ed.get("longrepr") or "").strip().splitlines() or [""])[0]
        lines.append(f"  ERROR {nodeid}: {head[:200]}")
    return "\n".join(lines)


# ── Public: build the StructuredTool list bound to a context ────────────────

def build_tools(ctx: HarnessContext) -> list[StructuredTool]:
    """Bind the tools to a HarnessContext and return LangChain tool wrappers."""
    return [
        StructuredTool.from_function(
            name="read_file",
            description=("Read a window of a file in the repo. Default window is 100 lines. "
                         "Use this to inspect related code, helpers, or existing tests. "
                         "Path is relative to the repo root."),
            func=lambda path, start_line=1, end_line=None: _read_file(ctx, path, start_line, end_line),
        ),
        StructuredTool.from_function(
            name="search_in_repo",
            description=("Find which files in the repo contain a regex pattern. Returns a "
                         "list of file paths only (no contents). Use search_in_file or "
                         "read_file to see contents. Useful for locating helpers, related "
                         "tests, or class definitions."),
            func=lambda pattern, glob="*.py": _search_in_repo(ctx, pattern, glob),
        ),
        StructuredTool.from_function(
            name="search_in_file",
            description=("Find lines in a single file that match a regex. Returns up to 50 "
                         "matches with line numbers."),
            func=lambda path, pattern: _search_in_file(ctx, path, pattern),
        ),
        StructuredTool.from_function(
            name="list_dir",
            description="List entries in a directory under the repo root. Path defaults to '.'.",
            func=lambda path=".": _list_dir(ctx, path),
        ),
        StructuredTool.from_function(
            name="run_generated_tests",
            description=("Run pytest on the current test file (the file you've been writing). "
                         "Returns pass/fail/error counts and short tracebacks. "
                         "Use this to verify a candidate before declaring done."),
            func=lambda: _run_generated_tests(ctx),
        ),
    ]
