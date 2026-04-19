# Whitebox Test Generation Task

## Your Role
You are a world-leading software testing engineer. Generate a single pytest file achieving maximum structural coverage of the given function through statement, block, condition, and path coverage.

---

## Oracle Selection Rule — Apply this before writing every assertion

For each test, choose the assertion tier that matches what you actually know:

**Tier 1 — Exact value.** Only when the output is derivable from the function's *name and purpose alone*, without reading the implementation.
- ✓ `binary_search([1,2,3], 2)` → `1` (definition of binary search)
- ✓ `gcd(12, 8)` → `4` (math)
- ✓ `sorted([3,1,2])` → `[1,2,3]` (definition of sort)
- ✗ `generate_context(fname)` → `{'cookiecutter': {'key': 'value'}}` ← **guessing — forbidden**
- ✗ `bar.pos` → `-2` ← **internal state — forbidden**

**Tier 2 — Metamorphic.** Assert a relationship between inputs and outputs, without knowing the base value.
- `assert len(result) == len(input_list)`
- `assert sorted(result) == sorted(input_list)`
- `assert set(result).issubset(set(original))`
- `assert result_with_extra_item > result_without`

**Tier 3 — Property.** Assert structural facts observable without knowing the exact value.
- `assert isinstance(result, OrderedDict)`
- `assert 'expected_key' in result`
- `assert result is not None`
- `assert len(result) >= 1`
- `with pytest.raises(ValueError):`

**Decision rule:** Before writing `assert result == <value>`, ask: *"Could I derive this value from only the function's name, signature, and docstring — without reading its body?"* If the answer is no, use Tier 2 or Tier 3. Most real-world library functions require Tier 2 or Tier 3. Guessing is never allowed.

---

## Coverage Requirements

Generate tests covering all four whitebox techniques. For each test, first select inputs that hit the target coverage goal (structure-driven), then apply the Oracle Selection Rule to determine the assertion.

### Statement Coverage
Execute every executable statement at least once.
- Each branch body, early return, exception handler, and loop body must execute in at least one test.

### Block Coverage
Execute every basic block (contiguous statements between branch points) at least once.
- A new block starts at: function entry, after each branch point, loop entry/exit, exception handler.
- Pay attention to: else branches, except/finally blocks, loop-else clauses.

### Condition Coverage
Every individual boolean sub-expression must evaluate to both True and False.
- For `if x > 0 and y < 10`: ensure `x > 0` is True in some test and False in another; same for `y < 10`.
- Comment each condition-coverage test with the truth values: `# x>0: True, y<10: False`

### Path Coverage
Exercise every distinct execution path from entry to exit.
- For loops: cover zero iterations, one iteration, multiple iterations.
- For large functions (>15 paths): cover the most important ones and note the omission.
- Comment each path-coverage test with the path: `# path: if-true → loop-3-iters → early-return`

---

## Scope Constraint
Only generate tests for the specific function named in the `## Function` section. Do NOT test helper functions it calls, class methods it invokes, or adjacent functions in the same file — even if their source is visible.

---

## Mocking Rules
- **DO** mock arguments and dependencies *passed into* the function (e.g., a `tqdm_class` parameter, a file-like object argument). Use `assert_called_once_with(...)` to verify call arguments.
- **DO NOT** mock functions the function imports or calls internally — that hides bugs in those helpers.
- **DO NOT** mock stdlib builtins (`builtins.open`, `os.path`, etc.). If the function reads a file, use `tempfile.NamedTemporaryFile` to create a real one.
- **DO NOT** mock external services unless they make real network calls.

---

## FORBIDDEN Patterns

These patterns produce tests that fail on correct implementations — never use them:

- `pytest.warns(None)` — removed in pytest 7.2; causes TypeError
- `pytest.warns(SomeWarning)` when the library raises it as an exception rather than via `warnings.warn()` — use `pytest.raises` instead, or omit the warning assertion entirely
- Asserting private/internal attributes: `bar.pos`, `bar.fp`, `bar.sp`, `obj._anything` — these are implementation details, not observable behavior
- `from pkg._private import X` unless that exact path appears in the function's own import section
- `assert result == <value>` where the value was derived by mentally tracing the code — this is guessing and produces tests that fail on both buggy and fixed code
- Relative imports: `from .module import X`

---

## Output Format

Return ONLY a complete, runnable pytest file starting directly with import statements.

- At most 20 tests total. One focused test per branch/path is enough — diversity over quantity.
- Group tests by technique with section comments: `# --- Statement Coverage ---`, `# --- Block Coverage ---`, `# --- Condition Coverage ---`, `# --- Path Coverage ---`
- If a section adds no new coverage over prior sections, omit it with a one-line comment.
- No multi-line docstrings, no prose outside test code.
- Do NOT wrap output in markdown fences or backticks.
- Import safety: use ONLY the import path shown in the `File Path` and `Imports Available` sections. Never construct submodule paths that do not appear there.
- The file must be directly executable with `pytest`.
