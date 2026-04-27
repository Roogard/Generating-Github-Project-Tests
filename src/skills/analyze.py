"""AnalyzeSkill — issue text → structured test plan (single LLM call).

Issue-driven: the skill reads only the issue (no function source). The plan
it produces tells Generate what to test for, what to search for in the repo,
and what F→F traps to avoid.
"""
from __future__ import annotations

from src.harness.context import HarnessContext
from src.skills.base import Skill, format_intent_section


class AnalyzeSkill(Skill):
    name = "analyze"
    prompt_file = "analyze.md"

    def run(self, ctx: HarnessContext) -> dict:
        intent = format_intent_section(ctx)
        if not intent:
            # Should be unreachable — the harness rejects empty issue_text
            # before invoking any skill — but be defensive.
            ctx.analysis = {"_skipped": "no issue text"}
            ctx.attempts.append({"skill": self.name, "ok": False, "reason": "no issue"})
            return ctx.analysis

        user_msg = (
            "# Build the test plan for this issue\n\n"
            f"{intent}\n\n"
            "Return the JSON object specified in the system prompt. No prose."
        )

        raw = self._call_llm(ctx, user_msg)
        analysis = self._parse_json_block(raw)
        if not analysis:
            analysis = {
                "issue_summary": (ctx.issue_title or "")[:200],
                "expected_behavior": "",
                "actual_behavior": "",
                "reproducer_steps": [],
                "suggested_assertions": [],
                "search_hints": [],
                "risk_notes": [],
                "_parse_failed": True,
            }
        ctx.analysis = analysis
        ctx.attempts.append({
            "skill": self.name,
            "ok": not analysis.get("_parse_failed"),
            "n_assertions": len(analysis.get("suggested_assertions") or []),
            "n_search_hints": len(analysis.get("search_hints") or []),
        })
        return analysis
