from python_programs.is_valid_parenthesization import is_valid_parenthesization

def test_empty_parenthesization():
    # paren=='(' not evaluated, depth<0: False
    assert is_valid_parenthesization("") == True

def test_balanced_parentheses():
    # paren=='(': True (for '('), False (for ')'); depth<0: False
    assert is_valid_parenthesization("()") == True

def test_too_many_closing_parenthesis():
    # paren=='(': False; depth<0: True
    assert is_valid_parenthesization(")(") == False