# Skill: Analyze

You receive a GitHub issue describing a bug in a Python repo. Produce a
structured **test plan** the Generate skill will use to write tests that
reproduce the bug.

You don't have access to the repo at this step — Generate has tools to
explore. Your job is to extract everything testable from the issue text
itself, and tell Generate where to look.

## Output schema

Return a single JSON object with exactly these keys. No prose around it.

```json
{
  "issue_summary": "one sentence — what's broken in the user's words",
  "expected_behavior": "what the issue says should happen, quoting where possible",
  "actual_behavior": "what the issue says the code does today",
  "reproducer_steps": [
    "ordered, concrete steps to reproduce — code snippets if the issue has them"
  ],
  "suggested_assertions": [
    {
      "tier": 1,
      "code": "<short assertion fragment>",
      "rationale": "why this tier",
      "issue_quote": "<verbatim short phrase from the issue justifying this assertion>"
    }
  ],
  "search_hints": [
    "regex or symbol name to grep the repo for — file/class/function the issue mentions"
  ],
  "risk_notes": [
    "F→F traps to avoid (e.g. fixture setup the issue doesn't describe)"
  ]
}
```

## Field rules

- **`reproducer_steps`**: a numbered, code-level sequence. Prefer copying
  snippets verbatim from the issue's "Steps to reproduce" / "Code Sample"
  section. If the issue only describes the bug in prose, write the steps
  as the smallest amount of code that exercises the described scenario.

- **`suggested_assertions`**: each entry has `tier` ∈ {1,2,3}, `code` (a
  short assertion fragment), `rationale`, and `issue_quote`.
  - **Tier 1** — exact equality. Only when the issue states the expected
    value (e.g. "expected `[1,2,3]` but got `[1,3]`"). The `issue_quote`
    must contain that value.
  - **Tier 2** — metamorphic. Assert a relationship the issue implies
    (`len(result) == len(input)`, `sorted(result) == input`,
    `f(g(x)) == x`).
  - **Tier 3** — property. Assert a structural fact (`isinstance`,
    `pytest.raises`, ordering, membership).
  - **Coverage**: at least one assertion per distinct symptom mentioned
    in the issue.

- **`search_hints`**: regexes / symbol names Generate should `search_in_repo`
  for. Example: if the issue mentions "the QDP reader," include `"_line_type"`
  or `"qdp"` so Generate can find the relevant file fast. Be specific; vague
  hints waste Generate's tool budget.

- **`risk_notes`**: things that would produce F→F (false positives) if
  Generate isn't careful — e.g. "the test must skip the network setup,"
  "use a tempfile not a hardcoded path."

## Critical rules

- **Never invent values the issue doesn't tell you.** If the issue says
  "the result is wrong" without saying what it should be, drop to Tier 2
  or Tier 3. A guessed Tier 1 value that matches the buggy code becomes
  a P→F regression after the fix.

- **Read closely.** Issues bury the expected value in code blocks, error
  messages, or "expected vs got" tables. Quote when you find them.

## Forbidden

- Do not output Python outside the assertion fragments.
- Do not output anything outside the JSON object.
- Do not include a `tests` key or write any test code — that's Generate's job.
- Do not echo the raw issue text — extract the testable facts.
