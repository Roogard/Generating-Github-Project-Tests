from python_programs.is_valid_parenthesization import is_valid_parenthesization

# catches: missing final return (would return None), wrong final depth check (depth<=0 vs <0), wrong paren comparison inversion
def test_valid_simple_pair():
    assert is_valid_parenthesization("()") is True

# catches: off-by-one in depth updates (e.g., depth +=2 or depth -=2), wrong initial value of depth
def test_valid_nested():
    assert is_valid_parenthesization("(()())") is True

# catches: flipped comparison (if depth<0 mutated to if depth>0), paren comparison inverted (using !=), missing early False return
def test_unmatched_closing_prefix():
    assert is_valid_parenthesization(")(") is False

# catches: missing handling of a lone closing (depth check omitted), or comparison mutated to <=0 causing wrong branch
def test_unmatched_single_closing():
    assert is_valid_parenthesization(")") is False

# catches: missing final depth==0 check (would incorrectly return True for unmatched opens)
def test_unmatched_single_opening():
    assert is_valid_parenthesization("(") is False

# catches: missing final depth==0 check on longer string of unmatched opens
def test_unmatched_trailing_opening():
    assert is_valid_parenthesization("(()") is False