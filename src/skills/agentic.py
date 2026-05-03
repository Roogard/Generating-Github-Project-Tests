"""Reusable agentic loop for skills that benefit from tool use.

Pattern (matches Claude Code's Agent-Computer Interface): the LLM iterates,
calling tools (Glob, Grep, Read, Edit, Write) until it emits a final
assistant message with no tool calls.

The harness owns running pytest. After any cycle whose tool calls modified
ctx.test_file_path (detected via mtime change), this module runs pytest on
the file and injects a synthetic HumanMessage carrying PASS/FAIL/ERROR + the
all-pass-on-buggy redirect into the next LLM call's context. The agent never
asks for results — it just sees them.

The submission is the file on disk (when the agent wrote the test file). The
LLM's final-message text is only used as a fallback by the calling skill if
no test file was ever written.

Budget accounting:
  - Every LLM response (tool-call or final) consumes one slot of
    ctx.llm_budget.
  - ctx.agentic_turn_cap bounds the per-skill loop length even if budget is
    high. When hit, the loop forces a final-answer turn — Otter's iteration-5
    satisfaction fallback.
"""
from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.tools import StructuredTool

from src.harness import BudgetExhausted, HarnessContext
from src.llm import cached_system_message, get_llm
from src.text_utils import truncate


@dataclass
class AgenticResult:
    final_text: str
    tool_calls: list[dict] = field(default_factory=list)  # {turn, name, args, result_chars}
    turns: int = 0
    forced_final: bool = False  # True if we exited the loop by forcing a final answer


def _coerce_text(content) -> str:
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return content or ""


_HOOK_HEADER = "[harness] pytest after your test file changed:"


def _run_and_format(ctx: HarnessContext) -> str:
    """Run pytest on ctx.test_file_path and format the result as the synthetic
    HumanMessage body the agent sees on its next turn.

    Returns either:
      - an ast.parse SyntaxError diagnostic (catches tool-call markup leaks
        before pytest sees them);
      - the all-pass-on-buggy redirect (the test isn't reproducing the bug);
      - PASS/FAIL/ERROR summary + first-`E `-line per failing test;
      - or a generic "no tests collected" hint.
    """
    from src.test_runner import run_tests as _pytest_run

    # ast.parse first so we don't waste a pytest invocation on a SyntaxError.
    try:
        with open(ctx.test_file_path, encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
    except SyntaxError as e:
        snippet = (source.strip().splitlines() or [""])[0][:200]
        return (
            f"{_HOOK_HEADER}\n"
            f"  Your test file is NOT valid Python — SyntaxError at line {e.lineno}: {e.msg}\n"
            f"    First line of the file: {snippet!r}\n"
            f"  When using Write on the test file, pass ONLY pytest source: `import` "
            f"statements, `def test_*` functions, assertions. NO prose, NO tool-call "
            f"markup, NO markdown fences."
        )
    except OSError:
        return f"{_HOOK_HEADER}\n  ERROR: could not read the test file."

    result = _pytest_run(
        ctx.test_file_path, ctx.repo_dir, ctx.runtime,
        timeout=ctx.timeout, per_test_timeout=ctx.per_test_timeout,
    )
    failed = result.get("failed") or []
    raw_errors = result.get("errors") or []
    real_errors = [e for e in raw_errors if not e.startswith("__")]
    synthetic = [e for e in raw_errors if e.startswith("__")]
    passed = result.get("passed") or []

    if not failed and not real_errors and not synthetic:
        if not passed:
            return (
                f"{_HOOK_HEADER}\n"
                f"  No tests collected from the file. Did you forget to define "
                f"`def test_*` functions? Use Write or Edit to add at least one."
            )
        # All tests PASSED on the buggy code. For an issue-driven run this is
        # backwards: the issue says this code is buggy, so a faithful test should
        # fail on it (that's the F→P signal). All-pass means the test is P→P
        # (wrong assertion / wrong trigger / wrong API surface) — never F→P.
        return (
            f"{_HOOK_HEADER}\n"
            f"  All {len(passed)} tests PASSED on the buggy code.\n"
            f"  But the issue says this code IS buggy. If your tests all pass, "
            f"one of these is true:\n"
            f"    - Your test exercises the wrong API (the buggy path isn't reached)\n"
            f"    - Your trigger inputs don't activate the bug\n"
            f"    - Your assertion describes what the buggy code does (P→P), "
            f"not what the issue says it should do (would be F→P)\n"
            f"  An F→P test MUST fail on the current code in the way the issue "
            f"predicts. Revise: pick the trigger inputs from the issue, and "
            f"assert the issue's intended behavior — not the current behavior. "
            f"Then Write or Edit the file again."
        )

    lines = [_HOOK_HEADER, f"  PASS {len(passed)}  FAIL {len(failed)}  ERROR {len(real_errors)}"]
    for fd in (result.get("failure_details") or [])[:5]:
        nodeid = fd.get("nodeid", "?").split("::")[-1]
        rep_lines = (fd.get("longrepr") or "").strip().splitlines()
        e_lines = [l for l in rep_lines if l.lstrip().startswith("E ")]
        msg = e_lines[0].strip() if e_lines else (rep_lines[0] if rep_lines else "")
        lines.append(f"    FAIL {nodeid}: {msg[:300]}")
    for ed in (result.get("error_details") or [])[:3]:
        nodeid = ed.get("nodeid", "?").split("::")[-1]
        rep_lines = (ed.get("longrepr") or "").strip().splitlines()
        e_lines = [l for l in rep_lines if l.lstrip().startswith("E ")]
        msg = e_lines[0].strip() if e_lines else (rep_lines[0] if rep_lines else "")
        lines.append(f"    ERROR {nodeid}: {msg[:300]}")
    if synthetic and not (failed or real_errors):
        for ed in (result.get("error_details") or [])[:1]:
            head = ((ed.get("longrepr") or "").strip().splitlines() or [""])[0]
            lines.append(f"    COLLECTION FAILURE: {head[:240]}")
    lines.append(
        "  Keep tests whose failures look like F→P detection (assertion matches the "
        "issue's intended behavior, current code disagrees) — that's what we want. "
        "Fix actionable infrastructure problems and Edit the file again."
    )
    return "\n".join(lines)


def _test_file_mtime(ctx: HarnessContext) -> float | None:
    """mtime of the test file, or None if it doesn't exist yet."""
    try:
        return os.path.getmtime(ctx.test_file_path)
    except OSError:
        return None


def run_agentic(
    ctx: HarnessContext,
    system_prompt: str,
    user_prompt: str,
    tools: list[StructuredTool],
    *,
    final_answer_instruction: str,
) -> AgenticResult:
    """Run a tool-using LLM loop. Returns AgenticResult with the agent's final
    assistant message text.

    `final_answer_instruction` is appended verbatim when the loop is forced to
    wrap up (cap hit). Should restate that the agent should emit a short final
    message and that the harness submits whatever's on disk.
    """
    if ctx.llm_calls_used >= ctx.llm_budget:
        raise BudgetExhausted("agentic-init")

    llm = get_llm(ctx.cfg).bind_tools(tools)
    tools_by_name = {t.name: t for t in tools}

    messages: list[BaseMessage] = [
        cached_system_message(ctx.cfg, system_prompt),
        HumanMessage(user_prompt),
    ]

    result = AgenticResult(final_text="")

    while True:
        if ctx.llm_calls_used >= ctx.llm_budget:
            raise BudgetExhausted("agentic")

        # If we've used the per-skill turn cap, force a final answer this turn.
        cap_reached = result.turns >= ctx.agentic_turn_cap
        if cap_reached and not result.forced_final:
            messages.append(HumanMessage(
                "Turn cap reached. " + final_answer_instruction +
                " Emit a short final message NOW with no tool calls."
            ))
            llm = get_llm(ctx.cfg)  # unbound — no tools available this call
            result.forced_final = True

        # Snapshot the test file's mtime BEFORE the turn so we can detect
        # whether any tool call (Write or Edit) modified it.
        mtime_before = _test_file_mtime(ctx)

        response: AIMessage = llm.invoke(messages)
        ctx.llm_calls_used += 1
        result.turns += 1
        messages.append(response)

        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls or cap_reached:
            result.final_text = _coerce_text(response.content).strip()
            return result

        # Dispatch each tool call sequentially. LangChain's StructuredTool
        # accepts dict args and returns the function's string result, which we
        # echo back as a ToolMessage keyed by tool_call_id.
        for tc in tool_calls:
            name = tc.get("name") or ""
            args = tc.get("args") or {}
            tool_call_id = tc.get("id") or ""
            tool = tools_by_name.get(name)
            if tool is None:
                tool_output = f"ERROR: unknown tool {name!r}. Available: {sorted(tools_by_name)}"
            else:
                try:
                    tool_output = tool.invoke(args)
                except Exception as e:
                    tool_output = f"ERROR running {name}({args!r}): {type(e).__name__}: {e}"
            tool_output_str = str(tool_output) if tool_output is not None else ""
            messages.append(ToolMessage(content=truncate(tool_output_str, 4000),
                                        tool_call_id=tool_call_id))
            result.tool_calls.append({
                "turn": result.turns,
                "name": name,
                "args": args,
                "result_chars": len(tool_output_str),
            })

        # End-of-cycle: if the test file's mtime changed (Write or Edit
        # modified it), run pytest and inject the result so the LLM sees it
        # on the next turn — no opt-in tool call required.
        mtime_after = _test_file_mtime(ctx)
        if mtime_after is not None and mtime_after != mtime_before:
            try:
                diagnostic = _run_and_format(ctx)
            except Exception as e:
                diagnostic = (f"{_HOOK_HEADER}\n"
                              f"  ERROR running pytest: {type(e).__name__}: {e}")
            messages.append(HumanMessage(truncate(diagnostic, 4000)))
