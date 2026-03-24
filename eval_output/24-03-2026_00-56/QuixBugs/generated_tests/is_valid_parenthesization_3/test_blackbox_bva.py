import pytest
from correct_python_programs.is_valid_parenthesization import is_valid_parenthesization

def test_empty_string():
    assert is_valid_parenthesization("") == True

def test_single_opening():
    assert is_valid_parenthesization("(") == False

def test_single_closing():
    assert is_valid_parenthesization(")") == False

def test_minimal_valid_pair():
    assert is_valid_parenthesization("()") == True

def test_nested_valid_small():
    assert is_valid_parenthesization("(())") == True

def test_sequence_valid_small():
    assert is_valid_parenthesization("()()") == True

def test_imbalanced_extra_opening():
    assert is_valid_parenthesization("(()") == False

def test_imbalanced_extra_closing():
    assert is_valid_parenthesization("())") == False

def test_starts_with_closing():
    assert is_valid_parenthesization(")(") == False

def test_long_valid_sequence():
    assert is_valid_parenthesization("((()())())") == True

def test_long_invalid_sequence():
    assert is_valid_parenthesization("((()())()") == False

def test_max_depth_one():
    assert is_valid_parenthesization("((()))") == True

def test_depth_goes_negative_early():
    assert is_valid_parenthesization("())(") == False