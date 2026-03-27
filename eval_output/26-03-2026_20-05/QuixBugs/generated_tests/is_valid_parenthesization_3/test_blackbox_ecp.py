import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# Valid equivalence class: balanced parentheses
def test_valid_balanced_parentheses():
    assert is_valid_parenthesization("(())") == True

# Valid equivalence class: empty string (trivially valid)
def test_valid_empty_string():
    assert is_valid_parenthesization("") == True

# Valid equivalence class: single matching pair
def test_valid_single_pair():
    assert is_valid_parenthesization("()") == True

# Valid equivalence class: multiple sequential pairs
def test_valid_sequential_pairs():
    assert is_valid_parenthesization("()()") == True

# Invalid equivalence class: more closing than opening parens (depth goes negative)
def test_invalid_closing_before_opening():
    assert is_valid_parenthesization(")(") == False

# Invalid equivalence class: unmatched opening parens (depth > 0 at end)
def test_invalid_unmatched_opening():
    assert is_valid_parenthesization("(()") == False

# Invalid equivalence class: only closing parens
def test_invalid_only_closing():
    assert is_valid_parenthesization(")") == False

# Invalid equivalence class: only opening parens
def test_invalid_only_opening():
    assert is_valid_parenthesization("(") == False

# Invalid equivalence class: deeply nested but mismatched
def test_invalid_deeply_nested_mismatched():
    assert is_valid_parenthesization("((())") == False

# Valid equivalence class: deeply nested and balanced
def test_valid_deeply_nested_balanced():
    assert is_valid_parenthesization("((()))") == True