_(showing 10 of 16 failures)_

## Trigger Test(s)

```python
# test_blackbox_bva.py
import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

def test_empty_string():
    # Empty string: no parens, depth stays 0, should be valid
    assert is_valid_parenthesization('') == True

def test_single_open_paren():
    # Single '(' leaves depth=1 at end, should be invalid
    assert is_valid_parenthesization('(') == False

def test_single_close_paren():
    # Single ')' causes depth to go negative immediately, should be invalid
    assert is_valid_parenthesization(')') == False

def test_minimal_valid_pair():
    # Minimal valid case: one matched pair
    assert is_valid_parenthesization('()') == True

def test_minimal_invalid_reversed():
    # Reversed minimal pair: closes before opens
    assert is_valid_parenthesization(')(') == False

def test_two_pairs_sequential():
    # Two sequential matched pairs
    assert is_valid_parenthesization('()()') == True

def test_two_pairs_nested():
    # Two nested matched pairs
    assert is_valid_parenthesization('(())') == True

def test_unmatched_extra_open():
    # More opens than closes
    assert is_valid_parenthesization('(()') == False

def test_unmatched_extra_close():
    # More closes than opens
    assert is_valid_parenthesization('())') == False

def test_closes_before_opens_long():
    # Closes appear before matching opens in longer string
    assert is_valid_parenthesization(')(()') == False

def test_deeply_nested_valid():
    # Deeply nested valid parenthesization
    assert is_valid_parenthesization('(((())))') == True

def test_deeply_nested_missing_close():
    # Deeply nested but missing one closing paren
    assert is_valid_parenthesization('(((())))(' ) == False

def test_deeply_nested_extra_close():
    # Deeply nested but one extra closing paren at end
    assert is_valid_parenthesization('(((()))))') == False

def test_alternating_valid():
    # Alternating open/close repeated multiple times
    assert is_valid_parenthesization('()()()()') == True

def test_close_in_middle_of_opens():
    # Close paren appears mid-sequence causing early negative depth
    assert is_valid_parenthesization('(())(') == False

def test_all_opens():
    # All opens, no closes: depth never goes negative but not zero at end
    assert is_valid_parenthesization('((((') == False

def test_all_closes():
    # All closes: depth goes negative immediately
    assert is_valid_parenthesization('))))') == False

def test_valid_complex():
    # Complex valid nesting: (()(()))
    assert is_valid_parenthesization('(()(()))') == True

def test_invalid_complex_close_early():
    # Complex invalid: )()( - starts with close
    assert is_valid_parenthesization(')()(') == False

def test_return_type_is_bool_on_valid():
    result = is_valid_parenthesization('()')
    assert isinstance(result, bool)

def test_return_type_is_bool_on_invalid():
    result = is_valid_parenthesization('(')
    assert isinstance(result, bool)

def test_long_valid_string():
    # Long balanced string of pairs
    s = '()' * 1000
    assert is_valid_parenthesization(s) == True

def test_long_invalid_extra_open():
    # Long string with one extra open at the end
    s = '()' * 1000 + '('
    assert is_valid_parenthesization(s) == False

def test_long_invalid_early_close():
    # Long string starting with a close
    s = ')' + '()' * 999
    assert is_valid_parenthesization(s) == False
```

```python
# test_blackbox_ecp.py
import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# Valid equivalence class: balanced parentheses
def test_valid_balanced_parentheses():
    assert is_valid_parenthesization("()") == True

# Valid equivalence class: multiple balanced pairs
def test_valid_multiple_balanced_pairs():
    assert is_valid_parenthesization("()()") == True

# Valid equivalence class: nested balanced parentheses
def test_valid_nested_balanced():
    assert is_valid_parenthesization("(())") == True

# Valid equivalence class: empty string (trivially valid)
def test_valid_empty_string():
    assert is_valid_parenthesization("") == True

# Invalid equivalence class: unmatched closing paren (depth goes negative)
def test_invalid_unmatched_closing():
    assert is_valid_parenthesization(")(") == False

# Invalid equivalence class: more closing than opening parens
def test_invalid_more_closing_than_opening():
    assert is_valid_parenthesization("())") == False

# Invalid equivalence class: unmatched opening paren (depth > 0 at end)
def test_invalid_unmatched_opening():
    assert is_valid_parenthesization("(") == False

# Invalid equivalence class: multiple unmatched opening parens
def test_invalid_multiple_unmatched_opening():
    assert is_valid_parenthesization("(((") == False

# Invalid equivalence class: closing before any opening
def test_invalid_closing_before_opening():
    assert is_valid_parenthesization(")") == False

# Valid equivalence class: complex nested and sequential balanced
def test_valid_complex_balanced():
    assert is_valid_parenthesization("((()))()") == True

# Invalid equivalence class: interleaved unmatched
def test_invalid_interleaved_unmatched():
    assert is_valid_parenthesization("(()") == False
```

```python
# test_blackbox_mutation.py
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# catches: missing final depth == 0 check (unbalanced but never negative)
def test_unmatched_open_parens():
    assert is_valid_parenthesization("(") == False

# catches: missing final depth == 0 check (multiple unclosed opens)
def test_multiple_unclosed_opens():
    assert is_valid_parenthesization("(((") == False

# catches: missing final depth == 0 check (opens and closes but not balanced)
def test_more_opens_than_closes():
    assert is_valid_parenthesization("(()") == False

# catches: "depth < 0" mutated to "depth <= 0" (off-by-one in early return)
def test_single_valid_pair():
    assert is_valid_parenthesization("()") == True

# catches: "depth -= 1" mutated to "depth += 1" (wrong operator on close paren)
def test_close_before_open_is_invalid():
    assert is_valid_parenthesization(")(") == False

# catches: "depth < 0" mutated to "depth > 0" (negated condition)
def test_immediate_close_is_invalid():
    assert is_valid_parenthesization(")") == False

# catches: "depth += 1" mutated to "depth -= 1" (wrong operator on open paren)
def test_nested_valid():
    assert is_valid_parenthesization("(())") == True

# catches: early return True instead of continuing loop
def test_valid_sequence_multiple_pairs():
    assert is_valid_parenthesization("()()") == True

# catches: missing final depth == 0 check (depth goes up and never comes back)
def test_opens_then_closes_unbalanced():
    assert is_valid_parenthesization("(()((") == False

# catches: return False mutated to return True (wrong return value in early exit)
def test_invalid_interleaved():
    assert is_valid_parenthesization(")()(") == False

# catches: depth initialized to wrong value (e.g., depth = 1)
def test_empty_string_is_valid():
    assert is_valid_parenthesization("") == True

# catches: final check off-by-one (depth == 0 vs depth <= 0)
def test_perfectly_balanced_complex():
    assert is_valid_parenthesization("((()))") == True

# catches: loop not processing all characters (e.g., off-by-one in iteration)
def test_last_char_causes_invalidity():
    assert is_valid_parenthesization("()(") == False

# catches: paren == '(' mutated to paren != '(' (wrong branch taken)
def test_only_close_parens():
    assert is_valid_parenthesization(")))") == False

# catches: missing final depth == 0 check with exact depth at end
def test_two_opens_one_close():
    assert is_valid_parenthesization("()(()") == False
```

## Error Message(s)

### [FAILURE] test_single_open_paren (type: blackbox_bva)
Assertion: assert is_valid_parenthesization('(') == False
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_bva.py:10: in test_single_open_paren
    assert is_valid_parenthesization('(') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(')
```

### [FAILURE] test_unmatched_extra_open (type: blackbox_bva)
Assertion: assert is_valid_parenthesization('(()') == False
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_bva.py:34: in test_unmatched_extra_open
    assert is_valid_parenthesization('(()') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(()')
```

### [FAILURE] test_deeply_nested_missing_close (type: blackbox_bva)
Assertion: assert is_valid_parenthesization('(((())))(' ) == False
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_bva.py:50: in test_deeply_nested_missing_close
    assert is_valid_parenthesization('(((())))(' ) == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(((())))(')
```

### [FAILURE] test_close_in_middle_of_opens (type: blackbox_bva)
Assertion: assert is_valid_parenthesization('(())(') == False
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_bva.py:62: in test_close_in_middle_of_opens
    assert is_valid_parenthesization('(())(') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(())(')
```

### [FAILURE] test_all_opens (type: blackbox_bva)
Assertion: assert is_valid_parenthesization('((((') == False
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_bva.py:66: in test_all_opens
    assert is_valid_parenthesization('((((') == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('((((')
```

### [FAILURE] test_long_invalid_extra_open (type: blackbox_bva)
Assertion: assert is_valid_parenthesization(s) == False
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_bva.py:96: in test_long_invalid_extra_open
    assert is_valid_parenthesization(s) == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()(...)()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()(')
```

### [FAILURE] test_invalid_unmatched_opening (type: blackbox_ecp)
Assertion: assert is_valid_parenthesization("(") == False
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_ecp.py:30: in test_invalid_unmatched_opening
    assert is_valid_parenthesization("(") == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(')
```

### [FAILURE] test_invalid_multiple_unmatched_opening (type: blackbox_ecp)
Assertion: assert is_valid_parenthesization("(((") == False
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_ecp.py:34: in test_invalid_multiple_unmatched_opening
    assert is_valid_parenthesization("(((") == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(((')
```

### [FAILURE] test_invalid_interleaved_unmatched (type: blackbox_ecp)
Assertion: assert is_valid_parenthesization("(()") == False
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_ecp.py:46: in test_invalid_interleaved_unmatched
    assert is_valid_parenthesization("(()") == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(()')
```

### [FAILURE] test_unmatched_open_parens (type: blackbox_mutation)
Assertion: assert is_valid_parenthesization("(") == False
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_mutation.py:5: in test_unmatched_open_parens
    assert is_valid_parenthesization("(") == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(')
```
