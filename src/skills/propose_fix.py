"""ProposeFixSkill — agentic source-code fix proposal.

Runs *after* the harness finishes producing a test. Edits source files in
`ctx.repo_dir` so the generated test passes. The test itself is treated as
read-only — this skill is the inverse of every other skill in the pipeline.

Only invoked by [src/action_entrypoint.py](src/action_entrypoint.py) via the
`run_agent(post_finalize=...)` hook. Not part of `run_harness`. The webapp
path never sees this skill.

Tool kit: Glob, Grep, Read, Edit. Write is intentionally excluded — Write
on a non-test path silently creates new files, and a fix shouldn't be
introducing new modules.

System prompt is **not** preceded by `_shared.md`. That preamble is
test-writing-specific ("you produce a pytest test function", "single-test
rule", oracle tiers) and would confuse a skill whose job is to edit source.
"""
from __future__ import annotations

from pathlib import Path

from src.harness import HarnessContext, read_test_file
from src.skills.agentic import run_agentic
from src.skills.base import Skill, format_intent_section
from src.skills.tools import build_tools


_PROMPTS_DIR = Path(__file__).parent / "prompts"


class ProposeFixSkill(Skill):
    name = "propose_fix"
    prompt_file = "propose_fix.md"

    def __init__(self) -> None:
        # Skip the shared preamble — it's specific to test writing and would
        # tell this skill to "produce a pytest test function" when its job
        # is the opposite. propose_fix.md is self-contained.
        if not self.name or not self.prompt_file:
            raise ValueError(f"{type(self).__name__} must set name and prompt_file")
        self._system_prompt = (_PROMPTS_DIR / self.prompt_file).read_text(encoding="utf-8")

    def run(self, ctx: HarnessContext) -> str:
        parts = ["# Propose a fix for the failing test"]
        intent = format_intent_section(ctx)
        if intent:
            parts.append(intent)
        parts.extend([
            "",
            "## The failing test (your spec)",
            "This test was just written from the issue above. It currently FAILS "
            "on the buggy code in this repo — that failure is the bug being "
            "detected. Your job is to edit the source so the test passes.",
            "",
            "```python",
            read_test_file(ctx),
            "```",
            "",
            "## What to do",
            "1. Read the test. Identify the imported symbols and the assertion.",
            "2. Use `Grep` / `Glob` to locate the source files those symbols live in.",
            "3. Use `Read` on the relevant source file(s).",
            "4. Use `Edit` to make the smallest change that satisfies the test's "
            "assertion (and the issue's intent).",
            "5. Do NOT edit the test file. Do NOT create new files. Do NOT touch "
            "tests/, conftest.py, or fixtures.",
            "6. When you believe the fix is complete, emit a short final message "
            "with no tool calls. The harness verifies by re-running the test.",
        ])

        # Filter Write out — we don't want this skill creating new source
        # files. Edit-only enforces "modify what's there, nothing else."
        tools = [t for t in build_tools(ctx) if t.name != "Write"]

        result = run_agentic(
            ctx,
            system_prompt=self._system_prompt,
            user_prompt="\n".join(parts),
            tools=tools,
            final_answer_instruction=(
                "Your edits on disk are your submission. Just confirm you're done."
            ),
        )

        ctx.attempts.append({
            "skill": self.name,
            "turns": result.turns,
            "tool_calls": result.tool_calls,
            "forced_final": result.forced_final,
        })
        return result.final_text
