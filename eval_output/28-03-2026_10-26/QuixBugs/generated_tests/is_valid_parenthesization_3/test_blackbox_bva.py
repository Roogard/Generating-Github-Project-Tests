from python_programs.is_valid_parenthesization import is_valid_parenthesization

def test_empty_string():
    # A correct parenthesization validator SHOULD return True for an empty string (no unmatched parens)
    result = is_valid_parenthesization("")
    assert result == True

def test_single_open_paren():
    # A correct validator SHOULD return False for a single unmatched '('
    result = is_valid_parenthesization("(")
    assert result == False

def test_single_close_paren():
    # A correct validator SHOULD return False for a single unmatched ')'
    result = is_valid_parenthesization(")")
    assert result == False

def test_single_matched_pair():
    # A correct validator SHOULD return True for "()"
    result = is_valid_parenthesization("()")
    assert result == True

def test_two_open_parens():
    # A correct validator SHOULD return False for "((" — depth never returns to 0
    result = is_valid_parenthesization("((")
    assert result == False

def test_two_close_parens():
    # A correct validator SHOULD return False for "))" — immediate depth < 0
    result = is_valid_parenthesization("))")
    assert result == False

def test_close_before_open():
    # A correct validator SHOULD return False for ")(" — close before open
    result = is_valid_parenthesization(")(")
    assert result == False

def test_open_before_close():
    # A correct validator SHOULD return True for "()" — standard valid pair
    result = is_valid_parenthesization("()")
    assert result == True

def test_nested_valid():
    # A correct validator SHOULD return True for "(())"
    result = is_valid_parenthesization("(())")
    assert result == True

def test_nested_invalid_extra_open():
    # A correct validator SHOULD return False for "(()" — one unmatched open remains
    result = is_valid_parenthesization("(()")
    assert result == False

def test_nested_invalid_extra_close():
    # A correct validator SHOULD return False for "())" — one extra close
    result = is_valid_parenthesization("())")
    assert result == False

def test_long_valid_sequence():
    # A correct validator SHOULD return True for a perfectly balanced long sequence
    result = is_valid_parenthesization("()()()()()")
    assert result == True

def test_long_invalid_extra_open():
    # A correct validator SHOULD return False when there are more opens than closes
    result = is_valid_parenthesization("()()()()()(")
    assert result == False

def test_long_invalid_extra_close():
    # A correct validator SHOULD return False when there are more closes than opens
    result = is_valid_parenthesization("()()()()())")
    assert result == False

def test_deeply_nested_valid():
    # A correct validator SHOULD return True for deeply nested matching parens
    result = is_valid_parenthesization("((((((()))))))")
    assert result == True

def test_deeply_nested_one_extra_open():
    # A correct validator SHOULD return False — depth is 1 at end, not 0
    result = is_valid_parenthesization("((((((("))
    assert result == False

def test_interleaved_valid():
    # A correct validator SHOULD return True for "(()())"
    result = is_valid_parenthesization("(()())")
    assert result == True

def test_interleaved_invalid():
    # A correct validator SHOULD return False for "(()()" — one open unmatched
    result = is_valid_parenthesization("(()()")
    assert result == False

def test_close_at_end_after_balanced():
    # A correct validator SHOULD return False for "()(" — extra open at the end
    result = is_valid_parenthesization("()(")
    assert result == False

def test_return_type_is_bool_valid():
    result = is_valid_parenthesization("()")
    assert isinstance(result, bool)

def test_return_type_is_bool_invalid():
    result = is_valid_parenthesization(")(")
    assert isinstance(result, bool)