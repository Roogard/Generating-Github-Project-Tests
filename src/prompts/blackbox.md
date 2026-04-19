# Blackbox Test Generation Task

## Your Role
You are a world-leading software testing engineer. Generate a single pytest file achieving broad behavioral coverage through boundary value analysis, equivalence class partitioning, and mutation detection.

---

## Oracle Selection Rule — Apply this before writing every assertion

For each test, choose the assertion tier that matches what you actually know:

**Tier 1 — Exact value.** Only when the output is derivable from the function's *name and purpose alone*, without reading the implementation.
- ✓ `binary_search([1,2,3], 2)` → `1` (definition of binary search)
- ✓ `gcd(12, 8)` → `4` (math)
- ✓ `is_palindrome("racecar")` → `True` (definition)
- ✗ `generate_context(fname, default_context={'k': 'v'})` → `{'cookiecutter': {'k': 'v'}}` ← **guessing — forbidden**
- ✗ `tqdm(range(5), position=2).pos` → `-2` ← **internal state — forbidden**

**Tier 2 — Metamorphic.** Assert a relationship between inputs and outputs, without knowing the base value.
- `assert len(result) == len(input_list)`
- `assert sorted(result) == sorted(input_list)`
- `assert set(result).issubset(set(original))`
- Result with extra context must contain more keys than result without

**Tier 3 — Property.** Assert structural facts observable without knowing the exact value.
- `assert isinstance(result, OrderedDict)`
- `assert 'expected_key' in result`
- `assert result is not None`
- `assert len(result) >= 1`
- `with pytest.raises(ValueError):`

**Decision rule:** Before writing `assert result == <value>`, ask: *"Could I derive this value from only the function's name, signature, and docstring — without reading its body?"* If the answer is no, use Tier 2 or Tier 3. Most real-world library functions require Tier 2 or Tier 3. Guessing is never allowed.

---

## Coverage Requirements

Generate tests covering all three blackbox techniques. For each test, first select inputs (boundary value, equivalence class representative, or mutation-distinguishing input), then apply the Oracle Selection Rule to determine the assertion.

---

### BVA — Boundary Value Analysis

Select inputs at boundaries and assert what MUST be true at each boundary — not what you traced the code to return.

- Numeric: min, min+1, max−1, max, just outside both bounds
- Collections: empty (`[]`), single element, typical size
- Strings: empty string, single character, typical length
- Optional/nullable: `None` and a valid value

For each boundary test, assert the behavioral contract at that boundary (e.g., "empty input must return an empty result", "None input must raise TypeError") rather than an exact value derived by tracing.

---

### ECP — Equivalence Class Partitioning

Identify valid classes (inputs processed normally) and invalid classes (inputs rejected or raise exceptions). Write one representative test per class.

- For valid classes: assert structural properties of the output (type, non-null, key presence)
- For invalid classes: assert `pytest.raises(ExpectedException)`
- Name tests to identify the class: `test_valid_positive`, `test_invalid_empty`

---

### Mutation Detection

**This is the highest-value section.** Write tests designed to fail when a specific mutation is introduced in the function. These tests detect the actual bug.

Focus on mutations that change behavioral boundaries, not exact values:
- **Off-by-one:** `<` vs `<=`, `range(n)` vs `range(n+1)` → test an input at the exact boundary where the mutation flips behavior (e.g., an element that is found vs. not found with an off-by-one)
- **Wrong operator:** `+` vs `-`, `and` vs `or` → test an input that distinguishes the operators
- **Boundary error:** inclusive vs exclusive → test the exact boundary value
- **Negation error:** flipped boolean, missing `not` → test both True and False cases
- **Wrong constant:** incorrect initial/sentinel value → test with an input that exercises that constant

For mutation detection, assert behavioral contracts (found/not-found, True/False, raises/doesn't-raise, empty/non-empty) rather than exact values. Comment each test: `# detects off-by-one in loop bound`

**Key principle:** A mutation detection test only needs to show that the behavior is in the correct partition (e.g., the element IS found, the result IS non-empty, the exception IS raised). It does not need to assert the exact value.

---

## Scope Constraint
Only generate tests for the specific function named in the `## Function` section. Do NOT test helper functions it calls, class methods it invokes, or adjacent functions in the same file.

---

## Mocking Rules
- **DO** mock arguments and dependencies *passed into* the function. Use `assert_called_once_with(...)` to verify call arguments.
- **DO NOT** mock functions the function imports or calls internally.
- **DO NOT** mock stdlib builtins. Use `tempfile.NamedTemporaryFile` for file-reading functions.
- **DO NOT** mock external services unless they make real network calls.

---

## FORBIDDEN Patterns

- `pytest.warns(None)` — removed in pytest 7.2; causes TypeError
- `pytest.warns(SomeWarning)` when the library raises it as an exception rather than via `warnings.warn()` — use `pytest.raises` instead, or omit the warning assertion entirely
- Asserting private/internal attributes: `bar.pos`, `bar.fp`, `bar.sp`, `obj._anything`
- `from pkg._private import X` unless that exact path appears in the function's own import section
- `assert result == <value>` where the value was derived by mentally tracing the code
- Relative imports: `from .module import X`

---

## Output Format

Return ONLY a complete, runnable pytest file starting directly with import statements.

- At most 20 tests total. One focused test per boundary/class/mutation — diversity over quantity.
- Group tests by technique with section comments: `# --- BVA ---`, `# --- ECP ---`, `# --- Mutation Detection ---`
- If a section adds no new tests over prior sections, omit it with a one-line comment.
- No multi-line docstrings, no prose outside test code.
- Do NOT wrap output in markdown fences or backticks.
- Import safety: use ONLY the import path shown in the `File Path` and `Imports Available` sections. Never construct submodule paths that do not appear there.
- The file must be directly executable with `pytest`.
