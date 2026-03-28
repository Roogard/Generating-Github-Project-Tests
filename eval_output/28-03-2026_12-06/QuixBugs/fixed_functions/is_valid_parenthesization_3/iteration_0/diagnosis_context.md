_(showing 10 of 14 failures)_

## Trigger Test(s)

```python
# test_blackbox.py
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# --- BVA ---

def test_empty_string():
    # Empty string: no parens, depth never goes negative, should be valid
    assert is_valid_parenthesization('') == True

def test_single_open_paren():
    # Single '(': depth ends at 1, never negative — but unmatched, correct impl SHOULD return False
    assert is_valid_parenthesization('(') == False

def test_single_close_paren():
    # Single ')': depth goes to -1 immediately, correct impl SHOULD return False
    assert is_valid_parenthesization(')') == False

def test_minimal_valid_pair():
    # Smallest valid: "()"
    assert is_valid_parenthesization('()') == True

def test_minimal_invalid_reversed():
    # Reversed smallest: ")("
    assert is_valid_parenthesization(')(') == False

def test_two_open_one_close():
    # "((" — two opens, one close missing, unmatched
    assert is_valid_parenthesization('((' ) == False

def test_one_open_two_close():
    # "())" — extra close
    assert is_valid_parenthesization('())') == False

def test_large_valid():
    # Large balanced string: 1000 matched pairs
    s = '()' * 1000
    assert is_valid_parenthesization(s) == True

def test_large_invalid_extra_open():
    # 1000 matched pairs + one open at end
    s = '()' * 1000 + '('
    assert is_valid_parenthesization(s) == False

def test_large_invalid_extra_close():
    # 1000 matched pairs + one close at end
    s = '()' * 1000 + ')'
    assert is_valid_parenthesization(s) == False

# --- ECP ---

def test_valid_nested():
    # Valid class: properly nested parens
    assert is_valid_parenthesization('((()))') == True

def test_valid_sequential():
    # Valid class: sequential pairs
    assert is_valid_parenthesization('()()()') == True

def test_invalid_early_close():
    # Invalid class: closing paren before any opening
    assert is_valid_parenthesization(')(()') == False

def test_invalid_unmatched_open():
    # Invalid class: more opens than closes
    assert is_valid_parenthesization('(()') == False

def test_invalid_unmatched_close():
    # Invalid class: more closes than opens
    assert is_valid_parenthesization('())') == False

def test_valid_complex_nested():
    # Valid class: complex nested and sequential mix
    assert is_valid_parenthesization('(())(()())') == True

def test_invalid_interleaved():
    # Invalid class: interleaved unmatched
    assert is_valid_parenthesization('(()(') == False

def test_all_opens():
    # Invalid class: all opening parens
    assert is_valid_parenthesization('((((') == False

def test_all_closes():
    # Invalid class: all closing parens
    assert is_valid_parenthesization('))))') == False

# --- Mutation Detection ---

def test_mutation_off_by_one_depth_check():
    # Detects mutation: `depth < 0` changed to `depth <= 0`
    # "()" — after '(' depth=1, after ')' depth=0; should be VALID
    # A mutant using depth<=0 would return False here incorrectly
    assert is_valid_parenthesization('()') == True

def test_mutation_depth_never_goes_negative_but_unmatched():
    # Detects mutation: missing final `depth == 0` check
    # A correct is_valid_parenthesization SHOULD return False for unmatched '('
    # because the parenthesization is not valid — depth ends at 1
    assert is_valid_parenthesization('(') == False

def test_mutation_depth_increment_vs_decrement():
    # Detects mutation: `depth += 1` changed to `depth -= 1`
    # "(())" — valid; a mutant swapping +/- for '(' would produce wrong depth
    assert is_valid_parenthesization('(())') == True

def test_mutation_return_true_vs_false_on_negative():
    # Detects mutation: `return False` changed to `return True` inside depth<0 branch
    assert is_valid_parenthesization(')(') == False

def test_mutation_final_return_flipped():
    # Detects mutation: final `return True` changed to `return False`
    # A well-balanced string must return True
    assert is_valid_parenthesization('(())()') == True

def test_mutation_depth_lt_vs_lte_boundary():
    # Detects mutation: `depth < 0` changed to `depth <= 0`
    # "()()" — depth hits 0 after each pair legitimately; must remain True
    assert is_valid_parenthesization('()()') == True

def test_mutation_unmatched_open_two():
    # Detects mutation: final check absent (always returns True at end)
    # "(()" — depth ends at 1, must be False
    assert is_valid_parenthesization('(()') == False

def test_mutation_unmatched_open_deep():
    # Detects mutation: final depth check missing
    # "((((()))" — opens=5, closes=3, depth ends at 2, must be False
    assert is_valid_parenthesization('((((())') == False

def test_mutation_wrong_variable_depth():
    # Detects mutation: checking wrong variable in the depth < 0 condition
    # ")(" — first char ')' should immediately make depth -1 and return False
    assert is_valid_parenthesization(')(') == False

def test_mutation_off_by_one_loop_range():
    # If the loop were range(len(parens)-1) instead of iterating all chars,
    # a single unmatched ')' at the last position would be missed.
    # "())" — last ')' is the extra one; must return False
    assert is_valid_parenthesization('())') == False
```

```python
# test_whitebox.py
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# --- Statement Coverage ---

def test_stmt_empty_string():
    # Empty string: loop body never executes, returns True
    # A correct validator should accept empty string (depth stays 0)
    assert is_valid_parenthesization('') == True

def test_stmt_open_paren_branch():
    # Exercises depth += 1 branch (open paren)
    # "()" is valid: depth goes 1 then 0
    assert is_valid_parenthesization('()') == True

def test_stmt_close_paren_negative_depth():
    # Exercises depth -= 1 and the early return False (depth < 0)
    # A single ')' causes depth to go negative: invalid
    assert is_valid_parenthesization(')') == False

def test_stmt_unmatched_open():
    # Exercises path where depth != 0 at end but never goes negative
    # "((" has depth 2 at end: a correct validator should return False
    assert is_valid_parenthesization('((') == False

# --- Block Coverage ---

def test_block_matched_parens():
    # Covers: function entry, open-paren block, close-paren block (depth stays >= 0),
    # loop-exit block, final return True
    # "(())" is valid
    assert is_valid_parenthesization('(())') == True

def test_block_early_return_false():
    # Covers: close-paren block where depth < 0 → early return False
    # ")(" triggers depth < 0 on first char
    assert is_valid_parenthesization(')(') == False

def test_block_close_no_negative():
    # Covers: close-paren block where depth decrements but does NOT go negative
    # then loop continues
    # "()()" exercises close-paren block multiple times without going negative
    assert is_valid_parenthesization('()()') == True

# --- Condition Coverage ---

def test_cond_paren_is_open_true():
    # paren == '(': True
    # depth goes to 1, then final return depends on depth == 0
    # Single '(' leaves depth=1: correct validator returns False
    assert is_valid_parenthesization('(') == False  # paren=='(': True

def test_cond_paren_is_open_false_depth_not_negative():
    # paren == '(': False (it's ')'), depth < 0: False (depth was 1, becomes 0)
    # "()" is valid
    assert is_valid_parenthesization('()') == True  # paren=='(': False, depth<0: False

def test_cond_depth_lt_zero_true():
    # paren == '(': False, depth < 0: True
    # ")" causes depth to go -1 → early return False
    assert is_valid_parenthesization(')') == False  # depth<0: True

def test_cond_depth_lt_zero_false_then_end_nonzero():
    # paren == '(': False, depth < 0: False (depth goes 1 → 0, then 1 at end)
    # "()(" has depth=1 at end: correct validator returns False
    assert is_valid_parenthesization('()(') == False  # paren=='(': both T&F, depth<0: False

# --- Path Coverage ---

def test_path_empty_directly_returns_true():
    # path: loop-zero-iterations → return True
    assert is_valid_parenthesization('') == True

def test_path_all_open_no_early_return():
    # path: loop-multiple-iters (all open parens) → final return
    # depth never < 0, but ends > 0: correct validator returns False
    assert is_valid_parenthesization('(((') == False

def test_path_immediate_early_return():
    # path: loop-1-iter → close paren → depth<0 → return False
    assert is_valid_parenthesization(')') == False

def test_path_early_return_mid_loop():
    # path: loop-multiple-iters → open → close → close (depth<0) → return False
    # "()" then ")" = "())"
    assert is_valid_parenthesization('())') == False

def test_path_single_open_close():
    # path: loop-2-iters (open then close, depth never negative) → return True (depth==0)
    assert is_valid_parenthesization('()') == True

def test_path_multiple_iters_balanced():
    # path: loop-many-iters, all close-parens keep depth >=0, final depth==0 → True
    assert is_valid_parenthesization('((()))') == True

def test_path_multiple_iters_unbalanced_open():
    # path: loop-many-iters, never early return, but depth > 0 at end → False
    assert is_valid_parenthesization('(()') == False

def test_path_interleaved_valid():
    # path: multiple open/close transitions, no negative depth, depth==0 at end
    assert is_valid_parenthesization('(()())') == True
```

## Error Message(s)

### [FAILURE] test_single_open_paren (type: blackbox)
Assertion: assert is_valid_parenthesization('(') == False
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox.py:11: in test_single_open_paren
    assert is_valid_parenthesization('(') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(')
```

### [FAILURE] test_two_open_one_close (type: blackbox)
Assertion: assert is_valid_parenthesization('((' ) == False
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox.py:27: in test_two_open_one_close
    assert is_valid_parenthesization('((' ) == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('((')
```

### [FAILURE] test_large_invalid_extra_open (type: blackbox)
Assertion: assert is_valid_parenthesization(s) == False
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox.py:41: in test_large_invalid_extra_open
    assert is_valid_parenthesization(s) == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()(...)()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()(')
```

### [FAILURE] test_invalid_unmatched_open (type: blackbox)
Assertion: assert is_valid_parenthesization('(()') == False
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox.py:64: in test_invalid_unmatched_open
    assert is_valid_parenthesization('(()') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(()')
```

### [FAILURE] test_invalid_interleaved (type: blackbox)
Assertion: assert is_valid_parenthesization('(()(') == False
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox.py:76: in test_invalid_interleaved
    assert is_valid_parenthesization('(()(') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(()(')
```

### [FAILURE] test_all_opens (type: blackbox)
Assertion: assert is_valid_parenthesization('((((') == False
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox.py:80: in test_all_opens
    assert is_valid_parenthesization('((((') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('((((')
```

### [FAILURE] test_mutation_depth_never_goes_negative_but_unmatched (type: blackbox)
Assertion: assert is_valid_parenthesization('(') == False
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox.py:98: in test_mutation_depth_never_goes_negative_but_unmatched
    assert is_valid_parenthesization('(') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(')
```

### [FAILURE] test_mutation_unmatched_open_two (type: blackbox)
Assertion: assert is_valid_parenthesization('(()') == False
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox.py:122: in test_mutation_unmatched_open_two
    assert is_valid_parenthesization('(()') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(()')
```

### [FAILURE] test_mutation_unmatched_open_deep (type: blackbox)
Assertion: assert is_valid_parenthesization('((((())') == False
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox.py:127: in test_mutation_unmatched_open_deep
    assert is_valid_parenthesization('((((())') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('((((())')
```

### [FAILURE] test_stmt_unmatched_open (type: whitebox)
Assertion: assert is_valid_parenthesization('((') == False
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\is_valid_parenthesization_3\test_whitebox.py:23: in test_stmt_unmatched_open
    assert is_valid_parenthesization('((') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('((')
```
