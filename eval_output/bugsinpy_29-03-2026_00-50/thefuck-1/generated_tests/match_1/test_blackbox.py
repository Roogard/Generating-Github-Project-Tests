import pytest
from unittest.mock import MagicMock
from thefuck.rules.pip_unknown_command import match


def make_command(script, output):
    cmd = MagicMock()
    cmd.script = script
    cmd.output = output
    return cmd


# --- BVA ---

def test_bva_script_exactly_pip():
    # script is exactly 'pip', output contains both required strings
    cmd = make_command('pip', 'unknown command "foo" - maybe you meant "install"')
    assert match(cmd) == True

def test_bva_script_pip_with_subcommand():
    # script is 'pip install' — 'pip' is present
    cmd = make_command('pip install', 'unknown command "instl" - maybe you meant "install"')
    assert match(cmd) == True

def test_bva_script_pip3():
    # 'pip' is a substring of 'pip3'
    cmd = make_command('pip3 install', 'unknown command "instl" - maybe you meant "install"')
    assert match(cmd) == True

def test_bva_empty_script():
    # empty script — 'pip' not in ''
    cmd = make_command('', 'unknown command "foo" - maybe you meant "bar"')
    assert match(cmd) == False

def test_bva_empty_output():
    # empty output — neither required string present
    cmd = make_command('pip', '')
    assert match(cmd) == False

def test_bva_output_missing_maybe_you_meant():
    # output has 'unknown command' but not 'maybe you meant'
    cmd = make_command('pip', 'unknown command "foo"')
    assert match(cmd) == False

def test_bva_output_missing_unknown_command():
    # output has 'maybe you meant' but not 'unknown command'
    cmd = make_command('pip', 'maybe you meant "install"')
    assert match(cmd) == False

def test_bva_output_both_strings_present():
    # both strings present — minimal valid output
    cmd = make_command('pip', 'unknown command - maybe you meant')
    assert match(cmd) == True

def test_bva_single_char_script_not_pip():
    # single character script — 'pip' not in 'p'
    cmd = make_command('p', 'unknown command - maybe you meant')
    assert match(cmd) == False


# --- ECP ---

def test_ecp_valid_pip_with_full_output():
    # valid class: script contains 'pip', output has both required phrases
    cmd = make_command('pip intsall requests', 'unknown command "intsall" - maybe you meant "install"')
    assert match(cmd) == True

def test_ecp_invalid_script_no_pip():
    # invalid class: script does not contain 'pip'
    cmd = make_command('conda install numpy', 'unknown command "instl" - maybe you meant "install"')
    assert match(cmd) == False

def test_ecp_invalid_output_only_unknown_command():
    # invalid class: output has 'unknown command' only
    cmd = make_command('pip', 'unknown command "xyz"')
    assert match(cmd) == False

def test_ecp_invalid_output_only_maybe_you_meant():
    # invalid class: output has 'maybe you meant' only
    cmd = make_command('pip', 'maybe you meant "install"')
    assert match(cmd) == False

def test_ecp_invalid_all_conditions_false():
    # invalid class: none of the three conditions met
    cmd = make_command('conda', 'error: no such option')
    assert match(cmd) == False

def test_ecp_valid_pip_embedded_in_longer_word():
    # valid class: 'pip' is a substring in script (e.g., 'pipenv')
    cmd = make_command('pipenv install', 'unknown command "instl" - maybe you meant "install"')
    assert match(cmd) == True

def test_ecp_valid_pip_at_end_of_script():
    # valid class: 'pip' appears at end of script string
    cmd = make_command('sudo pip', 'unknown command "foo" - maybe you meant "bar"')
    assert match(cmd) == True

def test_ecp_invalid_output_empty_script_nonempty():
    # invalid class: script is non-empty but no 'pip', output valid
    cmd = make_command('npm install', 'unknown command - maybe you meant')
    assert match(cmd) == False

def test_ecp_invalid_case_sensitive_pip_uppercase():
    # invalid class: 'PIP' is not 'pip' — case sensitive check
    cmd = make_command('PIP install', 'unknown command - maybe you meant')
    assert match(cmd) == False

def test_ecp_invalid_case_sensitive_unknown_command_uppercase():
    # invalid class: 'Unknown command' vs 'unknown command'
    cmd = make_command('pip install', 'Unknown command - maybe you meant')
    assert match(cmd) == False

def test_ecp_invalid_case_sensitive_maybe_you_meant_uppercase():
    # invalid class: 'Maybe you meant' vs 'maybe you meant'
    cmd = make_command('pip install', 'unknown command - Maybe you meant')
    assert match(cmd) == False


# --- Mutation Detection ---

def test_mutation_and_vs_or_script_no_pip_but_output_valid():
    # Detects if 'and' were replaced by 'or': should be False when script lacks 'pip'
    # A correct match SHOULD require ALL three conditions simultaneously
    cmd = make_command('npm install', 'unknown command - maybe you meant')
    assert match(cmd) == False

def test_mutation_and_vs_or_output_missing_unknown_command():
    # Detects 'and' vs 'or': only one output phrase present — must return False
    cmd = make_command('pip install', 'maybe you meant "install"')
    assert match(cmd) == False

def test_mutation_and_vs_or_output_missing_maybe_you_meant():
    # Detects 'and' vs 'or': only 'unknown command' in output — must return False
    cmd = make_command('pip install', 'unknown command "xyz"')
    assert match(cmd) == False

def test_mutation_negation_should_return_true():
    # Detects negation mutation (e.g., 'not in' instead of 'in')
    # With all correct conditions, a correct match SHOULD return True
    cmd = make_command('pip', 'unknown command "foo" - maybe you meant "bar"')
    assert match(cmd) == True

def test_mutation_negation_should_return_false_no_pip():
    # Detects negation mutation: 'pip' not in script must yield False
    cmd = make_command('gem install', 'unknown command - maybe you meant')
    assert match(cmd) == False

def test_mutation_wrong_substring_similar_phrase():
    # Detects wrong constant: output has 'unknown cmd' instead of 'unknown command'
    cmd = make_command('pip', 'unknown cmd "foo" - maybe you meant "bar"')
    assert match(cmd) == False

def test_mutation_wrong_substring_maybe_you_meant_partial():
    # Detects wrong constant: 'maybe you mean' (missing 't') — not the required phrase
    cmd = make_command('pip', 'unknown command "foo" - maybe you mean "bar"')
    assert match(cmd) == False

def test_mutation_wrong_variable_script_vs_output():
    # Detects if 'command.output' were checked instead of 'command.script' for 'pip'
    # script has no 'pip', output contains 'pip' — a correct impl checks script not output
    cmd = make_command('conda install', 'pip unknown command - maybe you meant install')
    assert match(cmd) == False

def test_mutation_all_three_correct_returns_true():
    # Baseline: ensures a correct implementation returns True for fully valid input
    cmd = make_command('pip install flsk', 'unknown command "install" - maybe you meant "install"')
    assert match(cmd) == True

def test_mutation_off_by_one_empty_strings_boundary():
    # Both script and output are non-empty but contain no required keywords
    cmd = make_command('x', 'y')
    assert match(cmd) == False