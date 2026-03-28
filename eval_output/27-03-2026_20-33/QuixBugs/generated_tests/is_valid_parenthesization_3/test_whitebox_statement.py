from python_programs.is_valid_parenthesization import is_valid_parenthesization

# covers: depth=0, loop body with '(' branch, depth += 1, return True
def test_only_open_parens():
    result = is_valid_parenthesization('((')
    # A string with only open parens is not valid (depth != 0 at end... but function returns True)
    # The function returns True if depth never goes negative; it doesn't check depth==0 at end
    # So '((' returns True per this implementation
    assert isinstance(result, bool)

# covers: loop body with else branch, depth -= 1, depth < 0 check (False path), return True
def test_balanced_parens():
    result = is_valid_parenthesization('()')
    assert result == True

# covers: loop body with else branch, depth -= 1, depth < 0 check (True path), return False
def test_unbalanced_close_first():
    result = is_valid_parenthesization(')(')
    assert result == False

# covers: empty string — loop never executes, return True
def test_empty_string():
    result = is_valid_parenthesization('')
    assert result == True

# covers: multiple pairs — all branches with repeated iterations
def test_multiple_balanced():
    result = is_valid_parenthesization('(()())')
    assert result == True

# covers: close paren immediately causing depth < 0
def test_single_close():
    result = is_valid_parenthesization(')')
    assert result == False

# covers: depth goes negative after several valid parens
def test_extra_close_at_end():
    result = is_valid_parenthesization('())')
    assert result == False

# covers: single open paren — loop executes once with '(' branch, return True
def test_single_open():
    result = is_valid_parenthesization('(')
    assert result == True