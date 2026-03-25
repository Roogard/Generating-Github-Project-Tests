from python_programs.is_valid_parenthesization import is_valid_parenthesization

def test_empty_string_is_valid():
    assert is_valid_parenthesization("") is True

def test_single_open_parenthesis_is_invalid():
    assert is_valid_parenthesization("(") is False

def test_single_close_parenthesis_is_invalid():
    assert is_valid_parenthesization(")") is False

def test_simple_pair_is_valid():
    assert is_valid_parenthesization("()") is True

def test_unbalanced_starting_with_close_is_invalid():
    assert is_valid_parenthesization(")(()") is False

def test_unbalanced_trailing_open_is_invalid():
    assert is_valid_parenthesization("(()") is False

def test_nested_parentheses_are_valid():
    assert is_valid_parenthesization("((()()))") is True

def test_multiple_pairs_are_valid():
    assert is_valid_parenthesization("()()()") is True

def test_partial_balance_with_extra_close_is_invalid():
    assert is_valid_parenthesization("()(())())") is False

def test_partial_balance_with_extra_open_is_invalid():
    assert is_valid_parenthesization("((()()") is False