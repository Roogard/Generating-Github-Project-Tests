from python_programs.is_valid_parenthesization import is_valid_parenthesization

# Condition 1: paren == '(' → True; depth < 0 never reached
def test_single_open_paren_is_invalid():
    # A correct validator must return False: one unmatched '(' means depth != 0 at end
    # paren == '(': True for the only character; depth < 0: never triggered
    result = is_valid_parenthesization('(')
    assert result == False

# Condition 1: paren == '(' → False (it is ')'); depth < 0: True → return False immediately
def test_single_close_paren_is_invalid():
    # A correct validator must return False: ')' with nothing to match causes depth < 0
    # paren == '(': False; depth < 0: True
    result = is_valid_parenthesization(')')
    assert result == False

# Condition 1: paren == '(' → True then False; depth < 0: False throughout → return True
def test_matched_pair_is_valid():
    # A correct validator must return True for a perfectly matched pair "()"
    # paren == '(': True (first char), False (second char); depth < 0: False
    result = is_valid_parenthesization('()')
    assert result == True

# Condition 1: paren == '(' → True and False multiple times; depth < 0: False → return True
def test_fully_matched_parens_is_valid():
    # A correct validator must return True for "(()())"
    # paren == '(': True (chars 0,2,4), False (chars 1,3,5); depth < 0: False
    result = is_valid_parenthesization('(()())')
    assert result == True

# Condition 1: paren == '(' → True and False; depth < 0: True in middle → return False
def test_close_before_open_is_invalid():
    # A correct validator must return False for ")(" — closing before opening
    # paren == '(': False (first char), True (second char); depth < 0: True after first char
    result = is_valid_parenthesization(')(')
    assert result == False

# Condition 1: paren == '(' → True multiple times only; depth < 0: False → return True is WRONG
def test_extra_open_parens_is_invalid():
    # A correct validator must return False for "(()" — unmatched open paren remains
    # paren == '(': True (chars 0,1), False (char 2); depth < 0: False; but depth != 0 at end
    result = is_valid_parenthesization('(()')
    assert result == False

# Condition 1: paren == '(' → False multiple times; depth < 0: True → return False
def test_extra_close_parens_is_invalid():
    # A correct validator must return False for "())" — too many closing parens
    # paren == '(': True (char 0), False (chars 1,2); depth < 0: True on third char
    result = is_valid_parenthesization('())')
    assert result == False

# Condition 1: paren == '(' → never evaluated (empty string); depth < 0: never triggered
def test_empty_string_is_valid():
    # A correct validator must return True for an empty string — no mismatches possible
    result = is_valid_parenthesization('')
    assert result == True

# Condition 1: paren == '(' → True and False; depth < 0: False → return True
def test_nested_parens_is_valid():
    # A correct validator must return True for "((()))"
    # paren == '(': True (chars 0,1,2), False (chars 3,4,5); depth < 0: False
    result = is_valid_parenthesization('((()))')
    assert result == True

# Condition 1: paren == '(' → True and False; depth < 0: True → return False
def test_interleaved_invalid():
    # A correct validator must return False for "())(" — closes too early
    # paren == '(': True (chars 0,3), False (chars 1,2); depth < 0: True at char 2
    result = is_valid_parenthesization('()(')
    assert result == False

# Property: result must always be a boolean
def test_returns_boolean_for_valid():
    result = is_valid_parenthesization('()')
    assert isinstance(result, bool)

def test_returns_boolean_for_invalid():
    result = is_valid_parenthesization(')')
    assert isinstance(result, bool)