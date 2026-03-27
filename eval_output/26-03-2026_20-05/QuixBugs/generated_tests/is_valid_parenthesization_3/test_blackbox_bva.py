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

def test_two_open_parens():
    assert is_valid_parenthesization('((') == False

def test_two_close_parens():
    assert is_valid_parenthesization('))') == False

def test_close_before_open():
    assert is_valid_parenthesization(')(') == False

def test_open_before_close():
    assert is_valid_parenthesization('()') == True

def test_nested_matched_pair():
    assert is_valid_parenthesization('(())') == True

def test_sequential_matched_pairs():
    assert is_valid_parenthesization('()()') == True

def test_unmatched_extra_open():
    assert is_valid_parenthesization('(()') == False

def test_unmatched_extra_close():
    assert is_valid_parenthesization('())') == False

def test_deeply_nested_matched():
    assert is_valid_parenthesization('(((())))') == True

def test_deeply_nested_extra_close():
    assert is_valid_parenthesization('((())))')  == False

def test_deeply_nested_extra_open():
    assert is_valid_parenthesization('(((()))') == False

def test_close_then_matched():
    assert is_valid_parenthesization(')(()') == False

def test_matched_then_close():
    assert is_valid_parenthesization('())') == False

def test_alternating_mismatched():
    assert is_valid_parenthesization(')()(') == False

def test_long_balanced_string():
    assert is_valid_parenthesization('()' * 50) == True

def test_long_unbalanced_extra_open():
    assert is_valid_parenthesization('(' * 51 + ')' * 50) == False

def test_long_unbalanced_extra_close():
    assert is_valid_parenthesization('(' * 50 + ')' * 51) == False

def test_long_all_open():
    assert is_valid_parenthesization('(' * 100) == False

def test_long_all_close():
    assert is_valid_parenthesization(')' * 100) == False

def test_depth_returns_to_zero_multiple_times():
    assert is_valid_parenthesization('()(())()') == True

def test_depth_goes_negative_in_middle():
    assert is_valid_parenthesization('()()()())))((') == False