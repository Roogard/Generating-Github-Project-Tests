"""GenerateSkill — issue + plan → agentic exploration → final test file.

Fully agentic. The LLM gets the issue + Analyze's test plan + Claude Code-shaped
tools (Glob, Grep, Read, Edit, Write) and iterates: write a draft, the harness
auto-runs pytest and injects the result, agent revises, repeats. There's no
single-shot fallback — without the ability to read the repo, an issue-driven
agent can't import anything correctly.

The submission is whatever's on disk when the loop ends. The agent's
final-message text is a fallback used only if no test file was ever written.
"""
from __future__ import annotations

import json
import os

from src.harness import HarnessContext, read_test_file
from src.skills.agentic import run_agentic
from src.skills.base import Skill, format_intent_section
from src.skills.tools import build_tools
from src.text_utils import strip_code_fence


def _format_plan(analysis: dict) -> str:
    if not analysis or analysis.get("_skipped") or analysis.get("_parse_failed"):
        return "(Analyze step did not produce a structured plan — proceed from the issue text directly.)"
    return json.dumps(analysis, indent=2, default=str)


class GenerateSkill(Skill):
    name = "generate"
    prompt_file = "generate.md"

    def run(self, ctx: HarnessContext) -> str:
        parts = ["# Reproduce the bug described in this issue"]
        intent = format_intent_section(ctx)
        if intent:
            parts.append(intent)

        parts.append("\n## Test plan from Analyze")
        parts.append(_format_plan(ctx.analysis or {}))

        parts.append(
            f"\n## Workflow — iterate like a human writing pytest\n"
            f"1. Use `Grep` (default `output_mode='files_with_matches'`) with the plan's\n"
            f"   `search_hints` to find relevant files. Use `Glob` for pattern-based file\n"
            f"   lookup (e.g. `Glob('**/test_*.py')`).\n"
            f"2. Use `Read` to see imports / signatures of the public API and any nearby\n"
            f"   existing tests. Re-Grep with `output_mode='content'` for line-level matches.\n"
            f"3. Call `Write(file_path={ctx.test_file_path!r}, content=...)` to put a draft\n"
            f"   on disk. **The harness will automatically run pytest and append the results\n"
            f"   (PASS/FAIL/ERROR + tracebacks) into your next turn's context** — you don't\n"
            f"   need to ask. Look for `[harness] pytest after your test file changed:` in\n"
            f"   the next message.\n"
            f"4. **All-pass on the buggy code means your test isn't reproducing the bug.**\n"
            f"   F→P (test fails on buggy, passes on fixed = bug detected) is what we want.\n"
            f"5. Revise: prefer `Edit` for small fixes (one assertion, one import) — cheaper\n"
            f"   than rewriting. Use `Write` for full rewrites. Either way the harness\n"
            f"   re-runs pytest. Repeat until you have an F→P signal or you're out of budget.\n"
            f"6. **When done, emit a short final message ('done') with no tool calls.** The\n"
            f"   harness submits whatever's on disk — do NOT re-emit the full code in your\n"
            f"   final message.\n"
        )

        result = run_agentic(
            ctx,
            system_prompt=self._system_prompt,
            user_prompt="\n".join(parts),
            tools=build_tools(ctx),
            final_answer_instruction=(
                "The harness will submit whatever's on disk from your last Write or Edit. "
                "Just confirm you're done."
            ),
        )

        # Submission rule: file on disk wins (agent used Write/Edit); fall back
        # to final-message text only if the agent never wrote.
        if os.path.isfile(ctx.test_file_path) and read_test_file(ctx).strip():
            code = read_test_file(ctx)
            submission_source = "disk"
        else:
            code = strip_code_fence(result.final_text)
            submission_source = "final_message"

        ctx.attempts.append({
            "skill": self.name, "mode": "agentic",
            "lines": len(code.splitlines()),
            "turns": result.turns,
            "tool_calls": result.tool_calls,
            "forced_final": result.forced_final,
            "submission_source": submission_source,
        })
        return code
