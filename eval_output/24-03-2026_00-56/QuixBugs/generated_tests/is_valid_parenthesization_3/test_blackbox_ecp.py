import pytest
from correct_python_programs.is_valid_parenthesization import is_valid_parenthesization

# Valid equivalence class: empty string (balanced)
def test_valid_empty():
    assert is_valid_parenthesization("") == True

# Valid equivalence class: simple balanced pair
def test_valid_single_pair():
    assert is_valid_parenthesization("()") == True

# Valid equivalence class: nested balanced parentheses
def test_valid_nested():
    assert is_valid_parenthesization("(())") == True

# Valid equivalence class: sequential balanced pairs
def test_valid_sequential():
    assert is_valid_parenthesization("()()") == True

# Valid equivalence class: complex balanced combination
def test_valid_complex():
    assert is_valid_parenthesization("(()(()))") == True

# Invalid equivalence class: string with only opening parentheses (depth > 0 at end)
def test_invalid_only_open():
    assert is_valid_parenthesization("(((") == False

# Invalid equivalence class: string with only closing parentheses (depth < 0 during traversal)
def test_invalid_only_close():
    assert is_valid_parenthesization(")))") == False

# Invalid equivalence class: more closing than opening at some prefix (depth < 0)
def test_invalid_close_before_open():
    assert is_valid_parenthesization(")(") == False

# Invalid equivalence class: balanced start but extra closing later
def test_invalid_extra_close():
    assert is_valid_parenthesization("())") == False

# Invalid equivalence class: balanced end but extra opening earlier
def test_invalid_extra_open():
    assert is_valid_parenthesization("(()") == False

# Invalid equivalence class: string with other characters (non-parenthesis)
def test_invalid_other_chars():
    assert is_valid_parenthesization("(a)") == False