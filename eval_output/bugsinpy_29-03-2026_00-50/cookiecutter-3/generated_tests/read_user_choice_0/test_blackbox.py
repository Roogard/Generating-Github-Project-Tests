import pytest
from unittest.mock import patch
from cookiecutter.prompt import read_user_choice

# --- BVA ---

def test_bva_single_option_default_selected():
    """BVA: single-element list — boundary minimum valid collection size; user accepts default '1'."""
    options = ['only_option']
    with patch('click.prompt', return_value='1') as mock_prompt:
        result = read_user_choice('my_var', options)
    assert result == 'only_option'

def test_bva_two_options_first_selected():
    """BVA: two-element list, select first item."""
    options = ['alpha', 'beta']
    with patch('click.prompt', return_value='1'):
        result = read_user_choice('my_var', options)
    assert result == 'alpha'

def test_bva_two_options_last_selected():
    """BVA: two-element list, select last item (boundary max index)."""
    options = ['alpha', 'beta']
    with patch('click.prompt', return_value='2'):
        result = read_user_choice('my_var', options)
    assert result == 'beta'

def test_bva_large_list_first():
    """BVA: large list, select first item."""
    options = [str(i) for i in range(100)]
    with patch('click.prompt', return_value='1'):
        result = read_user_choice('var', options)
    assert result == '0'

def test_bva_large_list_last():
    """BVA: large list, select last item (index 100)."""
    options = [str(i) for i in range(100)]
    with patch('click.prompt', return_value='100'):
        result = read_user_choice('var', options)
    assert result == '99'

def test_bva_large_list_middle():
    """BVA: large list, select a middle item."""
    options = [str(i) for i in range(100)]
    with patch('click.prompt', return_value='50'):
        result = read_user_choice('var', options)
    assert result == '49'

def test_bva_empty_list_raises_value_error():
    """BVA: empty list — just below minimum valid size."""
    with pytest.raises(ValueError):
        read_user_choice('var', [])

# --- ECP ---

def test_ecp_valid_list_returns_chosen_option():
    """ECP: valid list, user selects a specific item — normal case."""
    options = ['opt_a', 'opt_b', 'opt_c']
    with patch('click.prompt', return_value='2'):
        result = read_user_choice('choice_var', options)
    assert result == 'opt_b'

def test_ecp_valid_list_default_is_first():
    """ECP: valid list, default selection (no user input) returns first option."""
    options = ['first', 'second', 'third']
    with patch('click.prompt', return_value='1') as mock_prompt:
        result = read_user_choice('var', options)
    # A correct implementation SHOULD return the first item when default '1' is used
    assert result == 'first'
    # Verify default was set to '1'
    call_kwargs = mock_prompt.call_args
    assert call_kwargs[1]['default'] == '1'

def test_ecp_invalid_not_a_list_tuple_raises():
    """ECP: invalid class — tuple instead of list."""
    with pytest.raises(TypeError):
        read_user_choice('var', ('a', 'b', 'c'))

def test_ecp_invalid_not_a_list_string_raises():
    """ECP: invalid class — string instead of list."""
    with pytest.raises(TypeError):
        read_user_choice('var', 'abc')

def test_ecp_invalid_not_a_list_dict_raises():
    """ECP: invalid class — dict instead of list."""
    with pytest.raises(TypeError):
        read_user_choice('var', {'a': 1})

def test_ecp_invalid_not_a_list_none_raises():
    """ECP: invalid class — None instead of list."""
    with pytest.raises(TypeError):
        read_user_choice('var', None)

def test_ecp_invalid_empty_list_raises():
    """ECP: invalid class — empty list raises ValueError."""
    with pytest.raises(ValueError):
        read_user_choice('var', [])

def test_ecp_options_with_mixed_types():
    """ECP: valid list with mixed-type items; selected item should be returned unchanged."""
    options = [42, 'string', None, 3.14]
    with patch('click.prompt', return_value='3'):
        result = read_user_choice('mixed', options)
    assert result is None

def test_ecp_options_with_unicode_strings():
    """ECP: valid list with unicode strings — should work normally."""
    options = [u'café', u'naïve', u'résumé']
    with patch('click.prompt', return_value='2'):
        result = read_user_choice('unicode_var', options)
    assert result == u'naïve'

def test_ecp_prompt_includes_var_name():
    """ECP: the prompt text SHOULD contain the variable name."""
    options = ['x', 'y']
    with patch('click.prompt', return_value='1') as mock_prompt:
        read_user_choice('my_special_var', options)
    prompt_text = mock_prompt.call_args[0][0]
    assert 'my_special_var' in prompt_text

def test_ecp_prompt_includes_all_options():
    """ECP: the prompt text SHOULD list all options."""
    options = ['apple', 'banana', 'cherry']
    with patch('click.prompt', return_value='1') as mock_prompt:
        read_user_choice('fruit', options)
    prompt_text = mock_prompt.call_args[0][0]
    assert 'apple' in prompt_text
    assert 'banana' in prompt_text
    assert 'cherry' in prompt_text

def test_ecp_prompt_choice_type_contains_all_keys():
    """ECP: the click.Choice passed to prompt SHOULD contain keys for all options."""
    options = ['a', 'b', 'c', 'd']
    with patch('click.prompt', return_value='1') as mock_prompt:
        read_user_choice('var', options)
    call_kwargs = mock_prompt.call_args[1]
    choice_type = call_kwargs['type']
    # The Choice type should contain '1' through '4'
    assert '1' in choice_type.choices
    assert '2' in choice_type.choices
    assert '3' in choice_type.choices
    assert '4' in choice_type.choices

def test_ecp_return_value_is_exact_option_not_key():
    """ECP: SHOULD return the actual option value, not the numeric key string."""
    options = ['cat', 'dog', 'bird']
    with patch('click.prompt', return_value='3'):
        result = read_user_choice('animal', options)
    assert result == 'bird'
    assert result != '3'

# --- Mutation Detection ---

def test_mutation_off_by_one_enumerate_starts_at_1():
    """Mutation: detect if enumerate starts at 0 instead of 1 (off-by-one in choice_map keys)."""
    options = ['first', 'second']
    with patch('click.prompt', return_value='1') as mock_prompt:
        result = read_user_choice('v', options)
    # A correct implementation enumerating from 1 SHOULD map '1' -> 'first'
    assert result == 'first', "choice_map must start enumeration at 1, not 0"

def test_mutation_off_by_one_second_item_key():
    """Mutation: detect if second item is mapped to '2', not '1' (enumerate start mutation)."""
    options = ['alpha', 'beta']
    with patch('click.prompt', return_value='2'):
        result = read_user_choice('v', options)
    assert result == 'beta', "second item SHOULD map to key '2'"

def test_mutation_default_is_string_one():
    """Mutation: detect if default was changed from '1' to something else (constant error)."""
    options = ['x', 'y', 'z']
    with patch('click.prompt', return_value='1') as mock_prompt:
        read_user_choice('v', options)
    default_used = mock_prompt.call_args[1]['default']
    assert default_used == u'1', "default SHOULD be string '1' to select first option"

def test_mutation_empty_check_not_negated():
    """Mutation: detect if 'not options' was written as 'options' (negation error)."""
    # A correct implementation SHOULD raise ValueError for empty list
    with pytest.raises(ValueError):
        read_user_choice('v', [])

def test_mutation_type_check_inverted():
    """Mutation: detect if isinstance check was inverted (negation error on type guard)."""
    # A correct implementation SHOULD raise TypeError for non-list
    with pytest.raises(TypeError):
        read_user_choice('v', ('a', 'b'))

def test_mutation_wrong_operator_type_check_uses_list_not_tuple():
    """Mutation: detect if isinstance(options, list) was changed to isinstance(options, tuple)."""
    # A tuple SHOULD raise TypeError in a correct implementation
    with pytest.raises(TypeError):
        read_user_choice('v', (1, 2, 3))
    # A list SHOULD NOT raise TypeError
    with patch('click.prompt', return_value='1'):
        result = read_user_choice('v', [1, 2, 3])
    assert result == 1

def test_mutation_choice_map_returns_wrong_variable():
    """Mutation: detect if choice_map[user_choice] returned user_choice (key) instead of value."""
    options = ['correct_value', 'other']
    with patch('click.prompt', return_value='1'):
        result = read_user_choice('v', options)
    # SHOULD return the option value, not the numeric string key
    assert result == 'correct_value'
    assert result != '1'

def test_mutation_prompt_choices_are_strings_not_ints():
    """Mutation: detect if keys were stored as int instead of formatted string."""
    options = ['a', 'b', 'c']
    with patch('click.prompt', return_value='1') as mock_prompt:
        read_user_choice('v', options)
    choice_type = mock_prompt.call_args[1]['type']
    # Keys SHOULD be strings ('1', '2', '3'), not integers (1, 2, 3)
    for key in choice_type.choices:
        assert isinstance(key, str), "choice keys SHOULD be strings"

def test_mutation_select_last_item_correct_index():
    """Mutation: detect off-by-one where last index is n-1 vs n."""
    options = ['a', 'b', 'c']
    with patch('click.prompt', return_value='3'):
        result = read_user_choice('v', options)
    # A correct implementation SHOULD map '3' to 'c' (last item)
    assert result == 'c'

def test_mutation_prompt_uses_choices_not_values_for_click_choice():
    """Mutation: detect if click.Choice received option values instead of numeric keys."""
    options = ['foo', 'bar']
    with patch('click.prompt', return_value='1') as mock_prompt:
        read_user_choice('v', options)
    choice_type = mock_prompt.call_args[1]['type']
    # SHOULD be numeric string keys, not option values
    assert '1' in choice_type.choices
    assert '2' in choice_type.choices
    # The option values should NOT be the choice keys
    assert 'foo' not in choice_type.choices
    assert 'bar' not in choice_type.choices