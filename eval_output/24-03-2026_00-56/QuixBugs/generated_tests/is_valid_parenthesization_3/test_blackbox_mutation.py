from correct_python_programs.is_valid_parenthesization import is_valid_parenthesization

# catches: "depth == 0" mutated to "depth > 0" or "depth < 0" (wrong comparison)
def test_empty_string():
    assert is_valid_parenthesization("") == True

# catches: "depth < 0" mutated to "depth <= 0" (boundary mutation)
def test_single_closing_paren():
    assert is_valid_parenthesization(")") == False

# catches: "depth += 1" mutated to "depth += 0" or "depth = 1" (wrong increment)
def test_single_opening_paren():
    assert is_valid_parenthesization("(") == False

# catches: "depth -= 1" mutated to "depth -= 0" or "depth = -1" (wrong decrement)
def test_mismatched_pair_closing_first():
    assert is_valid_parenthesization(")(") == False

# catches: missing "if depth < 0: return False" (negation error)
def test_early_excess_closing():
    assert is_valid_parenthesization("())") == False

# catches: "depth == 0" mutated to "depth == 1" (off-by-one in return)
def test_simple_valid_pair():
    assert is_valid_parenthesization("()") == True

# catches: "depth < 0" mutated to "depth > 0" (comparison swap)
def test_excess_closing_after_valid_prefix():
    assert is_valid_parenthesization("())(") == False

# catches: "depth += 1" mutated to "depth += 2" (wrong constant)
def test_nested_valid():
    assert is_valid_parenthesization("(())") == True

# catches: "depth -= 1" mutated to "depth -= 2" (wrong constant)
def test_nested_invalid():
    assert is_valid_parenthesization("(()))") == False

# catches: "return False" mutated to "return True" (negation error)
def test_invalid_sequence_with_negative_depth():
    assert is_valid_parenthesization(")()") == False

# catches: "depth == 0" mutated to "depth != 0" (negation error)
def test_longer_valid_sequence():
    assert is_valid_parenthesization("()(())()") == True

# catches: "if paren == '(':" mutated to "if paren == ')':" (wrong operator)
def test_all_opening_then_all_closing():
    assert is_valid_parenthesization("((()))") == True

# catches: "else: depth -= 1" mutated to "else: depth += 1" (wrong operator)
def test_all_closing_then_all_opening():
    assert is_valid_parenthesization(")))(((") == False

# catches: "depth < 0" mutated to "depth <= -1" (off-by-one in boundary)
def test_exactly_one_excess_closing():
    assert is_valid_parenthesization("())") == False

# catches: "depth == 0" mutated to "depth >= 0" (wrong comparison)
def test_valid_sequence_ending_at_zero():
    assert is_valid_parenthesization("(()())") == True