"""ImproveSkill — fallback when the test file has infrastructure problems.

Only invoked when pytest can't collect or set up the agent's tests
(import errors, AttributeError on construction, missing fixtures,
timeouts in test setup). Pytest assertion failures DO NOT trigger
Improve — they may be the F→P detections we want.

Agentic, with the same tool kit as Generate. Emits the revised file as
its final assistant message.
"""
from __future__ import annotations

from src.harness.context import HarnessContext
from src.harness.feedback import Feedback
from src.skills.agentic import run_agentic
from src.skills.base import Skill, format_intent_section
from src.skills.tools import build_tools


def _format_failures(fb: Feedback) -> str:
    """Render the infrastructure problems for the LLM.

    Includes collection errors, real per-test errors, and timeouts. Pytest
    assertion failures are deliberately NOT included — even if some are in
    fb.failures, the harness only invokes Improve when has_infrastructure_problems
    is True, and we don't want the LLM to silence assertion failures.
    """
    lines = []
    for cp in fb.collection_problems:
        lines.append(f"- COLLECTION ERROR ({cp['kind']}): {cp['longrepr']}")
    for e in fb.errors:
        lines.append(f"- {e['name']}: ERROR — {e['longrepr']}")
    for name in fb.timeouts:
        lines.append(f"- {name}: TIMEOUT in test setup (probably an infinite loop in your test, not in the code under test)")
    if not lines:
        return "(no infrastructure failures — improve was invoked unexpectedly)"
    return "\n".join(lines)


class ImproveSkill(Skill):
    name = "improve"
    prompt_file = "improve.md"

    def run(self, ctx: HarnessContext) -> str:
        fb = ctx.last_feedback
        if fb is None:
            raise RuntimeError("ImproveSkill requires ctx.last_feedback to be set")

        parts = ["# Fix the infrastructure problems in the test file"]
        intent = format_intent_section(ctx)
        if intent:
            parts.append(intent)
        parts.extend([
            "",
            "## Current test file",
            f"```python\n{ctx.read_test_file()}\n```",
            "",
            "## Infrastructure failures",
            _format_failures(fb),
            "",
            "## Critical reminder",
            "Tests with **AssertionError** are NOT in the failure list above. If you see "
            "assertion failures when running pytest yourself, leave them alone — they may be "
            "the F→P bug detections we want. Only fix collection / setup / timeout failures.",
            "",
            "## Workflow",
            "1. Inspect the failures above. For each one: search the repo for the right import / "
            "constructor / fixture pattern. Existing tests in the repo are the best reference.",
            "2. Patch the broken test(s). Keep every other test untouched.",
            "3. Call run_generated_tests to verify the file at least collects. (Assertion failures "
            "remaining is FINE — that's the bug detection.)",
            "4. Emit the COMPLETE revised pytest file as your final reply. Code only — no fences, no prose.",
        ])

        result = run_agentic(
            ctx,
            system_prompt=self._system_prompt,
            user_prompt="\n".join(parts),
            tools=build_tools(ctx),
            final_answer_instruction=(
                "Emit the complete revised pytest file. Code only — no fences, no prose."
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
