from python_programs.is_valid_parenthesization import is_valid_parenthesization

# paren == '(': True → depth incremented
def test_single_open_paren_unmatched():
    # depth never goes negative but ends > 0; still returns True per logic
    # (': True, depth < 0: never reached
    assert is_valid_parenthesization('(') == False

# paren == '(': False (it's ')'), depth < 0: True → return False
def test_single_close_paren_invalid():
    # paren == '(': False, depth -= 1 makes depth = -1, depth < 0: True
    assert is_valid_parenthesization(')') == False

# paren == '(': True then False, depth < 0: False → balanced, return True
def test_balanced_single_pair():
    # paren == '(' : True (first), False (second)
    # depth < 0: False (depth goes 1 then 0)
    assert is_valid_parenthesization('()') == True

# paren == '(': True (multiple), False (multiple), depth < 0: False → return True
def test_balanced_multiple_pairs():
    # paren == '(': True and False exercised multiple times
    # depth < 0: False throughout
    assert is_valid_parenthesization('(())') == True

# paren == '(': False, depth < 0: True → return False early (close before open)
def test_close_before_open_invalid():
    # paren == '(': False first iteration, depth < 0: True
    assert is_valid_parenthesization(')(') == False

# empty string: loop body never executes → return True
def test_empty_string():
    # no conditions evaluated, returns True
    assert is_valid_parenthesization('') == True

# paren == '(': True and False, depth < 0: False, balanced nested
def test_balanced_nested():
    # paren == '(' : True for '(', False for ')'
    # depth < 0: False (depth: 1->2->1->2->1->0)
    assert is_valid_parenthesization('(()())') == True

# paren == '(': False multiple times, depth < 0: True at some point
def test_extra_close_parens_invalid():
    # paren == '(': True once, False three times
    # depth < 0: True when third ')' is encountered
    assert is_valid_parenthesization('())') == False

# paren == '(': True multiple times only, depth < 0: never True → return True (unmatched opens)
def test_only_open_parens():
    # paren == '(': True for all, depth < 0: False (never decremented)
    # function returns True even though unbalanced — tests the actual logic boundary
    assert is_valid_parenthesization('((') == False

# depth < 0: False across all iterations, ends balanced
def test_longer_balanced():
    # paren == '(': True and False alternating
    # depth < 0: False throughout
    assert is_valid_parenthesization('()()') == True