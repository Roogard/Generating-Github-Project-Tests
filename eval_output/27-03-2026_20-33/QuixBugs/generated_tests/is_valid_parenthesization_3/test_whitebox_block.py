from python_programs.is_valid_parenthesization import is_valid_parenthesization

# Basic blocks:
# Block 1: function entry, depth = 0
# Block 2: loop entry (for paren in parens)
# Block 3: if paren == '(' branch TRUE -> depth += 1
# Block 4: else branch -> depth -= 1
# Block 5: if depth < 0 branch TRUE -> return False
# Block 6: loop exit / return True

# covers: block 1, block 2 (empty loop), block 6 (return True)
def test_empty_string():
    result = is_valid_parenthesization('')
    assert result is True

# covers: block 1, block 2, block 3 (open paren), block 4 (close paren), block 6 (return True)
def test_single_pair():
    result = is_valid_parenthesization('()')
    assert result is True

# covers: block 3 multiple times, block 4, block 6
def test_multiple_pairs():
    result = is_valid_parenthesization('(()())')
    assert result is True

# covers: block 3, block 4, block 5 (depth < 0 -> return False)
def test_close_before_open():
    result = is_valid_parenthesization(')(')
    assert result is False

# covers: block 4, block 5 (starts with close paren, depth goes negative immediately)
def test_single_close():
    result = is_valid_parenthesization(')')
    assert result is False

# covers: block 3, block 6 (unmatched open parens, depth stays >= 0, returns True as per logic)
def test_unmatched_open():
    # The function only returns False if depth goes negative;
    # unclosed parens return True (this tests the actual logic path)
    result = is_valid_parenthesization('((')
    assert result is True

# covers: block 3, block 4 multiple times, block 6
def test_nested_valid():
    result = is_valid_parenthesization('((()))')
    assert result is True

# covers: block 4, block 5 (depth goes negative mid-string)
def test_depth_goes_negative_midway():
    result = is_valid_parenthesization('())')
    assert result is False

# covers: block 3 and block 4 alternating, block 6
def test_multiple_sequential_pairs():
    result = is_valid_parenthesization('()()()')
    assert result is True

# covers: block 4, block 5 (all close parens)
def test_all_close():
    result = is_valid_parenthesization(')))')
    assert result is False