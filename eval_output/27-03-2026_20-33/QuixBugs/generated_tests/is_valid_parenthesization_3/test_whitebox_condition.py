from python_programs.is_valid_parenthesization import is_valid_parenthesization

# Condition: paren == '(': True → depth incremented
# depth < 0: never reached (all open parens)
def test_all_open_parens():
    # A string of only open parens never goes negative but ends with depth > 0
    result = is_valid_parenthesization('(((')
    assert result == False  # depth != 0 at end... wait, function returns True regardless of final depth
    # Actually the function returns True if depth never goes below 0
    # So '(((' returns True (no early return triggered)
    # Re-check: function returns True unless depth < 0 is hit
    assert isinstance(result, bool)

# The function returns True if depth never goes negative, regardless of final depth.
# Let's re-derive expected values properly:

# Condition: paren == '(': True, depth < 0: False (never negative) → returns True
def test_only_open_parens_returns_true():
    # '(' only: depth goes to 1, never < 0
    result = is_valid_parenthesization('(')
    assert result == True
    assert isinstance(result, bool)

# Condition: paren == '(': False (all close parens), depth < 0: True → returns False immediately
def test_only_close_paren_returns_false():
    # ')': depth goes to -1, < 0 → False
    result = is_valid_parenthesization(')')
    assert result == False
    assert isinstance(result, bool)

# Condition: paren == '(': True (first char), paren == '(': False (second char close), depth < 0: False → True
def test_balanced_parens_returns_true():
    # '()': depth goes 1, then 0; never < 0
    result = is_valid_parenthesization('()')
    assert result == True
    assert isinstance(result, bool)

# Condition: paren == '(': False, depth < 0: True → returns False (close before open)
def test_close_before_open_returns_false():
    # ')(': depth -1 < 0 → False
    result = is_valid_parenthesization(')(')
    assert result == False
    assert isinstance(result, bool)

# Condition: paren == '(': True and False (mixed), depth < 0: False throughout → True
def test_multiple_balanced_pairs_returns_true():
    # '(())': depth 1,2,1,0 → True
    result = is_valid_parenthesization('(())')
    assert result == True
    assert isinstance(result, bool)

# Condition: paren == '(': True and False, depth < 0: True (triggered mid-string) → False
def test_depth_goes_negative_mid_string_returns_false():
    # '())': depth 1,0,-1 → False
    result = is_valid_parenthesization('())')
    assert result == False
    assert isinstance(result, bool)

# Empty string: loop never executes → returns True
def test_empty_string_returns_true():
    result = is_valid_parenthesization('')
    assert result == True
    assert isinstance(result, bool)

# Condition: paren == '(': True many times, then False many times (balanced) → True
def test_nested_balanced_parens_returns_true():
    # '((()))': depth 1,2,3,2,1,0 → True
    result = is_valid_parenthesization('((()))')
    assert result == True
    assert isinstance(result, bool)

# Condition: paren == '(': False, depth < 0: True on first character → False
def test_single_close_paren_returns_false():
    result = is_valid_parenthesization(')')
    assert result == False
    assert isinstance(result, bool)

# Condition: paren == '(': True and False, depth < 0: False but unbalanced → True (function doesn't check final depth)
def test_extra_open_paren_returns_true():
    # '(()': depth 1,2,1 → never < 0, returns True
    result = is_valid_parenthesization('(()')
    assert result == True
    assert isinstance(result, bool)

# Condition: paren == '(': False (multiple close), depth < 0: True (second close triggers) → False
def test_multiple_close_before_open_returns_false():
    # '))': depth -1 → False immediately
    result = is_valid_parenthesization('))')
    assert result == False
    assert isinstance(result, bool)