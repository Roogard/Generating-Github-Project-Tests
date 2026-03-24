from correct_python_programs.is_valid_parenthesization import is_valid_parenthesization

# Block mapping:
# block 1: function entry, initialization (depth = 0)
# block 2: loop entry (for paren in parens:)
# block 3: if paren == '(': (true branch)
# block 4: else: (paren != '(')
# block 5: inside else: depth -= 1; if depth < 0: (true branch)
# block 6: inside else: after if depth < 0 (false branch), loop continues
# block 7: loop exit (after for), return depth == 0

# covers: block 1, block 2 (enters loop), block 3, block 6, block 7 (depth == 0)
def test_valid_simple():
    assert is_valid_parenthesization("()") == True

# covers: block 1, block 2 (enters loop), block 3, block 6, block 7 (depth != 0)
def test_invalid_open_only():
    assert is_valid_parenthesization("(") == False

# covers: block 1, block 2 (enters loop), block 4, block 5 (depth < 0)
def test_invalid_close_first():
    assert is_valid_parenthesization(")") == False

# covers: block 1, block 2 (enters loop), block 4, block 5 (depth < 0) with longer sequence
def test_invalid_early_close():
    assert is_valid_parenthesization("())") == False

# covers: block 1, block 2 (enters loop), block 3, block 6, block 7 (depth == 0) with nested
def test_valid_nested():
    assert is_valid_parenthesization("(())") == True

# covers: block 1, block 2 (enters loop), block 3, block 6, block 7 (depth == 0) with sequence
def test_valid_sequence():
    assert is_valid_parenthesization("()()") == True

# covers: block 1, block 2 (does not enter loop), block 7 (depth == 0)
def test_empty_string():
    assert is_valid_parenthesization("") == True