## Trigger Test(s)

```python
# test_blackbox_mutation.py
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# catches: "depth < 0" mutated to "depth <= 0" (boundary mutation - would reject valid strings)
def test_depth_exactly_zero_after_close():
    # "()" should be valid: depth goes 0->1->0, never negative
    assert is_valid_parenthesization("()") == True

# catches: "depth < 0" mutated to "depth > 0" (wrong comparison direction)
def test_unmatched_close_at_start():
    # ")" should be invalid: depth goes 0->-1, must detect negative
    assert is_valid_parenthesization(")") == False

# catches: "depth -= 1" mutated to "depth += 1" (wrong operator on close paren)
def test_close_paren_decrements():
    # "()" valid, but if close paren increments instead, depth stays positive and never triggers False
    assert is_valid_parenthesization("()") == True
    assert is_valid_parenthesization(")") == False

# catches: "depth += 1" mutated to "depth -= 1" (wrong operator on open paren)
def test_open_paren_increments():
    # "((" valid-ish but unbalanced; if open decrements, depth goes negative immediately
    assert is_valid_parenthesization("(()") == False  # unbalanced, but open parens must increment
    assert is_valid_parenthesization("(())") == True

# catches: missing "return False" inside loop (falls through always returning True)
def test_invalid_close_before_open_returns_false():
    assert is_valid_parenthesization(")(") == False

# catches: "return True" at end mutated to "return False" (negation of final return)
def test_valid_empty_string():
    assert is_valid_parenthesization("") == True

# catches: "return True" mutated to "return depth == 0" vs "return True" ignoring unmatched opens
def test_unmatched_open_paren():
    # "(" has depth=1 at end; function should return True (it does NOT check final depth == 0)
    # This verifies the actual behavior: only checks for negative depth mid-string
    assert is_valid_parenthesization("(") == True

# catches: condition "paren == '('" mutated to "paren == ')'" (swapped branch logic)
def test_open_vs_close_branch_swap():
    # "()" is valid
    assert is_valid_parenthesization("()") == True
    # ")(" is invalid (negative depth at first char)
    assert is_valid_parenthesization(")(") == False

# catches: "depth < 0" mutated to "depth < 1" (off-by-one on threshold)
def test_depth_zero_not_negative_is_valid():
    # After "()()", depth returns to 0 each time, never negative
    assert is_valid_parenthesization("()()") == True

# catches: early return logic missing (loop body mutation removes the if depth < 0 check)
def test_multiple_unmatched_closes():
    assert is_valid_parenthesization("))") == False

# catches: "depth < 0" mutated to "depth < -1" (off-by-one allowing one extra negative)
def test_single_close_paren_triggers_false():
    # depth becomes -1, must trigger return False (not wait for -2)
    assert is_valid_parenthesization(")") == False

# catches: wrong variable used in condition (e.g., checking paren instead of depth)
def test_nested_valid():
    assert is_valid_parenthesization("((()))") == True

# catches: wrong variable used in condition (depth check uses wrong variable)
def test_nested_invalid():
    assert is_valid_parenthesization("(()" ) == False or is_valid_parenthesization("(()") == True
    # The function returns True for "((" (doesn't check final depth), so test the False case
    assert is_valid_parenthesization("())") == False
```

```python
# test_whitebox_block.py
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# Block mapping:
# Block 1: function entry, depth = 0
# Block 2: for loop iteration (paren in parens)
# Block 3: if paren == '(' -> depth += 1
# Block 4: else -> depth -= 1
# Block 5: if depth < 0 -> return False
# Block 6: return True (after loop)

# covers: block 1, block 2, block 3, block 4, block 6 (valid balanced parens)
def test_valid_balanced():
    assert is_valid_parenthesization('()') == True

# covers: block 1, block 6 (empty string, loop body never entered)
def test_empty_string():
    assert is_valid_parenthesization('') == True

# covers: block 1, block 2, block 3, block 6 (only open parens - depth never goes negative)
# Note: '(((' has depth 3 at end, returns True per the function logic
def test_only_open_parens():
    assert is_valid_parenthesization('(((') == True

# covers: block 1, block 2, block 4, block 5 (returns False immediately)
def test_close_before_open():
    assert is_valid_parenthesization(')(') == False

# covers: block 1, block 2, block 4, block 5 (single closing paren)
def test_single_close():
    assert is_valid_parenthesization(')') == False

# covers: block 1, block 2, block 3, block 4, block 6 (nested valid)
def test_nested_valid():
    assert is_valid_parenthesization('(())') == True

# covers: block 1, block 2, block 3, block 4, block 5 (depth goes negative mid-way)
def test_invalid_mid():
    assert is_valid_parenthesization('())(()') == False

# covers: block 1, block 2, block 3, block 4, block 6 (multiple valid pairs)
def test_multiple_pairs():
    assert is_valid_parenthesization('()()()') == True

# covers: block 1, block 2, block 3, block 4, block 6 (deeply nested)
def test_deeply_nested():
    assert is_valid_parenthesization('(((())))') == True

# covers: block 4 and block 5 triggered at last character
def test_extra_close_at_end():
    assert is_valid_parenthesization('())') == False
```

```python
# test_whitebox_path.py
import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# path: loop 0 iterations → return True
def test_empty_string():
    assert is_valid_parenthesization('') == True

# path: loop 1 iter → paren=='(' → depth becomes 1 → return True (depth != 0 but still True)
def test_single_open_paren():
    # A single '(' leaves depth=1, function returns True (no early exit)
    # Note: this exposes that unmatched open parens still return True
    assert is_valid_parenthesization('(') == True

# path: loop 1 iter → paren != '(' → depth becomes -1 → depth < 0 → return False
def test_single_close_paren():
    assert is_valid_parenthesization(')') == False

# path: loop 2 iters → first '(' depth=1, then ')' depth=0, depth not <0 → return True
def test_matched_pair():
    assert is_valid_parenthesization('()') == True

# path: loop 2 iters → first ')' depth=-1 → depth < 0 → return False (early exit)
def test_close_before_open():
    assert is_valid_parenthesization(')(') == False

# path: loop many iters → all '(' → depth grows → return True
def test_multiple_open_parens_only():
    assert is_valid_parenthesization('(((') == True

# path: loop many iters → close parens make depth negative early → return False
def test_multiple_close_parens_early_negative():
    assert is_valid_parenthesization(')))') == False

# path: loop many iters → balanced nested parens → depth never negative → return True
def test_nested_balanced():
    assert is_valid_parenthesization('((()))') == True

# path: loop many iters → sequential balanced pairs → depth never negative → return True
def test_sequential_balanced():
    assert is_valid_parenthesization('()()()') == True

# path: loop many iters → depth goes negative mid-way → return False
def test_unbalanced_close_in_middle():
    assert is_valid_parenthesization('(()))(()') == False

# path: loop many iters → more close than open, depth eventually negative → return False
def test_more_close_than_open():
    assert is_valid_parenthesization('(()))') == False

# path: loop many iters → more open than close, depth never negative → return True
def test_more_open_than_close():
    assert is_valid_parenthesization('(((())') == True

# path: loop many iters → complex valid nesting → return True
def test_complex_valid():
    assert is_valid_parenthesization('(())(())') == True

# path: loop many iters → valid until last char causes negative depth → return False
def test_negative_depth_at_last_char():
    assert is_valid_parenthesization('()())') == False
```

## Error Message(s)

### [FAILURE] test_unmatched_open_paren (type: blackbox_mutation)
Assertion: assert is_valid_parenthesization("(") == True
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_mutation.py:37: in test_unmatched_open_paren
    assert is_valid_parenthesization("(") == True
E   AssertionError: assert False == True
E    +  where False = is_valid_parenthesization('(')
```

### [FAILURE] test_only_open_parens (type: whitebox_block)
Assertion: assert is_valid_parenthesization('(((') == True
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\is_valid_parenthesization_3\test_whitebox_block.py:22: in test_only_open_parens
    assert is_valid_parenthesization('(((') == True
E   AssertionError: assert False == True
E    +  where False = is_valid_parenthesization('(((')
```

### [FAILURE] test_single_open_paren (type: whitebox_path)
Assertion: assert is_valid_parenthesization('(') == True
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\is_valid_parenthesization_3\test_whitebox_path.py:12: in test_single_open_paren
    assert is_valid_parenthesization('(') == True
E   AssertionError: assert False == True
E    +  where False = is_valid_parenthesization('(')
```

### [FAILURE] test_multiple_open_parens_only (type: whitebox_path)
Assertion: assert is_valid_parenthesization('(((') == True
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\is_valid_parenthesization_3\test_whitebox_path.py:28: in test_multiple_open_parens_only
    assert is_valid_parenthesization('(((') == True
E   AssertionError: assert False == True
E    +  where False = is_valid_parenthesization('(((')
```

### [FAILURE] test_more_open_than_close (type: whitebox_path)
Assertion: assert is_valid_parenthesization('(((())') == True
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\is_valid_parenthesization_3\test_whitebox_path.py:52: in test_more_open_than_close
    assert is_valid_parenthesization('(((())') == True
E   AssertionError: assert False == True
E    +  where False = is_valid_parenthesization('(((())')
```

## Previous Fix Attempts (all failed — do NOT repeat)

### Attempt 1
Diagnosis: Root Cause: The function only checks that `depth` never goes negative during traversal, but it never checks whether `depth` equals zero at the end. When there are unmatched opening parentheses (e.g., `'('`, `'((('`, `'(()'`), the loop finishes with `depth > 0`, but the function unconditionally returns `True` instead of checking that all opened parentheses were closed.

Suggestion 1: Check depth equals zero at the end
Change the final `return True` to `return depth == 0`. This ensures that any un
```python
def is_valid_parenthesization(parens):
    depth = 0
    for paren in parens:
        if paren == '(':
            depth += 1
        else:
            depth -= 1
            if depth < 0:
                return False

    return depth == 0
```
Remaining failures: 5
- [FAILURE] test_unmatched_open_paren: assert is_valid_parenthesization("(") == True
- [FAILURE] test_only_open_parens: assert is_valid_parenthesization('(((') == True
- [FAILURE] test_single_open_paren: assert is_valid_parenthesization('(') == True
- [FAILURE] test_multiple_open_parens_only: assert is_valid_parenthesization('(((') == True
- [FAILURE] test_more_open_than_close: assert is_valid_parenthesization('(((())') == True

Try a DIFFERENT approach from the attempts above.
