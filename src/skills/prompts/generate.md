# Skill: Generate

You receive an issue and a structured test plan (from Analyze). The repo is
already cloned; you have tools to read its files. Your job is to write a
pytest test file that **reproduces the bug described in the issue**.

## Output

Your final assistant message — the one with no tool calls — must be the
complete pytest test file as plain text. Start with `import pytest` (and any
other imports). **No markdown fences, no prose, no explanation.** That
final message IS the submission; the harness writes it to disk.

## How to work

1. Use `search_in_repo` with the `search_hints` from the test plan to
   locate the relevant code path. The plan already names symbols/files —
   feed those to the tool, don't reinvent them.

2. Use `read_file` on the located file(s) to understand:
   - The public API surface (what to import, what to call).
   - Any existing tests in the repo that exercise this area (via
     `search_in_repo` for `test_<name>` or by listing the `tests/` dir).
     Existing tests show you the right setup, fixtures, and import idioms.
   - The function signature so you call it correctly. **You don't need to
     understand the implementation** — and you should resist the urge to
     read it deeply, because tracing the buggy body re-encodes the bug.

3. Use `run_generated_tests` to verify your test file imports and runs
   before you submit. This is how you catch import errors, missing
   fixtures, AttributeError on construction. It's NOT a way to check
   "does my test pass" — your tests SHOULD fail on the buggy code; that's
   the point. What you're checking is that pytest can collect and execute
   them without infrastructure errors.

4. When the test file is ready, emit it as your final message with no tool
   calls.

## Reading the test plan

- `reproducer_steps` — translate these into the body of your tests.
- `suggested_assertions` — use these directly when their tier and quote
  match the issue.
- `search_hints` — feed to `search_in_repo` first.
- `risk_notes` — explicit F→F traps to avoid.

## What to write

- 3–8 tests. **Diversity over quantity.** A single razor-sharp reproducer
  beats five hedged tests.
- Every test is preceded by exactly one strategy comment per the shared
  rules (`# Reproducer: ...`, `# BVA: ...`, etc.).
- Each test name describes the scenario: `test_<scenario>`. No `test_1`.
- Apply the Oracle Selection Rule from the shared rules.

## Assertion strategy — read this twice

For "should raise X" or "should not raise" issues, your default tool is
`pytest.raises(<ExceptionType>)`. This is Tier 3 and almost never produces
F→F. Reach for it first.

For "wrong output" issues, prefer Tier 2 (the relationship) over Tier 1
(the specific value). If the issue says "the mask isn't being copied",
`assert result.mask is not None` is a stronger signal than
`assert np.array_equal(result.mask, [[1,0,1],...])` — the second can fail
on the fixed code if your guessed array doesn't match.

If you DO want to write a Tier 1 exact-value assertion, you must first
have run `read_file` on the function the issue is about, AND the value
must come from the issue text or from an existing test in the repo —
never from your own mental model of what the code "should" return.

## Imports

The repo is `pip install -e`-ed. Import the public API directly:
```python
from package.subpackage import public_thing
```
NEVER use relative imports. NEVER use deep `_private` paths unless the
issue mentions them and the existing tests in the repo use them too.

## What will happen to your tests

A post-hoc grader runs your test file twice: once on the buggy code, once
with the gold fix patch applied. F→P (your test went from failing to
passing) is the success metric. F→F (failed on both — your test was
broken or asserted the wrong thing) is the failure mode to avoid above
all else.

So: tests should **fail** on the current code (in a way the issue
predicts) and **pass** once the bug is fixed.
