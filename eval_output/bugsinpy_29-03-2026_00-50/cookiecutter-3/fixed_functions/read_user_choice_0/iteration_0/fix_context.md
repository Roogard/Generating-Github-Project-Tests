## Root Cause Diagnosis

Root Cause: The test file imports `read_user_choice` from `cookiecutter.prompt` but does not import `click` directly. When the test tries to use `click.Choice([])` on line 164 to verify the type of the choice argument passed to the mock, `click` is not defined in the test's namespace, causing a `NameError`.

Suggestion 1: Add `import click` to the test file
Add `import click` at the top of `test_whitebox.py` alongside the other imports. This makes `click.Choice` accessible in the test that checks `isinstance(choice_type, type(click.Choice([])))`.

Suggestion 2: Replace `click.Choice` reference with the string class name
Instead of using `click.Choice([])` to get the type, import `click` or reference the class differently — for example, check `type(choice_type).__name__ == "Choice"` — so that `click` does not need to be explicitly imported in the test file.

## Trigger Test(s)

```python
# test_whitebox.py
from unittest.mock import patch
from collections import OrderedDict
import pytest

from cookiecutter.prompt import read_user_choice


# --- Statement Coverage ---

def test_raises_type_error_for_non_list():
    # Covers: isinstance check branch (not a list) → raise TypeError
    # path: isinstance-false → raise TypeError
    # condition: isinstance(options, list): False
    with pytest.raises(TypeError):
        read_user_choice("framework", "not_a_list")


def test_raises_value_error_for_empty_list():
    # Covers: empty list check → raise ValueError
    # path: isinstance-true → empty-true → raise ValueError
    # condition: isinstance(options, list): True, not options: True
    with pytest.raises(ValueError):
        read_user_choice("framework", [])


def test_returns_first_option_on_default_input():
    # Covers: normal flow — choice_map built, prompt called, result returned
    # path: isinstance-true → empty-false → build map → prompt → return
    # condition: isinstance(options, list): True, not options: False
    # The first item is the default; user selecting '1' must return options[0]
    options = ["django", "flask", "pyramid"]
    with patch("click.prompt", return_value="1") as mock_prompt:
        result = read_user_choice("framework", options)
    assert result == "django"


def test_returns_correct_option_for_non_default_choice():
    # Covers: user selecting a non-default choice key
    # path: isinstance-true → empty-false → build map → prompt → return
    options = ["django", "flask", "pyramid"]
    with patch("click.prompt", return_value="2"):
        result = read_user_choice("framework", options)
    assert result == "flask"


# --- Block Coverage ---

# Block: TypeError branch — covered by test_raises_type_error_for_non_list
# Block: ValueError branch — covered by test_raises_value_error_for_empty_list
# Block: normal execution path — covered by test_returns_first_option_on_default_input

def test_single_option_list():
    # Covers the normal block with exactly one option
    # path: isinstance-true → empty-false (one item) → build map → prompt → return
    options = ["only_choice"]
    with patch("click.prompt", return_value="1"):
        result = read_user_choice("db", options)
    assert result == "only_choice"


def test_last_option_selected():
    # Covers picking the last key in the OrderedDict
    options = ["a", "b", "c", "d"]
    with patch("click.prompt", return_value="4"):
        result = read_user_choice("letter", options)
    assert result == "d"


# --- Condition Coverage ---

def test_condition_isinstance_false():
    # isinstance(options, list): False
    # A correct read_user_choice SHOULD raise TypeError when options is a tuple
    with pytest.raises(TypeError):
        read_user_choice("x", ("a", "b"))


def test_condition_isinstance_true_and_nonempty():
    # isinstance(options, list): True, not options: False
    options = ["opt1"]
    with patch("click.prompt", return_value="1"):
        result = read_user_choice("x", options)
    assert result == "opt1"


def test_condition_isinstance_true_and_empty():
    # isinstance(options, list): True, not options: True
    with pytest.raises(ValueError):
        read_user_choice("x", [])


def test_condition_isinstance_false_with_dict():
    # isinstance(options, list): False (dict passed)
    with pytest.raises(TypeError):
        read_user_choice("x", {"a": 1})


def test_condition_isinstance_false_with_none():
    # isinstance(options, list): False (None passed)
    with pytest.raises(TypeError):
        read_user_choice("x", None)


# --- Path Coverage ---

def test_path_non_list_raises_type_error():
    # path: entry → isinstance-false → raise TypeError → exit
    with pytest.raises(TypeError):
        read_user_choice("var", 42)


def test_path_empty_list_raises_value_error():
    # path: entry → isinstance-true → not options: True → raise ValueError → exit
    with pytest.raises(ValueError):
        read_user_choice("var", [])


def test_path_single_item_default_selection():
    # path: entry → isinstance-true → not options: False →
    #        build map (1 item) → prompt → return choice_map['1'] → exit
    options = ["solo"]
    with patch("click.prompt", return_value="1"):
        result = read_user_choice("pick", options)
    assert result == "solo"


def test_path_multiple_items_first_selected():
    # path: entry → isinstance-true → not options: False →
    #        build map (N items) → prompt returns '1' → return options[0] → exit
    options = ["alpha", "beta", "gamma"]
    with patch("click.prompt", return_value="1"):
        result = read_user_choice("greek", options)
    assert result == "alpha"


def test_path_multiple_items_middle_selected():
    # path: entry → isinstance-true → not options: False →
    #        build map (N items) → prompt returns '2' → return options[1] → exit
    options = ["alpha", "beta", "gamma"]
    with patch("click.prompt", return_value="2"):
        result = read_user_choice("greek", options)
    assert result == "beta"


def test_path_multiple_items_last_selected():
    # path: entry → isinstance-true → not options: False →
    #        build map (N items) → prompt returns 'N' → return options[-1] → exit
    options = ["alpha", "beta", "gamma"]
    with patch("click.prompt", return_value="3"):
        result = read_user_choice("greek", options)
    assert result == "gamma"


def test_prompt_receives_correct_choices_and_default():
    # Verifies the prompt is constructed with correct choices and default='1'
    options = ["x", "y", "z"]
    with patch("click.prompt", return_value="1") as mock_prompt:
        read_user_choice("var", options)
    call_kwargs = mock_prompt.call_args
    # default must be '1'
    assert call_kwargs[1]["default"] == "1"
    # The click.Choice must contain the string keys '1', '2', '3'
    choice_type = call_kwargs[1]["type"]
    assert isinstance(choice_type, type(click.Choice([])))


def test_choice_map_keys_are_one_indexed():
    # A correct implementation SHOULD index options starting from 1
    options = ["first", "second"]
    with patch("click.prompt", return_value="2"):
        result = read_user_choice("myvar", options)
    # key '2' corresponds to the second element
    assert result == "second"


def test_result_is_element_of_options():
    # Property: result must always be one of the provided options
    options = ["opt_a", "opt_b", "opt_c"]
    for key in ["1", "2", "3"]:
        with patch("click.prompt", return_value=key):
            result = read_user_choice("myvar", options)
        assert result in options


def test_prompt_text_contains_var_name():
    # Property: the prompt string passed to click.prompt must mention the var_name
    options = ["one", "two"]
    with patch("click.prompt", return_value="1") as mock_prompt:
        read_user_choice("myspecialvar", options)
    prompt_text = mock_prompt.call_args[0][0]
    assert "myspecialvar" in prompt_text


def test_prompt_text_contains_all_options():
    # Property: the prompt must display all available options
    options = ["django", "flask"]
    with patch("click.prompt", return_value="1") as mock_prompt:
        read_user_choice("framework", options)
    prompt_text = mock_prompt.call_args[0][0]
    assert "django" in prompt_text
    assert "flask" in prompt_text
```
