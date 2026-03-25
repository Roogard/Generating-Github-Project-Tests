import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

def test_valid_balanced_parentheses():
    assert is_valid_parenthesization("(())()") is True

def test_empty_string():
    assert is_valid_parenthesization("") is True

def test_invalid_too_many_closing():
    assert is_valid_parenthesization(")(") is False

def test_invalid_too_many_opening():
    assert is_valid_parenthesization("(((") is False

def test_invalid_characters():
    assert is_valid_parenthesization("(a)") is False

def test_invalid_type_none():
    with pytest.raises(TypeError):
        is_valid_parenthesization(None)