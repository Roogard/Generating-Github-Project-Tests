from python_programs.is_valid_parenthesization import is_valid_parenthesization

# covers: block 1, block 5 (empty input, no loop iterations)
def test_empty_string():
    assert is_valid_parenthesization("") is True

# covers: block 1, block 2, block 5 (only '(' increments depth, final return True)
def test_only_open_parens():
    assert is_valid_parenthesization("(((") is True

# covers: block 1, block 2, block 3, block 5 (mixed '(' and ')' without negative depth)
def test_balanced_parens():
    assert is_valid_parenthesization("()()") is True

# covers: block 1, block 3, block 4 (first ')' causes depth<0 and returns False)
def test_unbalanced_negative_depth():
    assert is_valid_parenthesization(")(") is False