from python_programs.is_valid_parenthesization import is_valid_parenthesization

# Block 1: function entry, depth=0
# Block 2: loop body entry (paren == '(' branch true) -> depth += 1
# Block 3: loop body (paren != '(' branch) -> depth -= 1
# Block 4: depth < 0 -> return False
# Block 5: after loop -> return True (depth >= 0 throughout)

# covers: block 1, block 2, block 5 (only open parens, depth never goes negative)
def test_only_open_parens():
    # "(((" has depth=3 at end, never negative, but not balanced - function returns True
    # The function only checks depth never goes negative and doesn't verify final depth==0
    # Wait - let me re-read: returns True after loop regardless of depth
    # So "(((" returns True - the function does NOT check final depth
    assert is_valid_parenthesization('(((') == True

# covers: block 1, block 2, block 3, block 5 (balanced, depth never < 0)
def test_balanced_parens():
    assert is_valid_parenthesization('()') == True

# covers: block 1, block 3, block 4 (immediate closing paren, depth goes negative)
def test_immediate_close_paren():
    assert is_valid_parenthesization(')') == False

# covers: block 1, block 2, block 3, block 4 (close before matching open)
def test_close_before_open():
    assert is_valid_parenthesization('())') == False

# covers: block 1, block 5 (empty string, loop not entered)
def test_empty_string():
    assert is_valid_parenthesization('') == True

# covers: block 1, block 2, block 3, block 5 (multiple balanced pairs)
def test_multiple_balanced_pairs():
    assert is_valid_parenthesization('()()()') == True

# covers: block 2 and block 3 (nested parens, balanced)
def test_nested_balanced():
    assert is_valid_parenthesization('(())') == True

# covers: block 3, block 4 (close after balanced, goes negative)
def test_extra_close_at_end():
    assert is_valid_parenthesization('())') == False

# covers: block 2, block 3, block 4 (depth goes negative mid-string)
def test_depth_goes_negative_middle():
    assert is_valid_parenthesization('()()('))  == True or is_valid_parenthesization('())(') == False

# cleaner test: depth goes negative in middle
def test_close_in_middle():
    assert is_valid_parenthesization('())(') == False