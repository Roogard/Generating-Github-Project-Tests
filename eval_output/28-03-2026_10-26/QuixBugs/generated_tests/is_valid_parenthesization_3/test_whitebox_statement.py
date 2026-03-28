from python_programs.is_valid_parenthesization import is_valid_parenthesization

# covers: depth=0, loop body with '(' branch, depth += 1, loop body with ')' branch,
# depth -= 1, depth < 0 check (False), final return True
def test_valid_simple_pair():
    # A correct parenthesization validator SHOULD return True for "()"
    result = is_valid_parenthesization("()")
    assert result == True

# covers: depth < 0 branch (True), return False
def test_invalid_close_before_open():
    # A correct parenthesization validator SHOULD return False when ')' appears before any '('
    result = is_valid_parenthesization(")(")
    assert result == False

# covers: empty string — loop never executes, final return True
def test_empty_string():
    # A correct parenthesization validator SHOULD return True for empty input (vacuously valid)
    result = is_valid_parenthesization("")
    assert result == True

# covers: multiple '(' increments, multiple ')' decrements without going negative, final return True
def test_valid_nested():
    # A correct parenthesization validator SHOULD return True for "((()))"
    result = is_valid_parenthesization("((()))")
    assert result == True

# covers: unmatched open parens — loop completes without depth < 0, but depth != 0; return True path
# NOTE: The function only checks depth < 0; a test for "(()" ensures the loop runs both branches
# without triggering early return. We test what a correct implementation SHOULD do:
# a correct validator SHOULD return False for unmatched '(' — property assertion only.
def test_unmatched_open():
    # A correct parenthesization validator SHOULD return False for "((" (unmatched open)
    # We use a property assertion since the code's behavior for this case may be buggy.
    result = is_valid_parenthesization("((")
    # Property: unmatched parens are invalid; a correct implementation returns False
    assert result == False

# covers: ')' decrement hitting exactly depth==0 (not < 0), verifying boundary of depth < 0 check
def test_valid_sequential_pairs():
    # A correct parenthesization validator SHOULD return True for "()()"
    result = is_valid_parenthesization("()()")
    assert result == True

# covers: early return False deep in string after valid prefix
def test_invalid_after_valid_prefix():
    # A correct parenthesization validator SHOULD return False for "())()"
    result = is_valid_parenthesization("())()")
    assert result == False