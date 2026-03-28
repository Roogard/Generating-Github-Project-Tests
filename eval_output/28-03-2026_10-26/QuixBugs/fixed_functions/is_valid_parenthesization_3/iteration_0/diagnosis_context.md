_(showing 10 of 19 failures)_

## Trigger Test(s)

```python
# test_blackbox_bva.py
from python_programs.is_valid_parenthesization import is_valid_parenthesization

def test_empty_string():
    # A correct parenthesization validator SHOULD return True for an empty string (no unmatched parens)
    result = is_valid_parenthesization("")
    assert result == True

def test_single_open_paren():
    # A correct validator SHOULD return False for a single unmatched '('
    result = is_valid_parenthesization("(")
    assert result == False

def test_single_close_paren():
    # A correct validator SHOULD return False for a single unmatched ')'
    result = is_valid_parenthesization(")")
    assert result == False

def test_single_matched_pair():
    # A correct validator SHOULD return True for "()"
    result = is_valid_parenthesization("()")
    assert result == True

def test_two_open_parens():
    # A correct validator SHOULD return False for "((" — depth never returns to 0
    result = is_valid_parenthesization("((")
    assert result == False

def test_two_close_parens():
    # A correct validator SHOULD return False for "))" — immediate depth < 0
    result = is_valid_parenthesization("))")
    assert result == False

def test_close_before_open():
    # A correct validator SHOULD return False for ")(" — close before open
    result = is_valid_parenthesization(")(")
    assert result == False

def test_open_before_close():
    # A correct validator SHOULD return True for "()" — standard valid pair
    result = is_valid_parenthesization("()")
    assert result == True

def test_nested_valid():
    # A correct validator SHOULD return True for "(())"
    result = is_valid_parenthesization("(())")
    assert result == True

def test_nested_invalid_extra_open():
    # A correct validator SHOULD return False for "(()" — one unmatched open remains
    result = is_valid_parenthesization("(()")
    assert result == False

def test_nested_invalid_extra_close():
    # A correct validator SHOULD return False for "())" — one extra close
    result = is_valid_parenthesization("())")
    assert result == False

def test_long_valid_sequence():
    # A correct validator SHOULD return True for a perfectly balanced long sequence
    result = is_valid_parenthesization("()()()()()")
    assert result == True

def test_long_invalid_extra_open():
    # A correct validator SHOULD return False when there are more opens than closes
    result = is_valid_parenthesization("()()()()()(")
    assert result == False

def test_long_invalid_extra_close():
    # A correct validator SHOULD return False when there are more closes than opens
    result = is_valid_parenthesization("()()()()())")
    assert result == False

def test_deeply_nested_valid():
    # A correct validator SHOULD return True for deeply nested matching parens
    result = is_valid_parenthesization("((((((()))))))")
    assert result == True

def test_deeply_nested_one_extra_open():
    # A correct validator SHOULD return False — depth is 1 at end, not 0
    result = is_valid_parenthesization("((((((("))
    assert result == False

def test_interleaved_valid():
    # A correct validator SHOULD return True for "(()())"
    result = is_valid_parenthesization("(()())")
    assert result == True

def test_interleaved_invalid():
    # A correct validator SHOULD return False for "(()()" — one open unmatched
    result = is_valid_parenthesization("(()()")
    assert result == False

def test_close_at_end_after_balanced():
    # A correct validator SHOULD return False for "()(" — extra open at the end
    result = is_valid_parenthesization("()(")
    assert result == False

def test_return_type_is_bool_valid():
    result = is_valid_parenthesization("()")
    assert isinstance(result, bool)

def test_return_type_is_bool_invalid():
    result = is_valid_parenthesization(")(")
    assert isinstance(result, bool)
```

```python
# test_blackbox_ecp.py
import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# Valid equivalence class: balanced parentheses — simple matched pair
def test_valid_simple_balanced():
    result = is_valid_parenthesization("()")
    assert result == True

# Valid equivalence class: multiple nested balanced parentheses
def test_valid_nested_balanced():
    result = is_valid_parenthesization("((()))")
    assert result == True

# Valid equivalence class: multiple sequential balanced pairs
def test_valid_sequential_balanced():
    result = is_valid_parenthesization("()()()")
    assert result == True

# Valid equivalence class: empty string — trivially balanced
def test_valid_empty_string():
    result = is_valid_parenthesization("")
    assert result == True

# Invalid equivalence class: unmatched closing paren — depth goes negative
def test_invalid_unmatched_closing():
    result = is_valid_parenthesization(")(")
    # A correct validator MUST return False when a closing paren has no matching opener
    assert result == False

# Invalid equivalence class: more opening than closing parens — depth > 0 at end
def test_invalid_unmatched_opening():
    result = is_valid_parenthesization("(()")
    # A correct validator MUST return False when opening parens are left unmatched
    assert result == False

# Invalid equivalence class: all closing parens, no opening
def test_invalid_all_closing():
    result = is_valid_parenthesization(")))")
    # A correct validator MUST return False when there are no matching openers
    assert result == False

# Invalid equivalence class: all opening parens, no closing
def test_invalid_all_opening():
    result = is_valid_parenthesization("(((")
    # A correct validator MUST return False because depth never returns to 0
    assert result == False

# Invalid equivalence class: closing before opening in nested context
def test_invalid_wrong_order_nested():
    result = is_valid_parenthesization("())(")
    # A correct validator MUST return False — closing paren appears before its opener
    assert result == False
```

```python
# test_blackbox_mutation.py
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# catches: missing final "depth == 0" check — unmatched '(' should return False
def test_unmatched_open_paren_single():
    assert is_valid_parenthesization("(") == False

# catches: missing final "depth == 0" check — multiple unmatched '(' should return False
def test_unmatched_open_paren_multiple():
    assert is_valid_parenthesization("(()") == False

# catches: missing final "depth == 0" check — all opens, no closes
def test_all_open_parens():
    assert is_valid_parenthesization("((((") == False

# catches: "depth < 0" mutated to "depth <= 0" — valid string rejected
def test_single_valid_pair():
    assert is_valid_parenthesization("()") == True

# catches: "depth < 0" mutated to "depth > 0" — close before open not caught
def test_close_before_open():
    assert is_valid_parenthesization(")(") == False

# catches: "depth -= 1" mutated to "depth += 1" — unmatched close not detected
def test_unmatched_close_paren():
    assert is_valid_parenthesization(")") == False

# catches: "depth += 1" mutated to "depth -= 1" — valid deep nesting rejected
def test_nested_valid():
    assert is_valid_parenthesization("((()))") == True

# catches: "depth += 1" mutated to "depth = 1" — repeated opens not counted correctly
def test_multiple_valid_pairs():
    assert is_valid_parenthesization("()()()") == True

# catches: "return False" mutated to "return True" inside negative-depth branch
def test_close_only():
    assert is_valid_parenthesization(")()") == False

# catches: final return True mutated to return False — genuinely valid string rejected
def test_empty_string():
    assert is_valid_parenthesization("") == True

# catches: missing final depth == 0 check — two extra opens at end
def test_two_extra_opens():
    assert is_valid_parenthesization("()((") == False

# catches: off-by-one in depth < 0 vs depth <= 0 — depth hits exactly 0 then closes
def test_depth_returns_to_zero_then_closes():
    assert is_valid_parenthesization("())") == False

# catches: condition paren == '(' mutated to paren != '(' — open treated as close
def test_only_opens():
    assert is_valid_parenthesization("(((") == False

# catches: depth reset or wrong variable — interleaved valid pairs
def test_interleaved_valid():
    assert is_valid_parenthesization("(())()") == True

# catches: final check missing — one open never closed in complex expression
def test_complex_unbalanced():
    assert is_valid_parenthesization("(()(()") == False

# catches: final check missing — valid deeply nested then extra open
def test_deep_then_extra_open():
    assert is_valid_parenthesization("((()))(" ) == False
```

## Error Message(s)

### [ERROR] __collection_error__ (type: blackbox_bva)
```
=================================== ERRORS ====================================
_ ERROR collecting eval_output/28-03-2026_10-26/QuixBugs/generated_tests/is_valid_parenthesization_3/test_blackbox_bva.py _
.venv\Lib\site-packages\_pytest\python.py:507: in importtestmodule
    mod = import_path(
.venv\Lib\site-packages\_pytest\pathlib.py:587: in import_path
    importlib.import_module(module_name)
..\..\..\..\AppData\Roaming\uv\python\cpython-3.14.3-windows-x86_64-none\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1398: in _gcd_import
  ...truncated...
<frozen importlib._bootstrap>:1342: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:938: in _load_unlocked
    ???
.venv\Lib\site-packages\_pytest\assertion\rewrite.py:188: in exec_module
    source_stat, co = _rewrite_test(fn, self.config)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\_pytest\assertion\rewrite.py:357: in _rewrite_test
    tree = ast.parse(source, filename=strfn)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Roaming\uv\python\cpython-3.14.3-windows-x86_64-none\Lib\ast.py:46: in parse
    return compile(source, filename, mode, flags,
E     File "C:\Users\roota\OneDrive\Desktop\Projects\Generating-Github-Project-Tests\eval_output\28-03-2026_10-26\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_bva.py", line 80
E       result = is_valid_parenthesization("((((((("))
E                                                    ^
E   SyntaxError: unmatched ')'
=========================== short test summary info ===========================
ERROR eval_output/28-03-2026_10-26/QuixBugs/generated_tests/is_valid_parenthesization_3/test_blackbox_bva.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.24s
```

### [FAILURE] test_invalid_unmatched_opening (type: blackbox_ecp)
Assertion: assert result == False
Expected: False
Actual:   True
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_ecp.py:34: in test_invalid_unmatched_opening
    assert result == False
E   assert True == False
```

### [FAILURE] test_invalid_all_opening (type: blackbox_ecp)
Assertion: assert result == False
Expected: False
Actual:   True
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_ecp.py:46: in test_invalid_all_opening
    assert result == False
E   assert True == False
```

### [FAILURE] test_unmatched_open_paren_single (type: blackbox_mutation)
Assertion: assert is_valid_parenthesization("(") == False
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_mutation.py:5: in test_unmatched_open_paren_single
    assert is_valid_parenthesization("(") == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(')
```

### [FAILURE] test_unmatched_open_paren_multiple (type: blackbox_mutation)
Assertion: assert is_valid_parenthesization("(()") == False
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_mutation.py:9: in test_unmatched_open_paren_multiple
    assert is_valid_parenthesization("(()") == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(()')
```

### [FAILURE] test_all_open_parens (type: blackbox_mutation)
Assertion: assert is_valid_parenthesization("((((") == False
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_mutation.py:13: in test_all_open_parens
    assert is_valid_parenthesization("((((") == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('((((')
```

### [FAILURE] test_two_extra_opens (type: blackbox_mutation)
Assertion: assert is_valid_parenthesization("()((") == False
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_mutation.py:45: in test_two_extra_opens
    assert is_valid_parenthesization("()((") == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('()((')
```

### [FAILURE] test_only_opens (type: blackbox_mutation)
Assertion: assert is_valid_parenthesization("(((") == False
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_mutation.py:53: in test_only_opens
    assert is_valid_parenthesization("(((") == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(((')
```

### [FAILURE] test_complex_unbalanced (type: blackbox_mutation)
Assertion: assert is_valid_parenthesization("(()(()") == False
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_mutation.py:61: in test_complex_unbalanced
    assert is_valid_parenthesization("(()(()") == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('(()(()')
```

### [FAILURE] test_deep_then_extra_open (type: blackbox_mutation)
Assertion: assert is_valid_parenthesization("((()))(" ) == False
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\is_valid_parenthesization_3\test_blackbox_mutation.py:65: in test_deep_then_extra_open
    assert is_valid_parenthesization("((()))(" ) == False
E   AssertionError: assert True == False
E    +  where True = is_valid_parenthesization('((()))(')
```
