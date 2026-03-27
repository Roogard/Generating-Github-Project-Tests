from python_programs.is_valid_parenthesization import is_valid_parenthesization

# paren == '(': True → depth incremented
def test_single_open_paren():
    # depth never goes negative, but ends at 1 (unmatched) → should return True based on code
    # Actually a single '(' leaves depth=1, which returns True (no depth<0 encountered)
    # This exercises paren=='(' True path
    result = is_valid_parenthesization('(')
    assert result == True  # code returns True (no negative depth), though semantically invalid

# paren == '(': False, depth < 0: True → returns False
def test_single_close_paren():
    # paren == '(' is False, depth goes to -1, depth < 0 is True → return False
    assert is_valid_parenthesization(')') == False

# paren == '(': True and False, depth < 0: False → full valid string
def test_valid_simple_parens():
    # '()': paren=='(' True then False, depth goes 1 then 0, depth<0 never True
    assert is_valid_parenthesization('()') == True

# paren == '(': True and False multiple times, depth < 0: False → nested valid
def test_valid_nested_parens():
    # '(())': exercises paren=='(' True twice, False twice, depth never < 0
    assert is_valid_parenthesization('(())') == True

# paren == '(': False, depth < 0: True → unmatched close in middle
def test_close_before_open():
    # ')(' : first char ')' → paren=='(' False, depth=-1, depth<0 True → return False
    assert is_valid_parenthesization(')(') == False

# paren == '(': True and False, depth < 0: True → close after balanced
def test_extra_close_at_end():
    # '())': '(' True, ')' False depth=0 not<0, ')' False depth=-1 <0 True → False
    assert is_valid_parenthesization('())') == False

# empty string: loop never executes, returns True
def test_empty_string():
    # No iterations, no conditions evaluated in loop → returns True
    assert is_valid_parenthesization('') == True

# paren == '(': True multiple times, depth < 0: False → only opens
def test_all_open_parens():
    # '(((' : paren=='(' True three times, depth never < 0 → True
    assert is_valid_parenthesization('(((') == True

# paren == '(': False multiple times, depth < 0: True on first
def test_all_close_parens():
    # ')))': first ')' → depth=-1 < 0 → False
    assert is_valid_parenthesization(')))') == False

# paren == '(': True and False interleaved, depth < 0: False → multiple valid pairs
def test_multiple_valid_pairs():
    # '()()()': alternating, depth cycles 0→1→0→1→0→1→0, never < 0
    assert is_valid_parenthesization('()()()') == True

# paren == '(': False, depth < 0: False → close brings depth to exactly 0
def test_depth_reaches_zero_on_close():
    # '()(': after '()' depth=0, then '(' depth=1; last ')' brings it to 0, no negative
    assert is_valid_parenthesization('()()') == True

# depth < 0: True triggered after some valid pairs
def test_close_after_balanced_pairs():
    # '())'  → depth: 0→1→0→-1 → False
    assert is_valid_parenthesization('())') == False