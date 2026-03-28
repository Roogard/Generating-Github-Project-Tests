from python_programs.is_valid_parenthesization import is_valid_parenthesization

# --- Statement Coverage ---

def test_stmt_empty_string():
    # Empty string: loop body never executes, returns True
    # A correct validator should accept empty string (depth stays 0)
    assert is_valid_parenthesization('') == True

def test_stmt_open_paren_branch():
    # Exercises depth += 1 branch (open paren)
    # "()" is valid: depth goes 1 then 0
    assert is_valid_parenthesization('()') == True

def test_stmt_close_paren_negative_depth():
    # Exercises depth -= 1 and the early return False (depth < 0)
    # A single ')' causes depth to go negative: invalid
    assert is_valid_parenthesization(')') == False

def test_stmt_unmatched_open():
    # Exercises path where depth != 0 at end but never goes negative
    # "((" has depth 2 at end: a correct validator should return False
    assert is_valid_parenthesization('((') == False

# --- Block Coverage ---

def test_block_matched_parens():
    # Covers: function entry, open-paren block, close-paren block (depth stays >= 0),
    # loop-exit block, final return True
    # "(())" is valid
    assert is_valid_parenthesization('(())') == True

def test_block_early_return_false():
    # Covers: close-paren block where depth < 0 → early return False
    # ")(" triggers depth < 0 on first char
    assert is_valid_parenthesization(')(') == False

def test_block_close_no_negative():
    # Covers: close-paren block where depth decrements but does NOT go negative
    # then loop continues
    # "()()" exercises close-paren block multiple times without going negative
    assert is_valid_parenthesization('()()') == True

# --- Condition Coverage ---

def test_cond_paren_is_open_true():
    # paren == '(': True
    # depth goes to 1, then final return depends on depth == 0
    # Single '(' leaves depth=1: correct validator returns False
    assert is_valid_parenthesization('(') == False  # paren=='(': True

def test_cond_paren_is_open_false_depth_not_negative():
    # paren == '(': False (it's ')'), depth < 0: False (depth was 1, becomes 0)
    # "()" is valid
    assert is_valid_parenthesization('()') == True  # paren=='(': False, depth<0: False

def test_cond_depth_lt_zero_true():
    # paren == '(': False, depth < 0: True
    # ")" causes depth to go -1 → early return False
    assert is_valid_parenthesization(')') == False  # depth<0: True

def test_cond_depth_lt_zero_false_then_end_nonzero():
    # paren == '(': False, depth < 0: False (depth goes 1 → 0, then 1 at end)
    # "()(" has depth=1 at end: correct validator returns False
    assert is_valid_parenthesization('()(') == False  # paren=='(': both T&F, depth<0: False

# --- Path Coverage ---

def test_path_empty_directly_returns_true():
    # path: loop-zero-iterations → return True
    assert is_valid_parenthesization('') == True

def test_path_all_open_no_early_return():
    # path: loop-multiple-iters (all open parens) → final return
    # depth never < 0, but ends > 0: correct validator returns False
    assert is_valid_parenthesization('(((') == False

def test_path_immediate_early_return():
    # path: loop-1-iter → close paren → depth<0 → return False
    assert is_valid_parenthesization(')') == False

def test_path_early_return_mid_loop():
    # path: loop-multiple-iters → open → close → close (depth<0) → return False
    # "()" then ")" = "())"
    assert is_valid_parenthesization('())') == False

def test_path_single_open_close():
    # path: loop-2-iters (open then close, depth never negative) → return True (depth==0)
    assert is_valid_parenthesization('()') == True

def test_path_multiple_iters_balanced():
    # path: loop-many-iters, all close-parens keep depth >=0, final depth==0 → True
    assert is_valid_parenthesization('((()))') == True

def test_path_multiple_iters_unbalanced_open():
    # path: loop-many-iters, never early return, but depth > 0 at end → False
    assert is_valid_parenthesization('(()') == False

def test_path_interleaved_valid():
    # path: multiple open/close transitions, no negative depth, depth==0 at end
    assert is_valid_parenthesization('(()())') == True