import pytest
from unittest.mock import MagicMock
from thefuck.rules.git_push import match

# Helper to build a command mock


def make_command(script_parts, output):
    cmd = MagicMock()
    cmd.script_parts = script_parts
    cmd.output = output
    return cmd


# --- ECP ---

# Valid class: both 'push' in script_parts AND 'set-upstream' in output
def test_ecp_valid_push_and_set_upstream():
    cmd = make_command(
        ['git', 'push', 'origin', 'master'],
        "fatal: The current branch master has no upstream branch.\n"
        "To push the current branch and set the remote as upstream, use\n"
        "    git push --set-upstream origin master"
    )
    assert match(cmd) == True


# Invalid class: 'push' NOT in script_parts, 'set-upstream' in output
def test_ecp_invalid_no_push_in_parts():
    cmd = make_command(
        ['git', 'status'],
        "To push the current branch and set-upstream use..."
    )
    assert match(cmd) == False


# Invalid class: 'push' in script_parts, 'set-upstream' NOT in output
def test_ecp_invalid_no_set_upstream_in_output():
    cmd = make_command(
        ['git', 'push', 'origin', 'master'],
        "Everything up-to-date"
    )
    assert match(cmd) == False


# Invalid class: neither 'push' nor 'set-upstream'
def test_ecp_invalid_neither_condition():
    cmd = make_command(
        ['git', 'commit', '-m', 'msg'],
        "Some other git error"
    )
    assert match(cmd) == False


# --- BVA ---

# Empty script_parts
def test_bva_empty_script_parts():
    cmd = make_command(
        [],
        "To push the current branch and set-upstream use..."
    )
    assert match(cmd) == False


# Single-element script_parts containing 'push'
def test_bva_single_element_push_in_parts():
    cmd = make_command(
        ['push'],
        "hint: set-upstream blah blah"
    )
    assert match(cmd) == True


# Single-element script_parts NOT containing 'push'
def test_bva_single_element_no_push():
    cmd = make_command(
        ['git'],
        "set-upstream hint here"
    )
    assert match(cmd) == False


# Empty output string
def test_bva_empty_output():
    cmd = make_command(
        ['git', 'push'],
        ""
    )
    assert match(cmd) == False


# Output containing only 'set-upstream' keyword
def test_bva_output_exactly_set_upstream():
    cmd = make_command(
        ['git', 'push'],
        "set-upstream"
    )
    assert match(cmd) == True


# Output with 'set-upstream' as a substring inside a word (boundary: not exact word)
def test_bva_output_set_upstream_as_substring():
    cmd = make_command(
        ['git', 'push'],
        "Please use --set-upstream-extended or something"
    )
    # 'set-upstream' IS a substring of '--set-upstream-extended', so it matches
    assert match(cmd) == True


# 'push' as substring of another word in script_parts (should NOT match)
def test_bva_push_as_substring_in_part():
    cmd = make_command(
        ['git', 'pushall'],
        "set-upstream hint"
    )
    # 'push' is NOT in the list as an element; 'pushall' != 'push'
    assert match(cmd) == False


# Large script_parts list, 'push' at the end
def test_bva_large_script_parts_push_at_end():
    parts = ['git'] + ['other'] * 100 + ['push']
    cmd = make_command(parts, "set-upstream")
    assert match(cmd) == True


# --- Mutation Detection ---

# Detects mutation: 'and' changed to 'or'
# With 'push' in parts but NOT 'set-upstream' in output, should return False
# An 'or' mutation would return True here
def test_mutation_and_vs_or_push_without_set_upstream():
    cmd = make_command(
        ['git', 'push'],
        "Everything up-to-date"
    )
    # A correct implementation uses AND: both conditions must be True
    assert match(cmd) == False


# Detects mutation: 'and' changed to 'or'
# With 'set-upstream' in output but NOT 'push' in parts, should return False
# An 'or' mutation would return True here
def test_mutation_and_vs_or_set_upstream_without_push():
    cmd = make_command(
        ['git', 'fetch'],
        "set-upstream hint"
    )
    # A correct implementation uses AND: both conditions must be True
    assert match(cmd) == False


# Detects mutation: checking 'push' in output instead of script_parts
def test_mutation_wrong_variable_push_in_output_not_parts():
    cmd = make_command(
        ['git', 'fetch'],
        "push something set-upstream"
    )
    # Correct implementation checks script_parts for 'push', not output
    assert match(cmd) == False


# Detects mutation: checking 'set-upstream' in script_parts instead of output
def test_mutation_wrong_variable_set_upstream_in_parts_not_output():
    cmd = make_command(
        ['git', 'push', '--set-upstream'],
        "Everything up-to-date"
    )
    # Even with '--set-upstream' in parts, if it's not in output, should return False
    # '--set-upstream' != 'set-upstream' for list membership, and output lacks it
    assert match(cmd) == False


# Detects negation mutation: `not ('push' in ...)` would flip result
def test_mutation_negation_on_push_check():
    cmd = make_command(
        ['git', 'push', 'origin'],
        "set-upstream"
    )
    # A correct implementation returns True when 'push' IS in parts
    assert match(cmd) == True


# Detects negation mutation: `not ('set-upstream' in ...)` would flip result
def test_mutation_negation_on_set_upstream_check():
    cmd = make_command(
        ['git', 'push'],
        "fatal: set-upstream needed"
    )
    # A correct implementation returns True when 'set-upstream' IS in output
    assert match(cmd) == True


# Detects constant error: wrong string literal e.g. 'push ' vs 'push'
def test_mutation_constant_push_with_trailing_space():
    cmd = make_command(
        ['git', 'push'],
        "set-upstream"
    )
    # The element in script_parts is exactly 'push' (no spaces); must still match
    assert match(cmd) == True


# Detects constant error: checking 'upstream' instead of 'set-upstream'
def test_mutation_constant_upstream_vs_set_upstream():
    cmd = make_command(
        ['git', 'push'],
        "upstream only, not set-upstream prefix"
    )
    # This output contains 'set-upstream' so correct impl returns True
    assert match(cmd) == True


# Detects constant error: checking 'upstream' instead of 'set-upstream'
# Output has 'upstream' but NOT 'set-upstream'
def test_mutation_constant_only_upstream_in_output():
    cmd = make_command(
        ['git', 'push'],
        "the upstream branch is missing"
    )
    # 'set-upstream' is NOT in output; a correct implementation returns False
    assert match(cmd) == False