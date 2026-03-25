from python_programs.is_valid_parenthesization import is_valid_parenthesization

# covers: block 1, block 6 (no iterations, return True)
def test_empty_string():
    assert is_valid_parenthesization("") is True

# covers: block 1, block 2, block 6 (single open parenthesis)
def test_single_open_paren():
    assert is_valid_parenthesization("(") is True

# covers: block 1, block 3, block 4 (single close parenthesis triggers negative depth)
def test_single_close_paren():
    assert is_valid_parenthesization(")") is False

# covers: block 1, block 2, block 3, block 5, block 6 (balanced simple pair)
def test_simple_pair():
    assert is_valid_parenthesization("()") is True

# covers: block 1, blocks 2, 3, 5, 6 (complex balanced string)
def test_complex_balanced():
    assert is_valid_parenthesization("(()())()") is True