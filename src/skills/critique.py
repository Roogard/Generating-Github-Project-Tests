"""CritiqueSkill — predict the test's transition outcome before submission.

Single LLM call (no tools). Inputs: issue + plan + final test file + pytest
result on the buggy code. Output: structured JSON with expected_transition
(F2P / F2F / P2P / P2F / UNKNOWN), confidence, rationale, concerns, and
needs_revision flag.

This skill does NOT modify the test file. It's a passive signal recorded on
ctx.last_critique and persisted via ctx.attempts. Whether to act on
needs_revision (e.g. fire another Improve pass) is the harness's call.

Mirrors AutoCodeRover's review stage and Otter's satisfaction check.
"""
from __future__ import annotations

import json

from src.harness import Feedback, HarnessContext, read_test_file
from src.skills.base import Skill, format_intent_section


def _format_pytest_summary(fb: Feedback | None) -> str:
    if fb is None or not fb.run_result:
        return "(no pytest result available)"
    r = fb.run_result
    passed = len(r.get("passed") or [])
    failed = len(r.get("failed") or [])
    real_errors = [e for e in (r.get("errors") or []) if not e.startswith("__")]
    lines = [f"PASS={passed} FAIL={failed} ERROR={len(real_errors)}"]
    for fd in (r.get("failure_details") or [])[:3]:
        nodeid = fd.get("nodeid", "?").split("::")[-1]
        rep = (fd.get("longrepr") or "").strip().splitlines()
        e_lines = [l for l in rep if l.lstrip().startswith("E ")]
        msg = e_lines[0].strip() if e_lines else (rep[0] if rep else "")
        lines.append(f"  FAIL {nodeid}: {msg[:240]}")
    for ed in (r.get("error_details") or [])[:2]:
        nodeid = ed.get("nodeid", "?").split("::")[-1]
        rep = (ed.get("longrepr") or "").strip().splitlines()
        e_lines = [l for l in rep if l.lstrip().startswith("E ")]
        msg = e_lines[0].strip() if e_lines else (rep[0] if rep else "")
        lines.append(f"  ERROR {nodeid}: {msg[:240]}")
    return "\n".join(lines)


class CritiqueSkill(Skill):
    name = "critique"
    prompt_file = "critique.md"

    def run(self, ctx: HarnessContext) -> dict:
        intent = format_intent_section(ctx)
        if not intent:
            ctx.last_critique = {"_skipped": "no issue text"}
            ctx.attempts.append({"skill": self.name, "ok": False, "reason": "no issue"})
            return ctx.last_critique

        test_code = read_test_file(ctx)
        if not test_code.strip():
            ctx.last_critique = {"_skipped": "no test file"}
            ctx.attempts.append({"skill": self.name, "ok": False, "reason": "no test"})
            return ctx.last_critique

        plan_block = (json.dumps(ctx.analysis or {}, indent=2, default=str)
                      if ctx.analysis else "(no plan)")

        user_msg = "\n".join([
            "# Critique this test",
            intent,
            "## Test plan from Analyze",
            plan_block,
            "",
            "## Final test file",
            f"```python\n{test_code}\n```",
            "",
            "## Pytest result on the buggy code",
            _format_pytest_summary(ctx.last_feedback),
            "",
            "Return the JSON object specified in the system prompt. No prose.",
        ])

        raw = self._call_llm(ctx, user_msg)
        critique = self._parse_json_block(raw)
        if not critique:
            critique = {
                "expected_transition": "UNKNOWN",
                "confidence": "low",
                "rationale": "",
                "concerns": [],
                "needs_revision": False,
                "_parse_failed": True,
            }
        ctx.last_critique = critique
        ctx.attempts.append({
            "skill": self.name,
            "ok": not critique.get("_parse_failed"),
            "expected_transition": critique.get("expected_transition"),
            "confidence": critique.get("confidence"),
            "needs_revision": bool(critique.get("needs_revision")),
            "concerns_count": len(critique.get("concerns") or []),
        })
        return critique
