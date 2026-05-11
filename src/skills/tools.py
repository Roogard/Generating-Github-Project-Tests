"""Agentic tool kit — mirrors Claude Code's tool shape.

Five tools (PascalCase to match Claude Code):
  Glob(pattern, path=None)
    File pattern matching. Returns paths sorted by mtime.
  Grep(pattern, path=None, output_mode='files_with_matches', ...)
    Regex content search. Three output modes: files_with_matches | content | count.
  Read(file_path, offset=1, limit=2000)
    Windowed file read with cat -n line numbers.
  Edit(file_path, old_string, new_string, replace_all=False)
    Exact string replace. Requires the file to have been Read this session.
  Write(file_path, content)
    Full file write. When the target is ctx.test_file_path, markdown fences
    and relative imports are stripped via src.harness.write_test_file.

There is no run-tests tool: when Write or Edit modifies ctx.test_file_path,
the harness auto-runs pytest and injects the result into the next LLM turn
(see src/skills/agentic.py).

Path safety: every relative path resolves under ctx.repo_dir or ctx.test_dir.
Absolute paths that escape both are rejected.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from langchain_core.tools import StructuredTool

from src.harness import HarnessContext, write_test_file


_DEFAULT_READ_LIMIT = 2000
_MAX_FILE_BYTES = 200_000
_DEFAULT_HEAD_LIMIT = 250
_SKIP_DIR_NAMES = {".git", "__pycache__", "node_modules", "venv", ".venv",
                   "dist", "build", ".tox", ".mypy_cache", ".pytest_cache"}


def _resolve(ctx: HarnessContext, path: str) -> Path | None:
    """Resolve a relative-or-absolute path under ctx.repo_dir OR ctx.test_dir.
    Returns None if it escapes both — caller should refuse.
    """
    p = Path(path)
    for root in (Path(ctx.repo_dir).resolve(), Path(ctx.test_dir).resolve()):
        target = (p if p.is_absolute() else root / p).resolve()
        try:
            target.relative_to(root)
            return target
        except ValueError:
            continue
    return None


def _display_path(ctx: HarnessContext, p: Path) -> str:
    """Format a path for display: relative to repo_dir if possible, else as-is."""
    repo = Path(ctx.repo_dir).resolve()
    try:
        return p.relative_to(repo).as_posix()
    except ValueError:
        return p.as_posix()


def _iter_files(root: Path):
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIR_NAMES and not d.startswith(".")]
        for name in files:
            yield Path(r) / name


def _glob(ctx: HarnessContext, pattern: str, path: str | None = None) -> str:
    base = _resolve(ctx, path) if path else Path(ctx.repo_dir).resolve()
    if base is None or not base.is_dir():
        return f"ERROR: {path!r} is not a directory under the repo."

    try:
        candidates = list(base.rglob(pattern))
    except (OSError, ValueError) as e:
        return f"ERROR: invalid glob pattern {pattern!r}: {e}"

    matches = []
    for p in candidates:
        if not p.is_file():
            continue
        rel_parts = p.relative_to(base).parts
        if any(part in _SKIP_DIR_NAMES or part.startswith(".") for part in rel_parts[:-1]):
            continue
        matches.append(p)

    matches.sort(key=lambda p: -p.stat().st_mtime)
    matches = matches[:_DEFAULT_HEAD_LIMIT]
    if not matches:
        return f"No files match {pattern!r}."
    return "\n".join(p.relative_to(base).as_posix() for p in matches)


def _grep(ctx: HarnessContext, pattern: str, path: str | None = None,
          output_mode: str = "files_with_matches", glob: str = "*",
          case_insensitive: bool = False, line_numbers: bool = True,
          before: int | None = None, after: int | None = None,
          context: int | None = None,
          head_limit: int = _DEFAULT_HEAD_LIMIT,
          multiline: bool = False) -> str:
    """Regex search across files. Mirrors Claude Code's Grep tool.

    output_mode controls the return:
      files_with_matches (default) — paths only
      content — matching lines (optionally with surrounding context)
      count — '<path>:<n>' per matching file
    """
    if output_mode not in {"files_with_matches", "content", "count"}:
        return (f"ERROR: unknown output_mode {output_mode!r}. "
                f"Use 'files_with_matches' | 'content' | 'count'.")

    flags = 0
    if case_insensitive:
        flags |= re.IGNORECASE
    if multiline:
        flags |= re.DOTALL | re.MULTILINE
    try:
        rx = re.compile(pattern, flags)
    except re.error as e:
        return f"ERROR: invalid regex {pattern!r}: {e}"

    if context is not None:
        before = after = context
    before = max(0, before or 0)
    after = max(0, after or 0)

    if path:
        target = _resolve(ctx, path)
        if target is None:
            return f"ERROR: {path!r} resolves outside the repo."
        files = [target] if target.is_file() else list(_iter_files(target))
    else:
        files = list(_iter_files(Path(ctx.repo_dir).resolve()))

    files = [f for f in files if f.match(glob)]

    matched_files: list[str] = []
    counts: list[tuple[str, int]] = []
    content_blocks: list[str] = []

    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = text.splitlines()
        hit_idx = [i for i, ln in enumerate(lines) if rx.search(ln)]
        if not hit_idx:
            continue
        rel = _display_path(ctx, f)
        matched_files.append(rel)
        counts.append((rel, len(hit_idx)))

        if output_mode == "content":
            shown: set[int] = set()
            for i in hit_idx:
                lo, hi = max(0, i - before), min(len(lines), i + after + 1)
                for j in range(lo, hi):
                    if j in shown:
                        continue
                    shown.add(j)
                    sep = ":" if j == i else "-"
                    if line_numbers:
                        content_blocks.append(f"{rel}{sep}{j+1}{sep}{lines[j]}")
                    else:
                        content_blocks.append(f"{rel}{sep}{lines[j]}")

        if output_mode == "files_with_matches" and len(matched_files) >= head_limit:
            break

    if output_mode == "files_with_matches":
        return "\n".join(matched_files[:head_limit]) if matched_files else f"No files match {pattern!r}."
    if output_mode == "count":
        return "\n".join(f"{p}:{n}" for p, n in counts[:head_limit]) if counts else f"No matches for {pattern!r}."
    return "\n".join(content_blocks[:head_limit]) if content_blocks else f"No matches for {pattern!r}."


def _read(ctx: HarnessContext, file_path: str, offset: int = 1,
          limit: int = _DEFAULT_READ_LIMIT) -> str:
    target = _resolve(ctx, file_path)
    if target is None:
        return f"ERROR: {file_path!r} resolves outside the repo."
    if not target.is_file():
        return f"ERROR: {file_path!r} is not a file (or doesn't exist)."

    try:
        size = target.stat().st_size
        if size > _MAX_FILE_BYTES:
            return (f"ERROR: {file_path!r} is {size} bytes (>{_MAX_FILE_BYTES}). "
                    f"Use offset/limit to read a window.")
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"ERROR reading {file_path!r}: {e}"

    lines = text.splitlines()
    total = len(lines)
    start = max(1, offset)
    if start > total:
        return f"{file_path} has {total} lines; offset={offset} is past EOF."
    end = min(total, start + max(1, limit) - 1)

    ctx.read_paths.add(str(target))
    window = lines[start - 1:end]
    width = max(4, len(str(end)))
    body = "\n".join(f"{n:{width}d}\t{ln}" for n, ln in enumerate(window, start=start))
    suffix = f"\n... ({total - end} more lines below)" if end < total else ""
    return f"{file_path} (lines {start}-{end} of {total}):\n{body}{suffix}"


def _edit(ctx: HarnessContext, file_path: str, old_string: str,
          new_string: str, replace_all: bool = False) -> str:
    target = _resolve(ctx, file_path)
    if target is None:
        return f"ERROR: {file_path!r} resolves outside the repo."
    if not target.is_file():
        return f"ERROR: {file_path!r} is not a file (or doesn't exist)."
    if str(target) not in ctx.read_paths:
        return (f"ERROR: must Read {file_path!r} before editing it. "
                f"Call Read(file_path={file_path!r}) first.")
    if old_string == new_string:
        return "ERROR: old_string and new_string are identical."
    if not old_string:
        return "ERROR: old_string is empty. To create a new file, use Write."

    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"ERROR reading {file_path!r}: {e}"

    n = text.count(old_string)
    if n == 0:
        return f"ERROR: old_string not found in {file_path}."
    if n > 1 and not replace_all:
        return (f"ERROR: old_string occurs {n} times in {file_path}. "
                f"Provide more context to make it unique, or pass replace_all=True.")

    new_text = text.replace(old_string, new_string) if replace_all else text.replace(old_string, new_string, 1)
    try:
        target.write_text(new_text, encoding="utf-8")
    except OSError as e:
        return f"ERROR writing {file_path!r}: {e}"
    return f"edited {file_path} ({n} replacement{'s' if n > 1 else ''})."


def _write(ctx: HarnessContext, file_path: str, content: str) -> str:
    target = _resolve(ctx, file_path)
    if target is None:
        return f"ERROR: {file_path!r} resolves outside the repo."
    if content is None or not content.strip():
        return "ERROR: content is empty."

    # Writing the test file routes through src.harness.write_test_file so
    # markdown fences and relative imports get stripped (preserves an existing
    # protection that matters for the LLM's submission).
    test_file_resolved = Path(ctx.test_file_path).resolve()
    if target == test_file_resolved:
        try:
            n = write_test_file(ctx, content)
        except ValueError as e:
            return f"ERROR: {e}."
        return f"wrote {n} lines to {file_path}."

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(content, encoding="utf-8")
    except OSError as e:
        return f"ERROR writing {file_path!r}: {e}"
    ctx.read_paths.add(str(target))
    return f"wrote {len(content.splitlines())} lines to {file_path}."


def build_tools(ctx: HarnessContext) -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            name="Glob",
            description=(
                "Find files by glob pattern (e.g. '**/*.py', 'src/**/test_*.py'). "
                "Returns matching file paths sorted by modification time, newest first. "
                "Path defaults to the repo root."
            ),
            func=lambda pattern, path=None: _glob(ctx, pattern, path),
        ),
        StructuredTool.from_function(
            name="Grep",
            description=(
                "Regex content search across files. output_mode controls output:\n"
                "  'files_with_matches' (default) — paths only (use first to narrow)\n"
                "  'content' — matching lines, optional surrounding context via before/after/context\n"
                "  'count' — '<path>:<n>' per file\n"
                "Other args: glob (e.g. '*.py'), case_insensitive, line_numbers, "
                "head_limit, multiline (regex spans line breaks). "
                "path may be a directory or a single file."
            ),
            func=lambda pattern, path=None, output_mode="files_with_matches",
                       glob="*", case_insensitive=False, line_numbers=True,
                       before=None, after=None, context=None,
                       head_limit=_DEFAULT_HEAD_LIMIT, multiline=False:
                _grep(ctx, pattern, path, output_mode, glob, case_insensitive,
                      line_numbers, before, after, context, head_limit, multiline),
        ),
        StructuredTool.from_function(
            name="Read",
            description=(
                f"Read a file with line numbers. Default reads up to {_DEFAULT_READ_LIMIT} "
                "lines starting at line 1. For larger files, set offset (1-indexed start "
                "line) and limit. file_path is relative to the repo root."
            ),
            func=lambda file_path, offset=1, limit=_DEFAULT_READ_LIMIT:
                _read(ctx, file_path, offset, limit),
        ),
        StructuredTool.from_function(
            name="Edit",
            description=(
                "Replace exact string old_string with new_string in a file. "
                "old_string must be unique in the file unless replace_all=True. "
                "You must Read the file first in this session. "
                "When the file is the test file, pytest auto-runs in your next turn."
            ),
            func=lambda file_path, old_string, new_string, replace_all=False:
                _edit(ctx, file_path, old_string, new_string, replace_all),
        ),
        StructuredTool.from_function(
            name="Write",
            description=(
                "Write content to a file (creates or overwrites). "
                "When writing the test file, markdown fences and relative imports "
                "are stripped automatically and pytest auto-runs in your next turn. "
                "Pass the COMPLETE file source — imports + def test_* functions."
            ),
            func=lambda file_path, content: _write(ctx, file_path, content),
        ),
    ]
