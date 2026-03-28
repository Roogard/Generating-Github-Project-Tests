import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

def test_empty_string():
    # Empty string: no parens, depth stays 0, should be valid
    assert is_valid_parenthesization('') == True

def test_single_open_paren():
    # Single '(' leaves depth=1 at end, should be invalid
    assert is_valid_parenthesization('(') == False

def test_single_close_paren():
    # Single ')' causes depth to go negative immediately, should be invalid
    assert is_valid_parenthesization(')') == False

def test_minimal_valid_pair():
    # Minimal valid case: one matched pair
    assert is_valid_parenthesization('()') == True

def test_minimal_invalid_reversed():
    # Reversed minimal pair: closes before opens
    assert is_valid_parenthesization(')(') == False

def test_two_pairs_sequential():
    # Two sequential matched pairs
    assert is_valid_parenthesization('()()') == True

def test_two_pairs_nested():
    # Two nested matched pairs
    assert is_valid_parenthesization('(())') == True

def test_unmatched_extra_open():
    # More opens than closes
    assert is_valid_parenthesization('(()') == False

def test_unmatched_extra_close():
    # More closes than opens
    assert is_valid_parenthesization('())') == False

def test_closes_before_opens_long():
    # Closes appear before matching opens in longer string
    assert is_valid_parenthesization(')(()') == False

def test_deeply_nested_valid():
    # Deeply nested valid parenthesization
    assert is_valid_parenthesization('(((())))') == True

def test_deeply_nested_missing_close():
    # Deeply nested but missing one closing paren
    assert is_valid_parenthesization('(((())))(' ) == False

def test_deeply_nested_extra_close():
    # Deeply nested but one extra closing paren at end
    assert is_valid_parenthesization('(((()))))') == False

def test_alternating_valid():
    # Alternating open/close repeated multiple times
    assert is_valid_parenthesization('()()()()') == True

def test_close_in_middle_of_opens():
    # Close paren appears mid-sequence causing early negative depth
    assert is_valid_parenthesization('(())(') == False

def test_all_opens():
    # All opens, no closes: depth never goes negative but not zero at end
    assert is_valid_parenthesization('((((') == False

def test_all_closes():
    # All closes: depth goes negative immediately
    assert is_valid_parenthesization('))))') == False

def test_valid_complex():
    # Complex valid nesting: (()(()))
    assert is_valid_parenthesization('(()(()))') == True

def test_invalid_complex_close_early():
    # Complex invalid: )()( - starts with close
    assert is_valid_parenthesization(')()(') == False

def test_return_type_is_bool_on_valid():
    result = is_valid_parenthesization('()')
    assert isinstance(result, bool)

def test_return_type_is_bool_on_invalid():
    result = is_valid_parenthesization('(')
    assert isinstance(result, bool)

def test_long_valid_string():
    # Long balanced string of pairs
    s = '()' * 1000
    assert is_valid_parenthesization(s) == True

def test_long_invalid_extra_open():
    # Long string with one extra open at the end
    s = '()' * 1000 + '('
    assert is_valid_parenthesization(s) == False

def test_long_invalid_early_close():
    # Long string starting with a close
    s = ')' + '()' * 999
    assert is_valid_parenthesization(s) == False