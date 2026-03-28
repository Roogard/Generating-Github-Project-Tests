from python_programs.is_valid_parenthesization import is_valid_parenthesization

# catches: missing final "depth == 0" check — unmatched '(' should return False
def test_unmatched_open_paren_single():
    assert is_valid_parenthesization("(") == False

# catches: missing final "depth == 0" check — multiple unmatched '(' should return False
def test_unmatched_open_paren_multiple():
    assert is_valid_parenthesization("(()") == False

# catches: missing final "depth == 0" check — all opens, no closes
def test_all_open_parens():
    assert is_valid_parenthesization("((((") == False

# catches: "depth < 0" mutated to "depth <= 0" — valid string rejected
def test_single_valid_pair():
    assert is_valid_parenthesization("()") == True

# catches: "depth < 0" mutated to "depth > 0" — close before open not caught
def test_close_before_open():
    assert is_valid_parenthesization(")(") == False

# catches: "depth -= 1" mutated to "depth += 1" — unmatched close not detected
def test_unmatched_close_paren():
    assert is_valid_parenthesization(")") == False

# catches: "depth += 1" mutated to "depth -= 1" — valid deep nesting rejected
def test_nested_valid():
    assert is_valid_parenthesization("((()))") == True

# catches: "depth += 1" mutated to "depth = 1" — repeated opens not counted correctly
def test_multiple_valid_pairs():
    assert is_valid_parenthesization("()()()") == True

# catches: "return False" mutated to "return True" inside negative-depth branch
def test_close_only():
    assert is_valid_parenthesization(")()") == False

# catches: final return True mutated to return False — genuinely valid string rejected
def test_empty_string():
    assert is_valid_parenthesization("") == True

# catches: missing final depth == 0 check — two extra opens at end
def test_two_extra_opens():
    assert is_valid_parenthesization("()((") == False

# catches: off-by-one in depth < 0 vs depth <= 0 — depth hits exactly 0 then closes
def test_depth_returns_to_zero_then_closes():
    assert is_valid_parenthesization("())") == False

# catches: condition paren == '(' mutated to paren != '(' — open treated as close
def test_only_opens():
    assert is_valid_parenthesization("(((") == False

# catches: depth reset or wrong variable — interleaved valid pairs
def test_interleaved_valid():
    assert is_valid_parenthesization("(())()") == True

# catches: final check missing — one open never closed in complex expression
def test_complex_unbalanced():
    assert is_valid_parenthesization("(()(()") == False

# catches: final check missing — valid deeply nested then extra open
def test_deep_then_extra_open():
    assert is_valid_parenthesization("((()))(" ) == False