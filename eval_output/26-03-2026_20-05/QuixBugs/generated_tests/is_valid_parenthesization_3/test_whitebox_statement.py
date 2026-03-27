from python_programs.is_valid_parenthesization import is_valid_parenthesization

# covers: depth=0, loop with '(' branch, depth+=1, return True
def test_single_open_paren():
    assert is_valid_parenthesization('(') == False

# covers: depth=0, loop with ')' branch, depth-=1, depth<0 => return False
def test_single_close_paren():
    assert is_valid_parenthesization(')') == False

# covers: depth=0, loop with '(' then ')' branches, depth>=0 path, return True
def test_valid_single_pair():
    assert is_valid_parenthesization('()') == True

# covers: multiple '(' increments, then ')' decrements without going negative, return True
def test_valid_nested():
    assert is_valid_parenthesization('(())') == True

# covers: ')' after balanced section causes depth < 0 mid-string => return False
def test_invalid_close_after_balanced():
    assert is_valid_parenthesization('())') == False

# covers: empty string - loop body never executes, return True
def test_empty_string():
    assert is_valid_parenthesization('') == True

# covers: unmatched open parens - depth never < 0, return True (depth != 0 but function returns True)
def test_unmatched_open():
    assert is_valid_parenthesization('(()') == False

# covers: complex valid parenthesization
def test_valid_complex():
    assert is_valid_parenthesization('(()())') == True