# Skill: Generate

You receive an issue and a structured test plan (from Analyze). The repo is
already cloned; you have tools to read its files. Your job is to write a
pytest test file containing **exactly one test** that reproduces the bug
described in the issue.

## Output

Your final assistant message — the one with no tool calls — must be the
complete pytest test file as plain text. Start with `import pytest` (and any
other imports). **No markdown fences, no prose, no explanation.** That
final message IS the submission; the harness writes it to disk.

## How to work

1. **First: read the existing tests for this area.** If the test plan
   includes a `test_path_glob`, feed it to `search_in_repo` (or pass it
   directly to `read_file` if it's a single file path) and read the
   matching file(s). Existing tests are your best source for: the right
   import idioms, the fixture/setup pattern this part of the repo uses,
   and the **grounded Tier-1 values** (real shape strings, real column
   names, real exception messages) that the codebase actually produces.
   Cribbing these costs nothing and prevents F→F kills from invented
   values.

2. Use `search_in_repo` with the `search_hints` from the test plan to
   locate the relevant *source* code path. The plan already names
   symbols/files — feed those to the tool, don't reinvent them.

3. Use `read_file` on the located source file(s) to understand:
   - The public API surface (what to import, what to call).
   - The function signature so you call it correctly. **You don't need to
     understand the implementation** — and you should resist the urge to
     read it deeply, because tracing the buggy body re-encodes the bug.

4. Use `run_generated_tests` to verify your test file imports and runs
   before you submit. This is how you catch import errors, missing
   fixtures, AttributeError on construction. It's NOT a way to check
   "does my test pass" — your test SHOULD fail on the buggy code; that's
   the point. What you're checking is that pytest can collect and execute
   it without infrastructure errors.

5. When the test file is ready, emit it as your final message with no tool
   calls.

## Reading the test plan

- `bug_trigger` — **read this first**. It's the one-line statement of
  what activates the bug. If your test setup doesn't satisfy this
  trigger, your assertion will silently pass on the buggy code (P→P,
  not F→P). Before you write any assertion, ask: does my test put the
  system in the state `bug_trigger` describes? If `bug_trigger` is
  empty, the bug fires on a plain function call — proceed normally.
- `reproducer_steps` — translate these into the body of your test.
- `suggested_assertions` — pick the one that best matches the issue's
  expected behavior. Use it directly when its tier and quote match.
- `search_hints` — feed to `search_in_repo` first.
- `risk_notes` — explicit F→F traps to avoid.

## What to write

- **Exactly one** `def test_*` function. Not two, not a parametrized
  matrix, not a test class with multiple methods. One function.
- Function name describes the scenario: `test_<scenario>` (e.g.
  `test_separability_matrix_nested_compound`). No `test_1`, no
  `# Reproducer:` comment prefix needed.
- The test body should be the smallest amount of code that:
  1. Sets up the state `bug_trigger` describes (if not empty)
  2. Performs the issue's reproduction steps verbatim
  3. Asserts the expected behavior the issue states
- Apply the Oracle Selection Rule from the shared rules to pick the
  right tier for your one assertion.

## Assertion strategy — read this twice

For "should raise X" or "should not raise" issues, your default tool is
`pytest.raises(<ExceptionType>)` with NO `match=`. This is Tier 3 and
almost never produces F→F.

**Pick the exception type from the issue or existing tests, NOT from your
own intuition about what "should" be raised.** If the issue's traceback
shows `ValueError`, use `ValueError` — even if `TypeError` would feel
more semantically correct. Second-guessing the type is the fast path to
F→F because the fix preserves the type but changes the message.

Add `match="..."` only when the substring is literally quoted in the
issue's traceback or expected-error text — never from your own paraphrase
of the error. The regex string is the F→F trap; the exception type is
grounded — they have different invention risk.

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

## What will happen to your test

A post-hoc grader runs your test file twice: once on the buggy code, once
with the gold fix patch applied. F→P (your test went from failing to
passing) is the success metric. F→F (failed on both — your test was
broken or asserted the wrong thing) is the failure mode to avoid above
all else.

So: your test should **fail** on the current code (in a way the issue
predicts) and **pass** once the bug is fixed.
