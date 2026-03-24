from correct_python_programs.is_valid_parenthesization import is_valid_parenthesization

# covers: initialization, loop entry, paren == '(' (True), depth += 1, loop continuation, loop exit, return depth == 0 (True)
def test_valid_simple():
    assert is_valid_parenthesization('(())') == True

# covers: initialization, loop entry, paren == '(' (False), depth -= 1, depth < 0 (True), return False
def test_invalid_closing_first():
    assert is_valid_parenthesization(')(') == False

# covers: initialization, loop entry, paren == '(' (False), depth -= 1, depth < 0 (False), loop continuation, loop exit, return depth == 0 (False)
def test_invalid_unclosed():
    assert is_valid_parenthesization('(()') == False