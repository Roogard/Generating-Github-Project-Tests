import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

def test_empty_string():
    assert is_valid_parenthesization('') == True

def test_single_open_paren():
    assert is_valid_parenthesization('(') == False

def test_single_close_paren():
    assert is_valid_parenthesization(')') == False

def test_single_matched_pair():
    assert is_valid_parenthesization('()') == True

def test_two_matched_pairs():
    assert is_valid_parenthesization('()()') == True

def test_nested_matched_pair():
    assert is_valid_parenthesization('(())') == True

def test_open_then_unmatched_close():
    assert is_valid_parenthesization('(()') == False

def test_close_before_open():
    assert is_valid_parenthesization(')(') == False

def test_all_open_parens():
    assert is_valid_parenthesization('((((') == False

def test_all_close_parens():
    assert is_valid_parenthesization('))))') == False

def test_close_immediately_exceeds_depth():
    assert is_valid_parenthesization(')(()') == False

def test_deeply_nested_valid():
    assert is_valid_parenthesization('(((())))') == True

def test_deeply_nested_one_extra_open():
    assert is_valid_parenthesization('(((()))') == False

def test_deeply_nested_one_extra_close():
    assert is_valid_parenthesization('((())))')  == False

def test_interleaved_valid():
    assert is_valid_parenthesization('(()())') == True

def test_interleaved_invalid_close_first():
    assert is_valid_parenthesization(')()(') == False

def test_two_chars_open_open():
    assert is_valid_parenthesization('((') == False

def test_two_chars_close_close():
    assert is_valid_parenthesization('))') == False

def test_two_chars_close_open():
    assert is_valid_parenthesization(')(') == False

def test_long_valid_sequence():
    assert is_valid_parenthesization('()' * 50) == True

def test_long_invalid_sequence_extra_close():
    assert is_valid_parenthesization('()' * 49 + '))') == False

def test_long_invalid_sequence_extra_open():
    assert is_valid_parenthesization('((' + '()' * 49) == False

def test_depth_returns_to_zero_then_close():
    assert is_valid_parenthesization('()())')  == False

def test_depth_returns_to_zero_then_open():
    assert is_valid_parenthesization('()()(') == False