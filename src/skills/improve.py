"""ImproveSkill — second-pass refinement of the test file.

Runs in one of two modes, picked from ctx state:

  - **infrastructure**: pytest can't collect or set up the agent's tests
    (import errors, AttributeError on construction, missing fixtures,
    timeouts). Triggered by `ctx.last_feedback.has_infrastructure_problems`.
    Pytest assertion failures DO NOT trigger this mode — they may be
    F→P detections we want.

  - **semantic** (critique-driven): pytest collected and ran the test, but
    Critique flagged it as F→F / P→F / P→P risk and set
    `needs_revision=True`. The fix isn't an import or fixture — it's an
    invented value, a wrong API surface, a missed bug trigger. Improve
    may need to **re-explore** the repo (Grep/Read) before editing,
    because the LLM might be looking in the wrong place.

Same agentic tool kit as Generate (Glob, Grep, Read, Edit, Write). The
harness auto-runs pytest after each modification to ctx.test_file_path
and injects the result into the next turn.
"""
from __future__ import annotations

import os

from src.harness import Feedback, HarnessContext, read_test_file
from src.skills.agentic import run_agentic
from src.skills.base import Skill, format_intent_section
from src.skills.tools import build_tools
from src.text_utils import strip_code_fence


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
        return "(no infrastructure failures)"
    return "\n".join(lines)


def _format_critique(critique: dict) -> str:
    """Render the critique's diagnosis for the LLM."""
    parts = [
        f"- Predicted transition: {critique.get('expected_transition')}",
        f"- Confidence: {critique.get('confidence')}",
        f"- Rationale: {critique.get('rationale') or '(none)'}",
    ]
    concerns = critique.get("concerns") or []
    if concerns:
        parts.append("- Concerns:")
        for c in concerns:
            parts.append(f"    * {c}")
    focus = critique.get("revision_focus")
    if focus:
        parts.append(f"- Revision focus: {focus}")
    return "\n".join(parts)


class ImproveSkill(Skill):
    name = "improve"
    prompt_file = "improve.md"

    def run(self, ctx: HarnessContext) -> str:
        # Pick mode from ctx state. Infrastructure takes priority — if pytest
        # can't even run the test, fix that before considering semantics.
        fb = ctx.last_feedback
        critique = ctx.last_critique or {}
        infra_mode = bool(fb and fb.has_infrastructure_problems)
        critique_mode = bool(critique.get("needs_revision")) and not infra_mode

        if not infra_mode and not critique_mode:
            raise RuntimeError(
                "ImproveSkill requires either infrastructure problems in "
                "ctx.last_feedback OR needs_revision in ctx.last_critique"
            )

        mode = "infrastructure" if infra_mode else "semantic"

        parts = [f"# Improve the test file ({mode} mode)"]
        intent = format_intent_section(ctx)
        if intent:
            parts.append(intent)
        parts.extend([
            "",
            "## Current test file",
            f"```python\n{read_test_file(ctx)}\n```",
            "",
        ])

        if infra_mode:
            parts.extend([
                "## Why you were called: pytest can't run the test",
                _format_failures(fb),
                "",
                "## What to fix",
                "ONLY infrastructure problems (collection errors, import errors, "
                "AttributeError on construction, missing fixtures, timeouts in setup). "
                "Pytest assertion failures are NOT in the list above — leave any you "
                "see alone, they may be the F→P bug detection we want.",
                "",
                "## Workflow",
                "1. Inspect the failures above. For each one: use `Grep` / `Read` to "
                "find the right import / constructor / fixture pattern. Existing tests "
                "in the repo are the best reference.",
                "2. Patch with `Edit` (preferred — pass a unique snippet from the file "
                f"as `old_string`). Use `Write(file_path={ctx.test_file_path!r}, "
                f"content=...)` only for full rewrites.",
                "3. The harness auto-runs pytest after each modification and appends "
                "`[harness] pytest after your test file changed:` to your next turn. "
                "Iterate until collection failures are gone.",
                "4. Assertion failures REMAINING is FINE — that's the bug detection.",
                "5. When done, emit a short final message ('done') with no tool calls.",
            ])
        else:  # critique_mode
            parts.extend([
                "## Why you were called: Critique flagged the test for revision",
                _format_critique(critique),
                "",
                "## What to fix",
                "The test is **infrastructurally fine** (pytest collected and ran it), "
                "but Critique predicts it won't be a clean F→P. The problem may be one of:",
                "  - **Invented values** — assertion uses an exact value the issue didn't state.",
                "  - **Wrong exception type** — `pytest.raises(X)` where the issue's traceback "
                "showed a different exception.",
                "  - **Wrong API surface** — the test exercises a function that doesn't actually "
                "trigger the bug.",
                "  - **Wrong trigger inputs** — bug needs specific state the test doesn't set up.",
                "",
                "## Workflow — re-explore first, then edit",
                "**Don't just patch the assertion.** The Critique concerns may indicate you (or "
                "the previous skill) was looking at the wrong code or had the wrong understanding. "
                "Before editing:",
                "",
                "1. **Re-read the issue carefully.** What exact behavior does it describe? Is "
                "there a value, an exception type, or an error message you can quote verbatim?",
                "2. **Re-localize.** Use `Grep` to confirm the symbol the test imports actually "
                "matches what the issue describes. If the issue mentions function `foo` and your "
                "test imports `bar`, that's a localization error — find `foo` first.",
                "3. **Read the function signature.** Use `Read` on the located function to confirm "
                "its argument shape. Many F→F failures come from passing wrong-shaped inputs.",
                "4. **Then patch with `Edit`** — replace just the broken assertion or import. "
                f"Use `Write(file_path={ctx.test_file_path!r}, content=...)` for full rewrites.",
                "5. Pytest auto-runs after each change. Aim for: test FAILS on the buggy code "
                "with an `AssertionError` (or the issue-predicted exception) whose message lines "
                "up with the issue's described bug. That's F→P.",
                "6. **Avoid the trap of weakening assertions to make pytest pass.** If pytest "
                "passes on the buggy code after your edit, you've moved toward P→P (worse). "
                "F→P means failing on buggy in the right way.",
                "7. When done, emit a short final message ('done') with no tool calls.",
            ])

        result = run_agentic(
            ctx,
            system_prompt=self._system_prompt,
            user_prompt="\n".join(parts),
            tools=build_tools(ctx),
            final_answer_instruction=(
                "The harness will submit whatever's on disk from your last Edit or Write. "
                "Just confirm you're done."
            ),
        )

        # Submission rule: file on disk wins.
        if os.path.isfile(ctx.test_file_path) and read_test_file(ctx).strip():
            code = read_test_file(ctx)
            submission_source = "disk"
        else:
            code = strip_code_fence(result.final_text)
            submission_source = "final_message"

        ctx.attempts.append({
            "skill": self.name, "mode": mode,
            "lines": len(code.splitlines()),
            "turns": result.turns,
            "tool_calls": result.tool_calls,
            "forced_final": result.forced_final,
            "submission_source": submission_source,
        })
        return code
