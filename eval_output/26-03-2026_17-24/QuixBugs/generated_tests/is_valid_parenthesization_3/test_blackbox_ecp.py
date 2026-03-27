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

# Valid equivalence class: multiple nested pairs
def test_valid_nested_pairs():
    assert is_valid_parenthesization("((()))") == True

# Invalid equivalence class: more closing than opening (depth goes negative)
def test_invalid_too_many_closing():
    assert is_valid_parenthesization(")(") == False

# Invalid equivalence class: unmatched opening parentheses (depth never returns to zero)
def test_invalid_unmatched_opening():
    assert is_valid_parenthesization("(()") == False

# Invalid equivalence class: closing before any opening
def test_invalid_closing_before_opening():
    assert is_valid_parenthesization(")") == False

# Invalid equivalence class: all opening parentheses no closing
def test_invalid_all_opening():
    assert is_valid_parenthesization("(((") == False

# Invalid equivalence class: interleaved but mismatched sequence
def test_invalid_interleaved_mismatched():
    assert is_valid_parenthesization("()()(") == False