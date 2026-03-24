from python_programs.is_valid_parenthesization import is_valid_parenthesization

# path: loop 0 iterations → return True
def test_empty():
    assert is_valid_parenthesization("") == True

# path: loop 1 iteration → paren == '(' → finish loop → return True
def test_single_open():
    assert is_valid_parenthesization("(") == True

# path: loop 1 iteration → paren != '(' → depth < 0 → return False
def test_single_close():
    assert is_valid_parenthesization(")") == False

# path: loop >1 iterations → all '(' branches → finish loop → return True
def test_multiple_opens():
    assert is_valid_parenthesization("(((") == True

# path: loop >1 iterations → '(' then ')' with no negative → finish loop → return True
def test_simple_balanced():
    assert is_valid_parenthesization("()") == True

# path: loop >1 iterations → invalid negative on last iteration → return False
def test_late_invalid():
    assert is_valid_parenthesization("())") == False