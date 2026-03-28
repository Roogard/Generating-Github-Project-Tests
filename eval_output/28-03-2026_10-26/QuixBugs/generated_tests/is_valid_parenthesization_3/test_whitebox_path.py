from python_programs.is_valid_parenthesization import is_valid_parenthesization

# path: loop 0 iterations → return True
def test_empty_string():
    # A correct validator should return True for empty string (vacuously valid)
    result = is_valid_parenthesization("")
    assert result == True

# path: loop 1 iter → paren == '(' → depth becomes 1 → return True (but depth != 0, so correct impl should return False)
def test_single_open_paren():
    # A correct validator must return False for unmatched '('
    result = is_valid_parenthesization("(")
    assert result == False

# path: loop 1 iter → paren != '(' → depth becomes -1 → depth < 0 → return False
def test_single_close_paren():
    # A correct validator must return False for unmatched ')'
    result = is_valid_parenthesization(")")
    assert result == False

# path: loop 2 iters → open then close → depth goes 1 then 0 → no depth<0 → return True
def test_matched_pair():
    # A correct validator should return True for "()"
    result = is_valid_parenthesization("()")
    assert result == True

# path: loop 2 iters → close then open → depth goes -1 → depth < 0 → return False
def test_close_before_open():
    # A correct validator must return False for ")(" (closes before opens)
    result = is_valid_parenthesization(")(")
    assert result == False

# path: loop many iters → all opens → depth never < 0 → return True (but unmatched, correct impl returns False)
def test_multiple_open_parens_only():
    # A correct validator must return False for "(((" (unmatched opens)
    result = is_valid_parenthesization("(((")
    assert result == False

# path: loop many iters → first close causes depth < 0 immediately → return False
def test_multiple_close_parens_only():
    # A correct validator must return False for ")))"
    result = is_valid_parenthesization(")))")
    assert result == False

# path: loop many iters → mixed, depth goes negative mid-way → return False
def test_interleaved_invalid():
    # A correct validator must return False for "())("
    result = is_valid_parenthesization("())(")
    assert result == False

# path: loop many iters → balanced nested → depth never < 0 → return True
def test_nested_balanced():
    # A correct validator should return True for "(())"
    result = is_valid_parenthesization("(())")
    assert result == True

# path: loop many iters → multiple balanced pairs → depth never < 0 → return True
def test_multiple_balanced_pairs():
    # A correct validator should return True for "()()()"
    result = is_valid_parenthesization("()()()")
    assert result == True

# path: loop many iters → opens exceed closes but depth never negative → correct impl returns False
def test_more_opens_than_closes():
    # A correct validator must return False for "(()(" (unmatched opens remain)
    result = is_valid_parenthesization("(()(")
    assert result == False

# path: loop many iters → closes exceed opens, depth goes negative → return False
def test_more_closes_than_opens():
    # A correct validator must return False for "())"
    result = is_valid_parenthesization("())")
    assert result == False

# path: loop many iters → complex balanced → depth returns to 0 → return True
def test_complex_balanced():
    # A correct validator should return True for "((())())"
    # Use a clearly correct input instead
    result = is_valid_parenthesization("((())())")
    assert result == True