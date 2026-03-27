from python_programs.is_valid_parenthesization import is_valid_parenthesization

# Block mapping:
# Block 1: function entry, depth = 0
# Block 2: for loop iteration (paren in parens)
# Block 3: if paren == '(' -> depth += 1
# Block 4: else -> depth -= 1
# Block 5: if depth < 0 -> return False
# Block 6: return True (after loop)

# covers: block 1, block 2, block 3, block 4, block 6 (valid balanced parens)
def test_valid_balanced():
    assert is_valid_parenthesization('()') == True

# covers: block 1, block 6 (empty string, loop body never entered)
def test_empty_string():
    assert is_valid_parenthesization('') == True

# covers: block 1, block 2, block 3, block 6 (only open parens - depth never goes negative)
# Note: '(((' has depth 3 at end, returns True per the function logic
def test_only_open_parens():
    assert is_valid_parenthesization('(((') == True

# covers: block 1, block 2, block 4, block 5 (returns False immediately)
def test_close_before_open():
    assert is_valid_parenthesization(')(') == False

# covers: block 1, block 2, block 4, block 5 (single closing paren)
def test_single_close():
    assert is_valid_parenthesization(')') == False

# covers: block 1, block 2, block 3, block 4, block 6 (nested valid)
def test_nested_valid():
    assert is_valid_parenthesization('(())') == True

# covers: block 1, block 2, block 3, block 4, block 5 (depth goes negative mid-way)
def test_invalid_mid():
    assert is_valid_parenthesization('())(()') == False

# covers: block 1, block 2, block 3, block 4, block 6 (multiple valid pairs)
def test_multiple_pairs():
    assert is_valid_parenthesization('()()()') == True

# covers: block 1, block 2, block 3, block 4, block 6 (deeply nested)
def test_deeply_nested():
    assert is_valid_parenthesization('(((())))') == True

# covers: block 4 and block 5 triggered at last character
def test_extra_close_at_end():
    assert is_valid_parenthesization('())') == False