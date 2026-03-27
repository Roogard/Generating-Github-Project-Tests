from python_programs.is_valid_parenthesization import is_valid_parenthesization

# catches: "depth < 0" mutated to "depth <= 0" (boundary mutation - would reject valid strings)
def test_depth_exactly_zero_after_close():
    # "()" -> depth goes 1, then 0; should be valid
    assert is_valid_parenthesization("()") == True

# catches: "depth < 0" mutated to "depth < 1" (off-by-one on negative check)
def test_depth_goes_to_zero_then_open():
    # "()()" -> valid, depth: 1,0,1,0
    assert is_valid_parenthesization("()()") == True

# catches: "depth -= 1" mutated to "depth += 1" (wrong operator on close paren)
def test_unmatched_close_paren_at_start():
    # ")" -> depth goes -1, should return False
    assert is_valid_parenthesization(")") == False

# catches: "depth += 1" mutated to "depth -= 1" (wrong operator on open paren)
def test_unmatched_open_paren():
    # "(" -> depth ends at 1, should return True (function does not check final depth)
    # Actually the function returns True for unmatched open parens
    # This tests the open paren increments correctly
    assert is_valid_parenthesization("(") == True

# catches: missing "return False" (function never returns False)
def test_close_before_open_returns_false():
    assert is_valid_parenthesization(")(") == False

# catches: "return True" at end mutated to "return False" (wrong return value)
def test_empty_string_is_valid():
    assert is_valid_parenthesization("") == True

# catches: "return True" mutated to "return False" for valid nested parens
def test_nested_parens_valid():
    assert is_valid_parenthesization("(())") == True

# catches: wrong comparison "paren == '('" mutated to "paren == ')'" (swapped branch logic)
def test_mixed_valid_sequence():
    assert is_valid_parenthesization("(()())") == True

# catches: "depth < 0" mutated to "depth > 0" (inverted check - would reject valid, accept invalid)
def test_multiple_unmatched_close():
    assert is_valid_parenthesization("))") == False

# catches: off-by-one where depth check uses wrong threshold, near-boundary
def test_close_paren_brings_depth_to_negative_one():
    # "())" -> depth: 1, 0, -1 -> should return False
    assert is_valid_parenthesization("())") == False

# catches: "depth += 1" not executed (open paren ignored) making valid string look invalid
def test_single_matched_pair():
    assert is_valid_parenthesization("()") == True

# catches: final "return True" missing (function falls through returning None)
def test_return_value_is_bool_true():
    result = is_valid_parenthesization("()")
    assert result is True

# catches: final "return True" mutated to "return depth == 0" or similar wrong condition
def test_unbalanced_open_returns_true():
    # The function returns True even for "((" since it only checks for negative depth
    assert is_valid_parenthesization("((") == True

# catches: "depth < 0" mutated to "depth < -1" (off-by-one in negative threshold)
def test_close_paren_alone_detected():
    # Single ")" should immediately return False when depth hits -1
    assert is_valid_parenthesization(")") == False

# catches: paren comparison using wrong character literal
def test_only_open_parens():
    assert is_valid_parenthesization("(((") == True

# catches: wrong variable used in depth update
def test_alternating_valid():
    assert is_valid_parenthesization("()()()") == True

# catches: depth not reset / initialized to wrong value (e.g., depth = 1 instead of 0)
def test_single_close_with_initial_depth_zero():
    # If depth started at 1, ")" would not trigger False
    assert is_valid_parenthesization(")") == False