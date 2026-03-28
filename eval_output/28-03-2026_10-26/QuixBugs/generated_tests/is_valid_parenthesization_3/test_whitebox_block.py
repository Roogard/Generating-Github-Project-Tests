from python_programs.is_valid_parenthesization import is_valid_parenthesization

# Blocks:
# Block 1: function entry, depth = 0
# Block 2: for loop entry/iteration
# Block 3: paren == '(' branch -> depth += 1
# Block 4: else branch -> depth -= 1
# Block 5: depth < 0 -> return False
# Block 6: loop exit -> return True (depth >= 0 throughout)

# covers: block 1, block 2 (empty loop), block 6
def test_empty_string():
    # A correct validator should accept empty string (no unmatched parens)
    result = is_valid_parenthesization('')
    assert result == True

# covers: block 1, block 2, block 3, block 6 (balanced parens)
def test_balanced_simple():
    # A correct validator should return True for "()"
    result = is_valid_parenthesization('()')
    assert result == True
    assert isinstance(result, bool)

# covers: block 1, block 2, block 3, block 4, block 5 (depth goes negative)
def test_closes_before_opens():
    # A correct validator must return False when ')' appears before matching '('
    result = is_valid_parenthesization(')(')
    assert result == False

# covers: block 1, block 2, block 3, block 4, block 5 (immediate negative depth)
def test_only_close():
    # A correct validator must return False for a lone ')'
    result = is_valid_parenthesization(')')
    assert result == False

# covers: block 1, block 2, block 3, block 6 (only opens, depth > 0 at end)
def test_unclosed_open():
    # A correct validator should return False for unmatched '('
    # NOTE: This tests the expected correct behavior — unclosed parens are invalid
    result = is_valid_parenthesization('(')
    assert result == False

# covers: block 1, block 2, block 3, block 4, block 6 (nested balanced)
def test_nested_balanced():
    # A correct validator should return True for properly nested parens
    result = is_valid_parenthesization('((()))')
    assert result == True
    assert isinstance(result, bool)

# covers: block 1, block 2, block 3, block 4, block 6 (multiple balanced pairs)
def test_multiple_pairs():
    # A correct validator should return True for multiple sequential balanced pairs
    result = is_valid_parenthesization('()()()')
    assert result == True

# covers: block 4, block 5 (depth goes negative after some valid opens)
def test_extra_close_after_balanced():
    # A correct validator must return False when there are more ')' than '('
    result = is_valid_parenthesization('())')
    assert result == False

# covers: block 3 and block 4 paths, block 6 (complex balanced)
def test_complex_balanced():
    # A correct validator should return True for a complex valid parenthesization
    result = is_valid_parenthesization('(()())')
    assert result == True
    assert isinstance(result, bool)

# covers: block 2 single iteration open, block 3, then close triggers block 4 and depth check
def test_two_char_balanced():
    result = is_valid_parenthesization('()')
    assert result == True

def test_two_char_unbalanced_reversed():
    result = is_valid_parenthesization(')(')
    assert result == False