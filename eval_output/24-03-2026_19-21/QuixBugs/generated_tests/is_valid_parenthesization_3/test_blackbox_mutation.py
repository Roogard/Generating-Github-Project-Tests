from python_programs.is_valid_parenthesization import is_valid_parenthesization

# catches mutation: using <= 0 instead of < 0 in negative depth check (rejects valid "()")
def test_simple_pair_valid():
    assert is_valid_parenthesization("()") is True

# catches mutation: missing final depth == 0 check (treating unmatched "(" as valid)
def test_single_open_invalid():
    assert is_valid_parenthesization("(") is False

# catches mutation: wrong operator in decrement (depth += 1 instead of depth -= 1) or missing negative return
def test_single_close_invalid():
    assert is_valid_parenthesization(")") is False

# catches mutation: errors in handling nested structures (e.g., incorrect depth tracking)
def test_nested_valid():
    assert is_valid_parenthesization("(()(()))()") is True

# catches mutation: missing early negative return or wrong condition (failing to detect invalid mid-string unbalance)
def test_interrupted_sequence_invalid():
    assert is_valid_parenthesization("(()))(") is False