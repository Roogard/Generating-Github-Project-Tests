import pytest
from unittest.mock import MagicMock
from thefuck.rules.pip_unknown_command import match


def make_command(script, output):
    cmd = MagicMock()
    cmd.script = script
    cmd.output = output
    return cmd


# --- BVA ---

def test_bva_all_conditions_present_minimal():
    # Boundary: minimal strings that satisfy all three conditions
    cmd = make_command('pip install foo', 'unknown command "foo" - maybe you meant something')
    assert match(cmd) == True

def test_bva_missing_unknown_command_in_output():
    # Boundary: output contains 'maybe you meant' but NOT 'unknown command'
    cmd = make_command('pip install foo', 'maybe you meant something else')
    assert match(cmd) == False

def test_bva_missing_maybe_you_meant_in_output():
    # Boundary: output contains 'unknown command' but NOT 'maybe you meant'
    cmd = make_command('pip install foo', 'unknown command "install"')
    assert match(cmd) == False

def test_bva_empty_script():
    # Boundary: empty script string — 'pip' not in it
    cmd = make_command('', 'unknown command "foo" - maybe you meant something')
    assert match(cmd) == False

def test_bva_empty_output():
    # Boundary: empty output string
    cmd = make_command('pip install foo', '')
    assert match(cmd) == False

def test_bva_all_empty():
    # Boundary: all empty
    cmd = make_command('', '')
    assert match(cmd) == False

def test_bva_pip_only_script():
    # Boundary: script is exactly 'pip'
    cmd = make_command('pip', 'unknown command "foo" - maybe you meant something')
    assert match(cmd) == True

def test_bva_output_with_both_phrases_adjacent():
    # Boundary: both required phrases appear right next to each other
    cmd = make_command('pip foo', 'unknown command maybe you meant')
    assert match(cmd) == True


# --- ECP ---

def test_ecp_valid_pip3_with_correct_output():
    # Valid class: pip3 command, correct error output
    cmd = make_command('pip3 instll requests', 'ERROR: unknown command "instll" - maybe you meant "install"')
    assert match(cmd) == True

def test_ecp_valid_pip2_with_correct_output():
    # Valid class: pip2 command, correct error output
    cmd = make_command('pip2 instll requests', 'ERROR: unknown command "instll" - maybe you meant "install"')
    assert match(cmd) == True

def test_ecp_invalid_no_pip_in_script():
    # Invalid class: script does not contain 'pip'
    cmd = make_command('gem install foo', 'unknown command "foo" - maybe you meant something')
    assert match(cmd) == False

def test_ecp_invalid_no_pip_no_relevant_output():
    # Invalid class: completely unrelated command and output
    cmd = make_command('git commit -m "fix"', 'error: pathspec does not match')
    assert match(cmd) == False

def test_ecp_invalid_pip_in_script_but_no_error_phrases():
    # Invalid class: pip in script but output is a success message
    cmd = make_command('pip install requests', 'Successfully installed requests-2.28.0')
    assert match(cmd) == False

def test_ecp_valid_pip_substring_in_script():
    # Valid class: 'pip' appears as substring in a longer script token
    cmd = make_command('pip install foo', 'unknown command "foo" - maybe you meant "install"')
    assert match(cmd) == True

def test_ecp_invalid_only_unknown_command_phrase():
    # Invalid class: output has 'unknown command' but not 'maybe you meant'
    cmd = make_command('pip install foo', 'ERROR: unknown command "foo"')
    assert match(cmd) == False

def test_ecp_invalid_only_maybe_you_meant_phrase():
    # Invalid class: output has 'maybe you meant' but not 'unknown command'
    cmd = make_command('pip install foo', 'maybe you meant "install"?')
    assert match(cmd) == False

def test_ecp_valid_case_sensitive_pip_lowercase():
    # Equivalence: 'pip' must appear literally (lowercase)
    cmd = make_command('pip install foo', 'unknown command "foo" - maybe you meant "install"')
    assert match(cmd) == True

def test_ecp_invalid_pip_uppercase_only():
    # Invalid class: 'PIP' uppercase in script, 'pip' not present
    cmd = make_command('PIP install foo', 'unknown command "foo" - maybe you meant something')
    # A correct match SHOULD require lowercase 'pip' in script
    assert match(cmd) == False

def test_ecp_invalid_case_sensitive_unknown_command():
    # Invalid class: 'Unknown Command' (wrong case) in output
    cmd = make_command('pip install foo', 'Unknown Command "foo" - Maybe You Meant "install"')
    assert match(cmd) == False


# --- Mutation Detection ---

def test_mutation_and_vs_or_all_three_required():
    # Detects: replacing 'and' with 'or' — only first condition true should still return False
    cmd = make_command('pip install foo', 'some other output')
    # Only 'pip' in script is true; no error phrases in output
    assert match(cmd) == False

def test_mutation_and_vs_or_second_condition_only():
    # Detects: replacing 'and' with 'or' — only 'unknown command' in output
    cmd = make_command('git commit', 'unknown command "foo"')
    # 'pip' not in script, 'maybe you meant' not in output
    assert match(cmd) == False

def test_mutation_and_vs_or_third_condition_only():
    # Detects: replacing 'and' with 'or' — only 'maybe you meant' in output
    cmd = make_command('git commit', 'maybe you meant something')
    assert match(cmd) == False

def test_mutation_negation_pip_in_script():
    # Detects: flipped boolean — 'pip' NOT in script should not match
    cmd = make_command('npm install foo', 'unknown command "foo" - maybe you meant something')
    assert match(cmd) == False

def test_mutation_negation_unknown_command():
    # Detects: negation on 'unknown command' check — present should match, absent should not
    cmd_present = make_command('pip foo', 'unknown command "foo" - maybe you meant something')
    cmd_absent = make_command('pip foo', 'maybe you meant something')
    assert match(cmd_present) == True
    assert match(cmd_absent) == False

def test_mutation_negation_maybe_you_meant():
    # Detects: negation on 'maybe you meant' check
    cmd_present = make_command('pip foo', 'unknown command "foo" - maybe you meant something')
    cmd_absent = make_command('pip foo', 'unknown command "foo"')
    assert match(cmd_present) == True
    assert match(cmd_absent) == False

def test_mutation_wrong_variable_script_vs_output():
    # Detects: checking 'pip' in output instead of script
    # Script has pip, output does NOT have pip — correct impl checks script
    cmd = make_command('pip install foo', 'unknown command "foo" - maybe you meant "install"')
    assert match(cmd) == True

def test_mutation_wrong_variable_output_vs_script():
    # Detects: checking 'unknown command' in script instead of output
    cmd = make_command('pip install foo', 'unknown command "foo" - maybe you meant "install"')
    assert match(cmd) == True  # both correct — positive anchor

def test_mutation_wrong_string_unknown_vs_maybe():
    # Detects: checking 'unknown command' twice instead of also checking 'maybe you meant'
    cmd = make_command('pip foo', 'unknown command "foo" unknown command repeated')
    # 'maybe you meant' is NOT present, so correct impl returns False
    assert match(cmd) == False

def test_mutation_pip_substring_check_exact_phrase():
    # Detects: off-by-one or wrong substring — 'pi' vs 'pip' 
    cmd = make_command('pi install foo', 'unknown command "foo" - maybe you meant something')
    # 'pip' is NOT in 'pi install foo', so correct impl returns False
    assert match(cmd) == False

def test_mutation_all_three_conditions_true_returns_true():
    # Positive anchor test — ensures all three conditions being True yields True
    cmd = make_command('pip instll requests', 
                       'ERROR: unknown command "instll" - maybe you meant "install"')
    assert match(cmd) == True