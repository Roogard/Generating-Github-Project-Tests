import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

def test_valid_empty_string():
    # Valid equivalence class: no parentheses
    assert is_valid_parenthesization("") is True

def test_valid_nested_parentheses():
    # Valid equivalence class: properly nested parentheses
    assert is_valid_parenthesization("((()()))") is True

def test_invalid_too_many_closing():
    # Invalid equivalence class: more closing parentheses than opening at some point
    assert is_valid_parenthesization("())(") is False

def test_invalid_unmatched_opening():
    # Invalid equivalence class: more opening parentheses than closing overall
    assert is_valid_parenthesization("(()") is False