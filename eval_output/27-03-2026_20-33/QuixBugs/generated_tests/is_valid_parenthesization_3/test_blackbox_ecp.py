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