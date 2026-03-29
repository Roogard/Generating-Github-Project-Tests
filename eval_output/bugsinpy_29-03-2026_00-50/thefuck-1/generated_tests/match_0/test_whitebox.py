import pytest
from unittest.mock import MagicMock
from thefuck.rules.pip_unknown_command import match


def make_command(script, output):
    cmd = MagicMock()
    cmd.script = script
    cmd.output = output
    return cmd


# --- Statement Coverage ---

def test_statement_all_conditions_true():
    # All three conditions true → match returns True
    cmd = make_command(
        script='pip instal requests',
        output='unknown command "instal" - maybe you meant "install"'
    )
    assert match(cmd) is True


def test_statement_pip_not_in_script():
    # 'pip' not in script → short-circuit, returns False
    cmd = make_command(
        script='npm install requests',
        output='unknown command "instal" - maybe you meant "install"'
    )
    assert match(cmd) is False


# --- Block Coverage ---

def test_block_unknown_command_missing():
    # 'pip' in script but 'unknown command' not in output → second condition False
    cmd = make_command(
        script='pip install requests',
        output='Successfully installed requests'
    )
    assert match(cmd) is False


def test_block_maybe_you_meant_missing():
    # 'pip' in script, 'unknown command' in output, but 'maybe you meant' missing
    cmd = make_command(
        script='pip instal requests',
        output='unknown command "instal"'
    )
    assert match(cmd) is False


def test_block_all_true():
    # All blocks executed with all conditions True (covers full execution block)
    cmd = make_command(
        script='pip3 instlal requests',
        output='ERROR: unknown command "instlal" - maybe you meant "install"'
    )
    assert match(cmd) is True


# --- Condition Coverage ---

def test_condition_pip_in_script_true_others_true():
    # 'pip' in script: True, 'unknown command' in output: True, 'maybe you meant' in output: True
    cmd = make_command(
        script='pip instll requests',
        output='unknown command "instll" - maybe you meant "install"'
    )
    assert match(cmd) is True  # pip_in_script: True, unknown_command: True, maybe_meant: True


def test_condition_pip_in_script_false():
    # 'pip' in script: False → entire expression False
    cmd = make_command(
        script='easy_install requests',
        output='unknown command "instal" - maybe you meant "install"'
    )
    assert match(cmd) is False  # pip_in_script: False


def test_condition_unknown_command_false():
    # 'pip' in script: True, 'unknown command' in output: False
    cmd = make_command(
        script='pip install requests',
        output='maybe you meant something else'
    )
    assert match(cmd) is False  # pip_in_script: True, unknown_command: False


def test_condition_maybe_you_meant_false():
    # 'pip' in script: True, 'unknown command' in output: True, 'maybe you meant': False
    cmd = make_command(
        script='pip instal requests',
        output='unknown command "instal" - did you mean something?'
    )
    assert match(cmd) is False  # pip_in_script: True, unknown_command: True, maybe_meant: False


def test_condition_pip2_in_script():
    # 'pip' in script via 'pip2': True (pip2 contains 'pip')
    cmd = make_command(
        script='pip2 instal requests',
        output='unknown command "instal" - maybe you meant "install"'
    )
    assert match(cmd) is True  # pip_in_script: True (via 'pip2'), unknown_command: True, maybe_meant: True


def test_condition_pip3_in_script():
    # 'pip3' contains 'pip': True
    cmd = make_command(
        script='pip3 instal requests',
        output='unknown command "instal" - maybe you meant "install"'
    )
    assert match(cmd) is True  # pip_in_script: True (via 'pip3'), unknown_command: True, maybe_meant: True


# --- Path Coverage ---

def test_path_all_true():
    # path: pip_in_script=True → unknown_command=True → maybe_meant=True → return True
    cmd = make_command(
        script='pip instll requests',
        output='unknown command "instll" - maybe you meant "install"'
    )
    assert match(cmd) is True


def test_path_pip_false_short_circuit():
    # path: pip_in_script=False → short-circuit → return False
    cmd = make_command(
        script='gem install requests',
        output='unknown command "instal" - maybe you meant "install"'
    )
    assert match(cmd) is False


def test_path_pip_true_unknown_command_false_short_circuit():
    # path: pip_in_script=True → unknown_command=False → short-circuit → return False
    cmd = make_command(
        script='pip install requests',
        output='maybe you meant "install"'
    )
    assert match(cmd) is False


def test_path_pip_true_unknown_command_true_maybe_meant_false():
    # path: pip_in_script=True → unknown_command=True → maybe_meant=False → return False
    cmd = make_command(
        script='pip instal requests',
        output='unknown command "instal" - did you mean install?'
    )
    assert match(cmd) is False


def test_path_empty_output():
    # path: pip_in_script=True → unknown_command=False (empty output) → return False
    cmd = make_command(
        script='pip instal requests',
        output=''
    )
    assert match(cmd) is False


def test_path_empty_script():
    # path: pip_in_script=False (empty script) → return False
    cmd = make_command(
        script='',
        output='unknown command "instal" - maybe you meant "install"'
    )
    assert match(cmd) is False