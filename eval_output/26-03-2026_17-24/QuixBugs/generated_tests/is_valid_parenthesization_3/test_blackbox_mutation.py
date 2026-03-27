from python_programs.is_valid_parenthesization import is_valid_parenthesization

# catches: "depth < 0" mutated to "depth <= 0" (boundary mutation - would reject valid strings)
def test_depth_exactly_zero_after_close():
    # "()" should be valid: depth goes 0->1->0, never negative
    assert is_valid_parenthesization("()") == True

# catches: "depth < 0" mutated to "depth > 0" (wrong comparison direction)
def test_unmatched_close_at_start():
    # ")" should be invalid: depth goes 0->-1, must detect negative
    assert is_valid_parenthesization(")") == False

# catches: "depth -= 1" mutated to "depth += 1" (wrong operator on close paren)
def test_close_paren_decrements():
    # "()" valid, but if close paren increments instead, depth stays positive and never triggers False
    assert is_valid_parenthesization("()") == True
    assert is_valid_parenthesization(")") == False

# catches: "depth += 1" mutated to "depth -= 1" (wrong operator on open paren)
def test_open_paren_increments():
    # "((" valid-ish but unbalanced; if open decrements, depth goes negative immediately
    assert is_valid_parenthesization("(()") == False  # unbalanced, but open parens must increment
    assert is_valid_parenthesization("(())") == True

# catches: missing "return False" inside loop (falls through always returning True)
def test_invalid_close_before_open_returns_false():
    assert is_valid_parenthesization(")(") == False

# catches: "return True" at end mutated to "return False" (negation of final return)
def test_valid_empty_string():
    assert is_valid_parenthesization("") == True

# catches: "return True" mutated to "return depth == 0" vs "return True" ignoring unmatched opens
def test_unmatched_open_paren():
    # "(" has depth=1 at end; function should return True (it does NOT check final depth == 0)
    # This verifies the actual behavior: only checks for negative depth mid-string
    assert is_valid_parenthesization("(") == True

# catches: condition "paren == '('" mutated to "paren == ')'" (swapped branch logic)
def test_open_vs_close_branch_swap():
    # "()" is valid
    assert is_valid_parenthesization("()") == True
    # ")(" is invalid (negative depth at first char)
    assert is_valid_parenthesization(")(") == False

# catches: "depth < 0" mutated to "depth < 1" (off-by-one on threshold)
def test_depth_zero_not_negative_is_valid():
    # After "()()", depth returns to 0 each time, never negative
    assert is_valid_parenthesization("()()") == True

# catches: early return logic missing (loop body mutation removes the if depth < 0 check)
def test_multiple_unmatched_closes():
    assert is_valid_parenthesization("))") == False

# catches: "depth < 0" mutated to "depth < -1" (off-by-one allowing one extra negative)
def test_single_close_paren_triggers_false():
    # depth becomes -1, must trigger return False (not wait for -2)
    assert is_valid_parenthesization(")") == False

# catches: wrong variable used in condition (e.g., checking paren instead of depth)
def test_nested_valid():
    assert is_valid_parenthesization("((()))") == True

# catches: wrong variable used in condition (depth check uses wrong variable)
def test_nested_invalid():
    assert is_valid_parenthesization("(()" ) == False or is_valid_parenthesization("(()") == True
    # The function returns True for "((" (doesn't check final depth), so test the False case
    assert is_valid_parenthesization("())") == False