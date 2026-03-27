from python_programs.is_valid_parenthesization import is_valid_parenthesization

# path: loop 0 iterations → return True
def test_empty_string():
    assert is_valid_parenthesization('') == True

# path: loop 1 iter → paren == '(' → depth becomes 1 → return True (depth > 0 at end, but no False)
def test_single_open_paren():
    # unmatched open paren: depth never goes negative, but not truly balanced
    # function only checks depth never goes negative, so returns True
    assert is_valid_parenthesization('(') == True

# path: loop 1 iter → paren != '(' → depth becomes -1 → depth < 0 → return False
def test_single_close_paren():
    assert is_valid_parenthesization(')') == False

# path: loop 2 iters → first '(' increases depth → second ')' decreases depth → depth >= 0 throughout → return True
def test_single_matched_pair():
    assert is_valid_parenthesization('()') == True

# path: loop 2 iters → first ')' → depth < 0 → return False (early exit)
def test_close_before_open():
    assert is_valid_parenthesization(')(') == False

# path: loop many iters → all '(' → depth always positive → return True
def test_all_open_parens():
    assert is_valid_parenthesization('(((') == True

# path: loop many iters → mix leading to depth < 0 mid-way → return False
def test_close_exceeds_open_midway():
    assert is_valid_parenthesization('(()))') == False

# path: loop many iters → balanced multiple pairs → depth never negative → return True
def test_multiple_matched_pairs():
    assert is_valid_parenthesization('(())()') == True

# path: loop many iters → nested valid parens → return True
def test_deeply_nested_valid():
    assert is_valid_parenthesization('((()))') == True

# path: loop many iters → depth goes negative at last character → return False
def test_extra_close_at_end():
    assert is_valid_parenthesization('())') == False

# path: loop many iters → interleaved parens, valid balanced → return True
def test_interleaved_valid():
    assert is_valid_parenthesization('()(())') == True

# path: loop many iters → depth goes negative early then would recover → return False (early exit)
def test_negative_depth_then_recovery_attempt():
    assert is_valid_parenthesization(')(()') == False