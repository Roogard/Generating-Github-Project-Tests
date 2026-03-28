from python_programs.is_valid_parenthesization import is_valid_parenthesization

# catches: missing final depth == 0 check (unbalanced but never negative)
def test_unmatched_open_parens():
    assert is_valid_parenthesization("(") == False

# catches: missing final depth == 0 check (multiple unclosed opens)
def test_multiple_unclosed_opens():
    assert is_valid_parenthesization("(((") == False

# catches: missing final depth == 0 check (opens and closes but not balanced)
def test_more_opens_than_closes():
    assert is_valid_parenthesization("(()") == False

# catches: "depth < 0" mutated to "depth <= 0" (off-by-one in early return)
def test_single_valid_pair():
    assert is_valid_parenthesization("()") == True

# catches: "depth -= 1" mutated to "depth += 1" (wrong operator on close paren)
def test_close_before_open_is_invalid():
    assert is_valid_parenthesization(")(") == False

# catches: "depth < 0" mutated to "depth > 0" (negated condition)
def test_immediate_close_is_invalid():
    assert is_valid_parenthesization(")") == False

# catches: "depth += 1" mutated to "depth -= 1" (wrong operator on open paren)
def test_nested_valid():
    assert is_valid_parenthesization("(())") == True

# catches: early return True instead of continuing loop
def test_valid_sequence_multiple_pairs():
    assert is_valid_parenthesization("()()") == True

# catches: missing final depth == 0 check (depth goes up and never comes back)
def test_opens_then_closes_unbalanced():
    assert is_valid_parenthesization("(()((") == False

# catches: return False mutated to return True (wrong return value in early exit)
def test_invalid_interleaved():
    assert is_valid_parenthesization(")()(") == False

# catches: depth initialized to wrong value (e.g., depth = 1)
def test_empty_string_is_valid():
    assert is_valid_parenthesization("") == True

# catches: final check off-by-one (depth == 0 vs depth <= 0)
def test_perfectly_balanced_complex():
    assert is_valid_parenthesization("((()))") == True

# catches: loop not processing all characters (e.g., off-by-one in iteration)
def test_last_char_causes_invalidity():
    assert is_valid_parenthesization("()(") == False

# catches: paren == '(' mutated to paren != '(' (wrong branch taken)
def test_only_close_parens():
    assert is_valid_parenthesization(")))") == False

# catches: missing final depth == 0 check with exact depth at end
def test_two_opens_one_close():
    assert is_valid_parenthesization("()(()") == False