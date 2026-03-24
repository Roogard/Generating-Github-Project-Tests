from python_programs.is_valid_parenthesization import is_valid_parenthesization

# covers: depth initialization, skip loop, return True
def test_empty_string():
    assert is_valid_parenthesization("") is True

# covers: '(': depth += 1; ')': depth -= 1 with depth >= 0, return True at end
def test_balanced_parentheses():
    assert is_valid_parenthesization("()()") is True

# covers: ')': depth -= 1 leading to depth < 0, early return False
def test_unbalanced_leading_closing():
    assert is_valid_parenthesization(")") is False