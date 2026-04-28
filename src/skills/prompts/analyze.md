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
  "bug_trigger": "one line — what about the inputs / state activates the buggy code path. Distinct from reproducer_steps (which is how to do it). E.g. 'figure must have been shown on a hi-DPI display before pickling — bug fires only when _original_dpi != _dpi'. Empty string if the trigger is just 'call this function with these args'.",
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
  "test_path_glob": "glob (or comma-separated globs) for the existing tests Generate should read first — e.g. 'sklearn/decomposition/tests/test_kernel_pca.py' or 'lib/matplotlib/tests/test_axes*.py'. Existing tests show the right import idioms, fixtures, and grounded Tier-1 values for this part of the codebase.",
  "risk_notes": [
    "F→F traps to avoid (e.g. fixture setup the issue doesn't describe)"
  ]
}
```

## Field rules

- **`bug_trigger`**: a one-line statement of what specifically activates
  the buggy branch. This is the **single most important field for
  detection** — many bugs require a particular input value, environment,
  or prior state to fire, and a test that hits the right API but the
  wrong trigger silently P→Ps. Examples:
  - "the input dtype must be `Int64` (nullable), not `int64`"
  - "must be called after `set_visible(False)` AND after `draw()`"
  - "only fires when `n_samples < n_clusters`"
  - "requires the figure to have been shown on a hi-DPI display first"
  If the trigger is just "call this function with these args" (no special
  state or input quality), use an empty string `""`.

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

- **`test_path_glob`**: a glob pointing Generate at the existing tests for
  the affected area. Best-guess from the issue's symbol/module names:
  - "the bug is in `KernelPCA`" → `"sklearn/decomposition/tests/test_kernel_pca.py"`
  - "issue with `pyplot.subplots`" → `"lib/matplotlib/tests/test_subplots*.py"`
  - "AffinityPropagation" → `"sklearn/cluster/tests/test_affinity_propagation.py"`
  Empty string if the affected module is unclear from the issue. Generate
  uses this to crib import idioms, fixtures, and grounded values rather
  than inventing them.

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
