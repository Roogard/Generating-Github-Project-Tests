from correct_python_programs.is_valid_parenthesization import is_valid_parenthesization

# condition: paren == '(': True
def test_paren_open():
    # paren == '(': True
    assert is_valid_parenthesization("(") == False

# condition: paren == '(': False
def test_paren_close():
    # paren == '(': False
    assert is_valid_parenthesization(")") == False

# condition: depth < 0: True
def test_depth_negative_true():
    # paren == '(': False, depth < 0: True
    assert is_valid_parenthesization("))") == False

# condition: depth < 0: False, depth == 0: True
def test_valid_simple():
    # paren == '(': True (first), paren == '(': False (second), depth < 0: False, depth == 0: True
    assert is_valid_parenthesization("()") == True

# condition: depth < 0: False, depth == 0: False
def test_invalid_unclosed():
    # paren == '(': True (first), paren == '(': False (second), depth < 0: False, depth == 0: False
    assert is_valid_parenthesization("((") == False

# condition: depth < 0: False (throughout), depth == 0: True (complex case)
def test_valid_nested():
    # paren == '(': True and False mixed, depth < 0: False always, depth == 0: True
    assert is_valid_parenthesization("(()())") == True

# condition: depth < 0: False (initially), depth == 0: False (ends negative)
def test_invalid_extra_close():
    # paren == '(': True (first), paren == '(': False (others), depth < 0: False (until end), depth == 0: False
    assert is_valid_parenthesization("())") == False