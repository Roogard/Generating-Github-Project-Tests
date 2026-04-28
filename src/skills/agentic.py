"""Reusable agentic loop for skills that benefit from tool use.

Pattern (matches SWE-Agent's Agent-Computer Interface): the LLM iterates,
calling tools (read_file, search_in_repo, run_generated_tests) until it
emits a final assistant message with no tool calls — that message IS the
answer. The harness then writes it to ctx.test_file_path.

Budget accounting:
  - Every LLM response (tool-call or final) consumes one slot of
    ctx.llm_budget. Matches the "count LLM responses as turns" rule from
    commit 2883aad.
  - ctx.agentic_turn_cap (default 6) bounds the per-skill loop length even
    if budget is high. When hit, the loop forces a final-answer turn —
    same as Otter's iteration-5 satisfaction fallback.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.tools import StructuredTool

from src.harness.context import BudgetExhausted, HarnessContext
from src.llm import cached_system_message, get_llm


@dataclass
class AgenticResult:
    final_text: str
    tool_calls: list[dict] = field(default_factory=list)  # {turn, name, args, result_chars}
    turns: int = 0
    forced_final: bool = False  # True if we exited the loop by forcing a final answer
    pre_commit_revisions: int = 0  # 1 if the agent emitted, hit problems, was given a revision turn


def _coerce_text(content) -> str:
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return content or ""


def _truncate(text: str, cap: int = 600) -> str:
    text = text or ""
    return text if len(text) <= cap else text[:cap] + "...[truncated]"


def _pre_commit_check(ctx: HarnessContext, candidate_code: str) -> str | None:
    """Write the candidate test file, run pytest, return a problem summary
    if anything's broken — else None.

    This is the SWE-Agent+ trick (NeurIPS 2024): forcing the agent to see
    its own test output before final submission catches construction
    errors, missing fixtures, AttributeError-on-init, and Tier-1 values
    that don't match the current code BEFORE they become F→F numbers in
    the oracle.
    """
    from src.test_runner import run_tests as _pytest_run

    if not candidate_code or not candidate_code.strip():
        return None  # caller handles empty-code case

    # Catch the model dumping prose / raw tool-call markup as the final answer
    # (e.g. DeepSeek's `<｜DSML｜tool_calls｜>` tokens leaking through when LangChain
    # didn't recognize them). ast.parse fails fast and gives a clearer revision
    # signal than waiting for pytest to error on a SyntaxError-laden file.
    try:
        ast.parse(candidate_code)
    except SyntaxError as e:
        snippet = candidate_code.strip().splitlines()[0][:200] if candidate_code.strip() else ""
        return (
            f"  Your output is NOT valid Python — SyntaxError at line {e.lineno}: {e.msg}\n"
            f"    First line of what you emitted: {snippet!r}\n"
            f"  Emit ONLY the contents of a pytest test file: `import` statements, "
            f"`def test_*` functions, assertions. NO prose, NO tool-call markup, "
            f"NO markdown fences."
        )

    try:
        ctx.write_test_file(candidate_code)
    except ValueError:
        return None

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
            return None  # No tests at all — let the harness handle the empty file
        # All tests PASSED on the buggy code. For an issue-driven run this is
        # backwards: the issue says this code is buggy, so a faithful test should
        # fail on it (that's the F→P signal). All-pass means the test is P→P
        # (wrong assertion / wrong trigger / wrong API surface) — never F→P.
        return (
            f"  All {len(passed)} tests PASSED on the buggy code.\n"
            f"  But the issue says this code IS buggy. If your tests all pass, "
            f"one of these is true:\n"
            f"    - Your test exercises the wrong API (the buggy path isn't reached)\n"
            f"    - Your trigger inputs don't activate the bug\n"
            f"    - Your assertion describes what the buggy code does (P→P), "
            f"not what the issue says it should do (would be F→P)\n"
            f"  An F→P test MUST fail on the current code in the way the issue "
            f"predicts. Revise: pick the trigger inputs from the issue, and "
            f"assert the issue's intended behavior — not the current behavior."
        )

    lines = [f"  PASS {len(passed)}  FAIL {len(failed)}  ERROR {len(real_errors)}"]
    for fd in (result.get("failure_details") or [])[:5]:
        nodeid = fd.get("nodeid", "?").split("::")[-1]
        rep_lines = (fd.get("longrepr") or "").strip().splitlines()
        # Pytest's longrepr starts with the failing line, then `E` lines with
        # the assertion / exception / diff. The most useful info is the
        # FIRST `E ` line (the actual error message, e.g.
        # "E   AssertionError: assert '-1th' == '-1st'" or
        # "E   AttributeError: 'X' object has no attribute 'col_starts'").
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
        # Pure collection failure (no per-test outcomes) — surface it directly
        for ed in (result.get("error_details") or [])[:1]:
            head = ((ed.get("longrepr") or "").strip().splitlines() or [""])[0]
            lines.append(f"    COLLECTION FAILURE: {head[:240]}")
    return "\n".join(lines)


def run_agentic(
    ctx: HarnessContext,
    system_prompt: str,
    user_prompt: str,
    tools: list[StructuredTool],
    *,
    final_answer_instruction: str,
) -> AgenticResult:
    """Run a tool-using LLM loop. Returns the final assistant message text.

    `final_answer_instruction` is appended verbatim when the loop is forced to
    wrap up (cap hit). Should restate the output format ("emit pytest code,
    no fences, no prose").
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
    pre_commit_done = False

    while True:
        if ctx.llm_calls_used >= ctx.llm_budget:
            raise BudgetExhausted("agentic")

        # If we've used the per-skill turn cap, force a final answer this turn.
        cap_reached = result.turns >= ctx.agentic_turn_cap
        if cap_reached:
            messages.append(HumanMessage(
                "Turn cap reached. " + final_answer_instruction +
                " Emit the final answer NOW with no further tool calls."
            ))
            llm = get_llm(ctx.cfg)  # unbound — no tools available this call
            result.forced_final = True

        response: AIMessage = llm.invoke(messages)
        ctx.llm_calls_used += 1
        result.turns += 1
        messages.append(response)

        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls or cap_reached:
            candidate = _coerce_text(response.content).strip()

            # Pre-commit check (Phase A). Run the candidate through pytest and,
            # if anything's broken AND we haven't already done a revision AND
            # we still have budget, give the agent ONE chance to fix it. Skips
            # if we're in cap-reached forced-final mode (no point — the agent
            # has no more tools and just emitted under duress).
            should_check = (
                not pre_commit_done
                and not cap_reached
                and ctx.llm_calls_used < ctx.llm_budget
            )
            if should_check:
                pre_commit_done = True
                problems = _pre_commit_check(ctx, candidate)
                if problems is not None:
                    result.pre_commit_revisions = 1
                    messages.append(HumanMessage(
                        "Pre-commit pytest check on your candidate found problems:\n"
                        f"{problems}\n\n"
                        "If the diagnosis lists FAIL/ERROR items: fix what's "
                        "actionable in ONE revision — bad imports, wrong "
                        "constructor arguments, missing fixtures, "
                        "AttributeError on object construction, Tier-1 values "
                        "that don't match the current code. **KEEP** any test "
                        "whose failure looks like an F→P detection (the "
                        "assertion matches the issue's intended behavior, the "
                        "current code disagrees) — that's exactly what we "
                        "want. Don't silence detection.\n\n"
                        "If the diagnosis says all tests PASSED on the buggy "
                        "code: your tests aren't exercising the bug. Rewrite "
                        "to make at least one test FAIL on the current code in "
                        "the way the issue predicts. Use the issue's reproducer "
                        "code verbatim for trigger inputs. Assert the issue's "
                        "stated intended behavior, not what the current code "
                        "happens to do.\n\n"
                        "Emit the complete revised pytest file as your final "
                        "reply. No tool calls, code only."
                    ))
                    # Bind the LLM to no tools for the revision turn — we want
                    # a clean re-emit, not more exploration.
                    llm = get_llm(ctx.cfg)
                    continue

            result.final_text = candidate
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
            messages.append(ToolMessage(content=_truncate(tool_output_str, cap=4000),
                                        tool_call_id=tool_call_id))
            result.tool_calls.append({
                "turn": result.turns,
                "name": name,
                "args": args,
                "result_chars": len(tool_output_str),
            })
