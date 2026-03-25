from python_programs.is_valid_parenthesization import is_valid_parenthesization

# covers: initialization depth=0, immediate return True on empty input
def test_empty_parenthesization():
    assert is_valid_parenthesization("") is True

# covers: '(' branch (depth += 1), ')' branch (depth -= 1), depth never negative, final return True
def test_simple_balanced_parenthesization():
    assert is_valid_parenthesization("()") is True

# covers: ')' branch (depth -= 1), depth becomes negative, early return False
def test_unbalanced_negative_depth():
    assert is_valid_parenthesization(")") is False