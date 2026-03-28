from python_programs.is_valid_parenthesization import is_valid_parenthesization

# --- BVA ---

def test_empty_string():
    # Empty string: no parens, depth never goes negative, should be valid
    assert is_valid_parenthesization('') == True

def test_single_open_paren():
    # Single '(': depth ends at 1, never negative — but unmatched, correct impl SHOULD return False
    assert is_valid_parenthesization('(') == False

def test_single_close_paren():
    # Single ')': depth goes to -1 immediately, correct impl SHOULD return False
    assert is_valid_parenthesization(')') == False

def test_minimal_valid_pair():
    # Smallest valid: "()"
    assert is_valid_parenthesization('()') == True

def test_minimal_invalid_reversed():
    # Reversed smallest: ")("
    assert is_valid_parenthesization(')(') == False

def test_two_open_one_close():
    # "((" — two opens, one close missing, unmatched
    assert is_valid_parenthesization('((' ) == False

def test_one_open_two_close():
    # "())" — extra close
    assert is_valid_parenthesization('())') == False

def test_large_valid():
    # Large balanced string: 1000 matched pairs
    s = '()' * 1000
    assert is_valid_parenthesization(s) == True

def test_large_invalid_extra_open():
    # 1000 matched pairs + one open at end
    s = '()' * 1000 + '('
    assert is_valid_parenthesization(s) == False

def test_large_invalid_extra_close():
    # 1000 matched pairs + one close at end
    s = '()' * 1000 + ')'
    assert is_valid_parenthesization(s) == False

# --- ECP ---

def test_valid_nested():
    # Valid class: properly nested parens
    assert is_valid_parenthesization('((()))') == True

def test_valid_sequential():
    # Valid class: sequential pairs
    assert is_valid_parenthesization('()()()') == True

def test_invalid_early_close():
    # Invalid class: closing paren before any opening
    assert is_valid_parenthesization(')(()') == False

def test_invalid_unmatched_open():
    # Invalid class: more opens than closes
    assert is_valid_parenthesization('(()') == False

def test_invalid_unmatched_close():
    # Invalid class: more closes than opens
    assert is_valid_parenthesization('())') == False

def test_valid_complex_nested():
    # Valid class: complex nested and sequential mix
    assert is_valid_parenthesization('(())(()())') == True

def test_invalid_interleaved():
    # Invalid class: interleaved unmatched
    assert is_valid_parenthesization('(()(') == False

def test_all_opens():
    # Invalid class: all opening parens
    assert is_valid_parenthesization('((((') == False

def test_all_closes():
    # Invalid class: all closing parens
    assert is_valid_parenthesization('))))') == False

# --- Mutation Detection ---

def test_mutation_off_by_one_depth_check():
    # Detects mutation: `depth < 0` changed to `depth <= 0`
    # "()" — after '(' depth=1, after ')' depth=0; should be VALID
    # A mutant using depth<=0 would return False here incorrectly
    assert is_valid_parenthesization('()') == True

def test_mutation_depth_never_goes_negative_but_unmatched():
    # Detects mutation: missing final `depth == 0` check
    # A correct is_valid_parenthesization SHOULD return False for unmatched '('
    # because the parenthesization is not valid — depth ends at 1
    assert is_valid_parenthesization('(') == False

def test_mutation_depth_increment_vs_decrement():
    # Detects mutation: `depth += 1` changed to `depth -= 1`
    # "(())" — valid; a mutant swapping +/- for '(' would produce wrong depth
    assert is_valid_parenthesization('(())') == True

def test_mutation_return_true_vs_false_on_negative():
    # Detects mutation: `return False` changed to `return True` inside depth<0 branch
    assert is_valid_parenthesization(')(') == False

def test_mutation_final_return_flipped():
    # Detects mutation: final `return True` changed to `return False`
    # A well-balanced string must return True
    assert is_valid_parenthesization('(())()') == True

def test_mutation_depth_lt_vs_lte_boundary():
    # Detects mutation: `depth < 0` changed to `depth <= 0`
    # "()()" — depth hits 0 after each pair legitimately; must remain True
    assert is_valid_parenthesization('()()') == True

def test_mutation_unmatched_open_two():
    # Detects mutation: final check absent (always returns True at end)
    # "(()" — depth ends at 1, must be False
    assert is_valid_parenthesization('(()') == False

def test_mutation_unmatched_open_deep():
    # Detects mutation: final depth check missing
    # "((((()))" — opens=5, closes=3, depth ends at 2, must be False
    assert is_valid_parenthesization('((((())') == False

def test_mutation_wrong_variable_depth():
    # Detects mutation: checking wrong variable in the depth < 0 condition
    # ")(" — first char ')' should immediately make depth -1 and return False
    assert is_valid_parenthesization(')(') == False

def test_mutation_off_by_one_loop_range():
    # If the loop were range(len(parens)-1) instead of iterating all chars,
    # a single unmatched ')' at the last position would be missed.
    # "())" — last ')' is the extra one; must return False
    assert is_valid_parenthesization('())') == False