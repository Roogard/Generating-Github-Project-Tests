"""GenerateSkill — issue + plan → agentic exploration → final test file.

Fully agentic. The LLM gets the issue + Analyze's test plan + tools (read_file,
search_in_repo, search_in_file, list_dir, run_generated_tests) and writes the
test file by exploring the repo. There's no single-shot fallback — without
the ability to read the repo, an issue-driven agent can't import anything
correctly.

The agent's final assistant message (with no tool calls) IS the submission;
the harness writes that text to disk.
"""
from __future__ import annotations

import json

from src.harness import HarnessContext
from src.skills.agentic import run_agentic
from src.skills.base import Skill, format_intent_section
from src.skills.tools import build_tools


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
            "\n## Workflow\n"
            "1. Use `search_in_repo` with the plan's `search_hints` to find relevant files.\n"
            "2. Use `read_file` to see imports / signatures of the public API and any nearby existing tests.\n"
            "3. Write your candidate test file. Run `run_generated_tests` to verify it imports cleanly.\n"
            "   (Tests SHOULD fail on the buggy code — don't 'fix' them by silencing the assertion.)\n"
            "4. Emit the COMPLETE test file as your final reply, with no tool calls. That is the submission.\n"
        )

        result = run_agentic(
            ctx,
            system_prompt=self._system_prompt,
            user_prompt="\n".join(parts),
            tools=build_tools(ctx),
            final_answer_instruction=(
                "Emit the complete pytest test file. Code only — no fences, no prose."
            ),
        )
        code = self._strip_code_fence(result.final_text)
        ctx.attempts.append({
            "skill": self.name, "mode": "agentic",
            "lines": len(code.splitlines()),
            "turns": result.turns,
            "tool_calls": result.tool_calls,
            "forced_final": result.forced_final,
        })
        return code
