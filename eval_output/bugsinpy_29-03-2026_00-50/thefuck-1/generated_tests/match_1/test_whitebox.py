import pytest
from unittest.mock import MagicMock
from thefuck.rules.pip_unknown_command import match

def make_command(script, output):
    cmd = MagicMock()
    cmd.script = script
    cmd.output = output
    return cmd

# --- Statement Coverage ---

def test_statement_all_true():
    # Exercises the single return statement with all conditions True
    cmd = make_command(
        script='pip instal requests',
        output="unknown command \"instal\" - maybe you meant \"install\""
    )
    assert match(cmd) == True

def test_statement_all_false():
    # Exercises the return statement with all conditions False
    cmd = make_command(
        script='npm install',
        output='some error'
    )
    assert match(cmd) == False

# --- Block Coverage ---

# Block: entire and-chain evaluates to True (covered by test_statement_all_true)
# Block: short-circuit on first condition ('pip' not in script)

def test_block_short_circuit_no_pip():
    # 'pip' not in script -> short-circuit, remaining conditions irrelevant
    cmd = make_command(
        script='gem install rails',
        output="unknown command \"instal\" - maybe you meant \"install\""
    )
    assert match(cmd) == False

def test_block_short_circuit_no_unknown_command():
    # 'pip' in script, but 'unknown command' not in output -> short-circuit
    cmd = make_command(
        script='pip install requests',
        output="some other error - maybe you meant something"
    )
    assert match(cmd) == False

def test_block_short_circuit_no_maybe_meant():
    # 'pip' in script, 'unknown command' in output, but 'maybe you meant' not in output
    cmd = make_command(
        script='pip instal requests',
        output="unknown command \"instal\""
    )
    assert match(cmd) == False

# --- Condition Coverage ---

# Sub-expression 1: 'pip' in command.script  -> True / False
# Sub-expression 2: 'unknown command' in command.output -> True / False
# Sub-expression 3: 'maybe you meant' in command.output -> True / False

def test_condition_pip_true_unknown_true_maybe_true():
    # 'pip' in script: True, 'unknown command' in output: True, 'maybe you meant' in output: True
    cmd = make_command(
        script='pip instal requests',
        output="unknown command \"instal\" - maybe you meant \"install\""
    )
    assert match(cmd) == True  # pip:True, unknown_command:True, maybe_meant:True

def test_condition_pip_false():
    # 'pip' in script: False, others irrelevant (short-circuit)
    cmd = make_command(
        script='easy_install requests',
        output="unknown command \"instal\" - maybe you meant \"install\""
    )
    assert match(cmd) == False  # pip:False

def test_condition_pip_true_unknown_false():
    # 'pip' in script: True, 'unknown command' in output: False
    cmd = make_command(
        script='pip install requests',
        output="maybe you meant something else"
    )
    assert match(cmd) == False  # pip:True, unknown_command:False

def test_condition_pip_true_unknown_true_maybe_false():
    # 'pip' in script: True, 'unknown command' in output: True, 'maybe you meant' in output: False
    cmd = make_command(
        script='pip instal requests',
        output="unknown command \"instal\""
    )
    assert match(cmd) == False  # pip:True, unknown_command:True, maybe_meant:False

def test_condition_pip_in_path():
    # 'pip' appears as part of a longer path string - still True
    cmd = make_command(
        script='/usr/bin/pip instal requests',
        output="unknown command \"instal\" - maybe you meant \"install\""
    )
    assert match(cmd) == True  # pip:True (substring), unknown_command:True, maybe_meant:True

# --- Path Coverage ---

# The function has one compound boolean expression with 3 sub-conditions.
# Due to short-circuit evaluation there are 4 distinct exit paths:
#   Path 1: pip:False -> return False
#   Path 2: pip:True, unknown_command:False -> return False
#   Path 3: pip:True, unknown_command:True, maybe_meant:False -> return False
#   Path 4: pip:True, unknown_command:True, maybe_meant:True -> return True

def test_path1_pip_false():
    # path: pip:False -> short-circuit -> return False
    cmd = make_command(
        script='conda install numpy',
        output="unknown command \"instal\" - maybe you meant \"install\""
    )
    assert match(cmd) == False

def test_path2_pip_true_unknown_false():
    # path: pip:True -> unknown_command:False -> short-circuit -> return False
    cmd = make_command(
        script='pip install requests',
        output="ERROR: No matching distribution found - maybe you meant something"
    )
    assert match(cmd) == False

def test_path3_pip_true_unknown_true_maybe_false():
    # path: pip:True -> unknown_command:True -> maybe_meant:False -> return False
    cmd = make_command(
        script='pip badcmd requests',
        output="unknown command \"badcmd\""
    )
    assert match(cmd) == False

def test_path4_pip_true_unknown_true_maybe_true():
    # path: pip:True -> unknown_command:True -> maybe_meant:True -> return True
    cmd = make_command(
        script='pip downlod requests',
        output='ERROR: unknown command "downlod" - maybe you meant "download"'
    )
    assert match(cmd) == True

def test_path_pip_in_output_not_script():
    # 'pip' only appears in output, not in script -> Path 1 (pip:False in script)
    cmd = make_command(
        script='python setup.py install',
        output="use pip: unknown command - maybe you meant install"
    )
    assert match(cmd) == False