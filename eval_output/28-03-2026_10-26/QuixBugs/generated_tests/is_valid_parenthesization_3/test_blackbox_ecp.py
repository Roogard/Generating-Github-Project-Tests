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