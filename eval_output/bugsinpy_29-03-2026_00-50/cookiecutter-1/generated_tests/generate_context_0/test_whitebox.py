import json
import os
import pytest
from collections import OrderedDict
from unittest.mock import patch, MagicMock
from cookiecutter.generate import generate_context
from cookiecutter.exceptions import ContextDecodingException


# --- Helpers ---

def write_json_file(tmp_path, filename, data):
    """Write a JSON file and return its path."""
    filepath = tmp_path / filename
    filepath.write_text(json.dumps(data))
    return str(filepath)


def write_invalid_json_file(tmp_path, filename):
    """Write an invalid JSON file and return its path."""
    filepath = tmp_path / filename
    filepath.write_text("{invalid json content}")
    return str(filepath)


# --- Statement Coverage ---
# Ensures every executable statement is reached at least once.

def test_statement_basic_load(tmp_path):
    # path: open file → json.load succeeds → no default_context → no extra_context → return context
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"project_name": "myproject"})
    result = generate_context(context_file=filepath)
    assert isinstance(result, OrderedDict)
    assert "cookiecutter" in result
    assert result["cookiecutter"]["project_name"] == "myproject"


def test_statement_json_decoding_exception(tmp_path):
    # Reaches the except ValueError block and raises ContextDecodingException
    filepath = write_invalid_json_file(tmp_path, "cookiecutter.json")
    with pytest.raises(ContextDecodingException) as exc_info:
        generate_context(context_file=filepath)
    assert "JSON decoding error" in str(exc_info.value)
    assert "cookiecutter.json" in str(exc_info.value)


def test_statement_with_default_context(tmp_path):
    # Reaches `if default_context:` branch (True)
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"project_name": "original"})
    with patch("cookiecutter.generate.apply_overwrites_to_context") as mock_apply:
        result = generate_context(
            context_file=filepath,
            default_context={"project_name": "overridden"},
        )
    mock_apply.assert_called_once()
    assert isinstance(result, OrderedDict)


def test_statement_with_extra_context(tmp_path):
    # Reaches `if extra_context:` branch (True)
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"project_name": "original"})
    with patch("cookiecutter.generate.apply_overwrites_to_context") as mock_apply:
        result = generate_context(
            context_file=filepath,
            extra_context={"project_name": "extra"},
        )
    mock_apply.assert_called_once()
    assert isinstance(result, OrderedDict)


def test_statement_file_stem_extraction(tmp_path):
    # Verifies os.path.split and split('.') statements produce correct file_stem
    filepath = write_json_file(tmp_path, "mytemplate.json", {"key": "value"})
    result = generate_context(context_file=filepath)
    assert "mytemplate" in result
    assert result["mytemplate"]["key"] == "value"


# --- Block Coverage ---
# Ensures every basic block (entry, branch bodies, except handler) is executed.

def test_block_success_no_overrides(tmp_path):
    # Block: function entry → open file → json.load → file_name/stem computation
    #        → default_context block skipped → extra_context block skipped → return
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"a": 1})
    result = generate_context(context_file=filepath)
    assert result["cookiecutter"] == OrderedDict([("a", 1)])


def test_block_except_handler(tmp_path):
    # Block: except ValueError → build full_fpath, json_exc_message, our_exc_message → raise
    filepath = write_invalid_json_file(tmp_path, "cookiecutter.json")
    with pytest.raises(ContextDecodingException) as exc_info:
        generate_context(context_file=filepath)
    full_path = os.path.abspath(filepath)
    assert full_path in str(exc_info.value)


def test_block_default_context_branch(tmp_path):
    # Block: if default_context is truthy → apply_overwrites_to_context(obj, default_context)
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"name": "test"})
    call_args_list = []
    def fake_apply(obj, context):
        call_args_list.append((obj, context))
    with patch("cookiecutter.generate.apply_overwrites_to_context", side_effect=fake_apply):
        generate_context(
            context_file=filepath,
            default_context={"name": "default_override"},
        )
    assert len(call_args_list) == 1
    assert call_args_list[0][1] == {"name": "default_override"}


def test_block_extra_context_branch(tmp_path):
    # Block: if extra_context is truthy → apply_overwrites_to_context(obj, extra_context)
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"name": "test"})
    call_args_list = []
    def fake_apply(obj, context):
        call_args_list.append((obj, context))
    with patch("cookiecutter.generate.apply_overwrites_to_context", side_effect=fake_apply):
        generate_context(
            context_file=filepath,
            extra_context={"name": "extra_override"},
        )
    assert len(call_args_list) == 1
    assert call_args_list[0][1] == {"name": "extra_override"}


def test_block_both_overrides(tmp_path):
    # Block: both default_context and extra_context truthy → apply_overwrites called twice
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"name": "test"})
    call_args_list = []
    def fake_apply(obj, context):
        call_args_list.append((obj, context))
    with patch("cookiecutter.generate.apply_overwrites_to_context", side_effect=fake_apply):
        generate_context(
            context_file=filepath,
            default_context={"name": "default"},
            extra_context={"name": "extra"},
        )
    assert len(call_args_list) == 2


def test_block_neither_override(tmp_path):
    # Block: both default_context and extra_context falsy → apply_overwrites never called
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"name": "test"})
    with patch("cookiecutter.generate.apply_overwrites_to_context") as mock_apply:
        generate_context(context_file=filepath)
    mock_apply.assert_not_called()


# --- Condition Coverage ---
# Each boolean sub-expression in each condition must be True in some test and False in another.

# Condition: `if default_context:`
#   default_context: True  → test_condition_default_context_truthy
#   default_context: False → test_condition_default_context_falsy

def test_condition_default_context_truthy(tmp_path):
    # default_context: True (non-empty dict is truthy)
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"x": 1})
    with patch("cookiecutter.generate.apply_overwrites_to_context") as mock_apply:
        generate_context(context_file=filepath, default_context={"x": 99})
    mock_apply.assert_called()


def test_condition_default_context_falsy_none(tmp_path):
    # default_context: False (None is falsy)
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"x": 1})
    with patch("cookiecutter.generate.apply_overwrites_to_context") as mock_apply:
        generate_context(context_file=filepath, default_context=None)
    # apply_overwrites should not have been called for the default_context branch
    # (it may still be called zero or one time based on extra_context, which is also None)
    mock_apply.assert_not_called()


def test_condition_default_context_falsy_empty(tmp_path):
    # default_context: False (empty dict is falsy)
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"x": 1})
    with patch("cookiecutter.generate.apply_overwrites_to_context") as mock_apply:
        generate_context(context_file=filepath, default_context={})
    mock_apply.assert_not_called()


# Condition: `if extra_context:`
#   extra_context: True  → test_condition_extra_context_truthy
#   extra_context: False → test_condition_extra_context_falsy

def test_condition_extra_context_truthy(tmp_path):
    # extra_context: True (non-empty dict is truthy)
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"y": 2})
    with patch("cookiecutter.generate.apply_overwrites_to_context") as mock_apply:
        generate_context(context_file=filepath, extra_context={"y": 99})
    mock_apply.assert_called()


def test_condition_extra_context_falsy_none(tmp_path):
    # extra_context: False (None is falsy)
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"y": 2})
    with patch("cookiecutter.generate.apply_overwrites_to_context") as mock_apply:
        generate_context(context_file=filepath, extra_context=None)
    mock_apply.assert_not_called()


def test_condition_extra_context_falsy_empty(tmp_path):
    # extra_context: False (empty dict is falsy)
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"y": 2})
    with patch("cookiecutter.generate.apply_overwrites_to_context") as mock_apply:
        generate_context(context_file=filepath, extra_context={})
    mock_apply.assert_not_called()


# --- Path Coverage ---
# Exercises all distinct entry-to-exit routes.

def test_path_success_no_overrides(tmp_path):
    # path: open→load OK → file_stem → default_context=False → extra_context=False → return
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"key": "val"})
    result = generate_context(context_file=filepath)
    # A correct generate_context SHOULD return an OrderedDict keyed by file stem
    assert isinstance(result, OrderedDict)
    assert "cookiecutter" in result
    assert result["cookiecutter"]["key"] == "val"


def test_path_success_default_context_only(tmp_path):
    # path: open→load OK → file_stem → default_context=True → extra_context=False → return
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"key": "val"})
    call_log = []
    def fake_apply(obj, ctx):
        call_log.append(ctx)
    with patch("cookiecutter.generate.apply_overwrites_to_context", side_effect=fake_apply):
        result = generate_context(
            context_file=filepath,
            default_context={"key": "default_val"},
        )
    assert len(call_log) == 1
    assert call_log[0] == {"key": "default_val"}
    assert isinstance(result, OrderedDict)


def test_path_success_extra_context_only(tmp_path):
    # path: open→load OK → file_stem → default_context=False → extra_context=True → return
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"key": "val"})
    call_log = []
    def fake_apply(obj, ctx):
        call_log.append(ctx)
    with patch("cookiecutter.generate.apply_overwrites_to_context", side_effect=fake_apply):
        result = generate_context(
            context_file=filepath,
            extra_context={"key": "extra_val"},
        )
    assert len(call_log) == 1
    assert call_log[0] == {"key": "extra_val"}
    assert isinstance(result, OrderedDict)


def test_path_success_both_overrides(tmp_path):
    # path: open→load OK → file_stem → default_context=True → extra_context=True → return
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"key": "val"})
    call_log = []
    def fake_apply(obj, ctx):
        call_log.append(ctx)
    with patch("cookiecutter.generate.apply_overwrites_to_context", side_effect=fake_apply):
        result = generate_context(
            context_file=filepath,
            default_context={"key": "default_val"},
            extra_context={"key": "extra_val"},
        )
    assert len(call_log) == 2
    # default_context is applied first, then extra_context
    assert call_log[0] == {"key": "default_val"}
    assert call_log[1] == {"key": "extra_val"}
    assert isinstance(result, OrderedDict)


def test_path_json_decode_error_raises(tmp_path):
    # path: open→load raises ValueError → build message → raise ContextDecodingException
    filepath = write_invalid_json_file(tmp_path, "cookiecutter.json")
    with pytest.raises(ContextDecodingException) as exc_info:
        generate_context(context_file=filepath)
    # A correct implementation SHOULD include absolute path and error details in message
    assert os.path.abspath(filepath) in str(exc_info.value)
    assert "Decoding error details" in str(exc_info.value)


def test_path_preserves_key_ordering(tmp_path):
    # A correct generate_context SHOULD preserve insertion order via OrderedDict
    data = OrderedDict([("z_key", 1), ("a_key", 2), ("m_key", 3)])
    filepath = str(tmp_path / "cookiecutter.json")
    with open(filepath, "w") as f:
        json.dump(data, f)
    result = generate_context(context_file=filepath)
    keys = list(result["cookiecutter"].keys())
    assert keys == ["z_key", "a_key", "m_key"]


def test_path_nested_json_structure(tmp_path):
    # A correct generate_context SHOULD handle nested JSON objects
    nested = {"outer": {"inner": "value"}, "list_key": [1, 2, 3]}
    filepath = write_json_file(tmp_path, "cookiecutter.json", nested)
    result = generate_context(context_file=filepath)
    assert result["cookiecutter"]["outer"]["inner"] == "value"
    assert result["cookiecutter"]["list_key"] == [1, 2, 3]


def test_path_exception_message_contains_filename(tmp_path):
    # A correct implementation SHOULD embed both absolute path and original JSON error
    filepath = write_invalid_json_file(tmp_path, "my_template.json")
    with pytest.raises(ContextDecodingException) as exc_info:
        generate_context(context_file=filepath)
    message = str(exc_info.value)
    assert "my_template.json" in message


def test_path_default_context_file_parameter(tmp_path):
    # A correct generate_context SHOULD use 'cookiecutter.json' as default file name stem
    filepath = write_json_file(tmp_path, "cookiecutter.json", {"hello": "world"})
    result = generate_context(context_file=filepath)
    # stem of 'cookiecutter.json' SHOULD be 'cookiecutter'
    assert "cookiecutter" in result
    assert result["cookiecutter"]["hello"] == "world"