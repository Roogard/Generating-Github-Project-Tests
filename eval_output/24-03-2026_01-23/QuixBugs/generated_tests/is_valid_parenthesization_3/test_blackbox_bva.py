import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

def test_empty_string_returns_true():
    assert is_valid_parenthesization("") is True

def test_single_open_parenthesis_returns_true():
    assert is_valid_parenthesization("(") is True

def test_single_close_parenthesis_returns_false():
    assert is_valid_parenthesization(")") is False

def test_two_balanced_parentheses_returns_true():
    assert is_valid_parenthesization("()") is True

def test_two_unbalanced_open_parentheses_returns_true():
    assert is_valid_parenthesization("((") is True

def test_two_unbalanced_close_parentheses_returns_false():
    assert is_valid_parenthesization("))") is False

def test_unbalanced_close_at_start_returns_false():
    assert is_valid_parenthesization(")(") is False

def test_complex_valid_parenthesization_returns_true():
    assert is_valid_parenthesization("(())()") is True