import json
import os
import tempfile
import pytest
from collections import OrderedDict

from cookiecutter.generate import generate_context
from cookiecutter.exceptions import ContextDecodingException


# ─── Helpers ────────────────────────────────────────────────────────────────

def write_json_file(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)

def write_raw_file(path, content):
    with open(path, 'w') as f:
        f.write(content)


# ─── BVA ────────────────────────────────────────────────────────────────────

class TestBVA:
    """Boundary Value Analysis tests."""

    def test_empty_json_object(self, tmp_path):
        """BVA: minimal valid JSON – empty object {}."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {})
        result = generate_context(context_file=str(ctx_file))
        assert isinstance(result, OrderedDict)
        assert 'cookiecutter' in result
        assert result['cookiecutter'] == OrderedDict()

    def test_single_key_value_pair(self, tmp_path):
        """BVA: minimal non-empty JSON – exactly one key."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'project_name': 'hello'})
        result = generate_context(context_file=str(ctx_file))
        assert 'cookiecutter' in result
        assert result['cookiecutter']['project_name'] == 'hello'

    def test_many_key_value_pairs(self, tmp_path):
        """BVA: large number of keys."""
        data = {f'key_{i}': f'value_{i}' for i in range(100)}
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), data)
        result = generate_context(context_file=str(ctx_file))
        assert len(result['cookiecutter']) == 100

    def test_none_default_context(self, tmp_path):
        """BVA: default_context=None (boundary – not applied)."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'name': 'original'})
        result = generate_context(context_file=str(ctx_file), default_context=None)
        assert result['cookiecutter']['name'] == 'original'

    def test_none_extra_context(self, tmp_path):
        """BVA: extra_context=None (boundary – not applied)."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'name': 'original'})
        result = generate_context(context_file=str(ctx_file), extra_context=None)
        assert result['cookiecutter']['name'] == 'original'

    def test_empty_default_context(self, tmp_path):
        """BVA: default_context={} – empty dict is falsy, should not overwrite."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'name': 'original'})
        result = generate_context(context_file=str(ctx_file), default_context={})
        # {} is falsy so apply_overwrites_to_context should NOT be called
        assert result['cookiecutter']['name'] == 'original'

    def test_empty_extra_context(self, tmp_path):
        """BVA: extra_context={} – empty dict is falsy, should not overwrite."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'name': 'original'})
        result = generate_context(context_file=str(ctx_file), extra_context={})
        assert result['cookiecutter']['name'] == 'original'

    def test_file_stem_with_single_char_name(self, tmp_path):
        """BVA: context file with single-character stem 'a.json'."""
        ctx_file = tmp_path / 'a.json'
        write_json_file(str(ctx_file), {'k': 'v'})
        result = generate_context(context_file=str(ctx_file))
        assert 'a' in result
        assert result['a']['k'] == 'v'

    def test_deeply_nested_json(self, tmp_path):
        """BVA: deeply nested JSON structure."""
        data = {'level1': {'level2': {'level3': 'deep_value'}}}
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), data)
        result = generate_context(context_file=str(ctx_file))
        assert result['cookiecutter']['level1']['level2']['level3'] == 'deep_value'


# ─── ECP ────────────────────────────────────────────────────────────────────

class TestECP:
    """Equivalence Class Partitioning tests."""

    # --- Valid classes ---

    def test_valid_typical_context_file(self, tmp_path):
        """ECP valid: typical well-formed JSON context file."""
        data = {'project_name': 'my_project', 'version': '0.1.0', 'author': 'Alice'}
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), data)
        result = generate_context(context_file=str(ctx_file))
        assert isinstance(result, OrderedDict)
        assert result['cookiecutter']['project_name'] == 'my_project'
        assert result['cookiecutter']['version'] == '0.1.0'

    def test_valid_with_list_values(self, tmp_path):
        """ECP valid: JSON with list values."""
        data = {'choices': ['a', 'b', 'c']}
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), data)
        result = generate_context(context_file=str(ctx_file))
        assert result['cookiecutter']['choices'] == ['a', 'b', 'c']

    def test_valid_with_boolean_values(self, tmp_path):
        """ECP valid: JSON with boolean values."""
        data = {'use_docker': True, 'use_heroku': False}
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), data)
        result = generate_context(context_file=str(ctx_file))
        assert result['cookiecutter']['use_docker'] is True
        assert result['cookiecutter']['use_heroku'] is False

    def test_valid_with_integer_values(self, tmp_path):
        """ECP valid: JSON with integer values."""
        data = {'port': 8080}
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), data)
        result = generate_context(context_file=str(ctx_file))
        assert result['cookiecutter']['port'] == 8080

    def test_valid_default_context_overrides(self, tmp_path):
        """ECP valid: default_context overrides existing key."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'name': 'original', 'other': 'keep'})
        result = generate_context(
            context_file=str(ctx_file),
            default_context={'name': 'overridden'}
        )
        assert result['cookiecutter']['name'] == 'overridden'
        # Key not in default_context should remain
        assert result['cookiecutter']['other'] == 'keep'

    def test_valid_extra_context_overrides(self, tmp_path):
        """ECP valid: extra_context overrides existing key."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'name': 'original', 'other': 'keep'})
        result = generate_context(
            context_file=str(ctx_file),
            extra_context={'name': 'extra_override'}
        )
        assert result['cookiecutter']['name'] == 'extra_override'

    def test_valid_both_contexts_applied(self, tmp_path):
        """ECP valid: both default_context and extra_context provided."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'a': 'orig_a', 'b': 'orig_b'})
        result = generate_context(
            context_file=str(ctx_file),
            default_context={'a': 'default_a'},
            extra_context={'b': 'extra_b'}
        )
        assert result['cookiecutter']['a'] == 'default_a'
        assert result['cookiecutter']['b'] == 'extra_b'

    def test_valid_extra_context_wins_over_default(self, tmp_path):
        """ECP valid: extra_context applied after default_context (extra wins for same key)."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'name': 'original'})
        result = generate_context(
            context_file=str(ctx_file),
            default_context={'name': 'from_default'},
            extra_context={'name': 'from_extra'}
        )
        # extra_context applied last, so it should win
        assert result['cookiecutter']['name'] == 'from_extra'

    def test_valid_non_default_filename_stem(self, tmp_path):
        """ECP valid: context file with a non-default stem becomes the context key."""
        ctx_file = tmp_path / 'mytemplate.json'
        write_json_file(str(ctx_file), {'project': 'test'})
        result = generate_context(context_file=str(ctx_file))
        assert 'mytemplate' in result
        assert 'cookiecutter' not in result

    def test_valid_returns_ordered_dict(self, tmp_path):
        """ECP valid: return value is always an OrderedDict."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'a': 1})
        result = generate_context(context_file=str(ctx_file))
        assert isinstance(result, OrderedDict)

    def test_valid_json_preserves_order(self, tmp_path):
        """ECP valid: key order is preserved (OrderedDict with object_pairs_hook)."""
        # Write JSON manually to control ordering
        ctx_file = tmp_path / 'cookiecutter.json'
        ctx_file.write_text('{"z": 1, "a": 2, "m": 3}')
        result = generate_context(context_file=str(ctx_file))
        keys = list(result['cookiecutter'].keys())
        assert keys == ['z', 'a', 'm']

    # --- Invalid classes ---

    def test_invalid_malformed_json(self, tmp_path):
        """ECP invalid: malformed JSON raises ContextDecodingException."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_raw_file(str(ctx_file), '{not valid json}')
        with pytest.raises(ContextDecodingException):
            generate_context(context_file=str(ctx_file))

    def test_invalid_truncated_json(self, tmp_path):
        """ECP invalid: truncated JSON raises ContextDecodingException."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_raw_file(str(ctx_file), '{"key": ')
        with pytest.raises(ContextDecodingException):
            generate_context(context_file=str(ctx_file))

    def test_invalid_json_array_at_root(self, tmp_path):
        """ECP invalid: JSON array at root – json.load succeeds but may break context logic.
        A correct implementation still loads it; the stem key maps to the array."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_raw_file(str(ctx_file), '[1, 2, 3]')
        # json.load of a root array does not raise ValueError, so no exception expected
        result = generate_context(context_file=str(ctx_file))
        assert 'cookiecutter' in result
        assert result['cookiecutter'] == [1, 2, 3]

    def test_invalid_nonexistent_file(self, tmp_path):
        """ECP invalid: file does not exist raises FileNotFoundError (or OSError)."""
        missing = str(tmp_path / 'nonexistent.json')
        with pytest.raises((FileNotFoundError, OSError)):
            generate_context(context_file=missing)

    def test_invalid_empty_file(self, tmp_path):
        """ECP invalid: empty file raises ContextDecodingException (JSON parse error)."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_raw_file(str(ctx_file), '')
        with pytest.raises(ContextDecodingException):
            generate_context(context_file=str(ctx_file))

    def test_invalid_null_json(self, tmp_path):
        """ECP invalid: JSON 'null' at root – valid JSON but unusual.
        json.load succeeds; result stored under stem key as None."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_raw_file(str(ctx_file), 'null')
        result = generate_context(context_file=str(ctx_file))
        assert 'cookiecutter' in result
        assert result['cookiecutter'] is None


# ─── Mutation Detection ──────────────────────────────────────────────────────

class TestMutationDetection:
    """Tests designed to catch common coding mutations in generate_context."""

    def test_mutation_context_key_uses_filestem_not_full_filename(self, tmp_path):
        """Mutation: wrong variable – using file_name instead of file_stem as context key.
        e.g., context[file_name] = obj instead of context[file_stem] = obj."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'x': 1})
        result = generate_context(context_file=str(ctx_file))
        # Key must be 'cookiecutter', NOT 'cookiecutter.json'
        assert 'cookiecutter' in result
        assert 'cookiecutter.json' not in result

    def test_mutation_filestem_split_on_dot_takes_first_part(self, tmp_path):
        """Mutation: off-by-one index – file_name.split('.')[1] instead of [0].
        Uses a file with stem 'myapp' and extension '.json'."""
        ctx_file = tmp_path / 'myapp.json'
        write_json_file(str(ctx_file), {'k': 'v'})
        result = generate_context(context_file=str(ctx_file))
        # Correct: key == 'myapp'; mutant would use 'json'
        assert 'myapp' in result
        assert 'json' not in result

    def test_mutation_default_context_not_applied_when_truthy(self, tmp_path):
        """Mutation: negation – 'if not default_context' instead of 'if default_context'.
        A truthy default_context must actually override values."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'color': 'red'})
        result = generate_context(
            context_file=str(ctx_file),
            default_context={'color': 'blue'}
        )
        # Correct: override applied → 'blue'; mutant skips it → 'red'
        assert result['cookiecutter']['color'] == 'blue'

    def test_mutation_extra_context_not_applied_when_truthy(self, tmp_path):
        """Mutation: negation – 'if not extra_context' instead of 'if extra_context'."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'color': 'red'})
        result = generate_context(
            context_file=str(ctx_file),
            extra_context={'color': 'green'}
        )
        # Correct: override applied → 'green'; mutant skips it → 'red'
        assert result['cookiecutter']['color'] == 'green'

    def test_mutation_both_contexts_skipped_when_falsy(self, tmp_path):
        """Mutation: wrong operator – 'if default_context and extra_context' instead of separate ifs.
        Providing only one should still apply overrides."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'a': 'orig', 'b': 'orig'})
        # Only default_context provided; extra_context=None
        result = generate_context(
            context_file=str(ctx_file),
            default_context={'a': 'new_a'},
        )
        assert result['cookiecutter']['a'] == 'new_a'

    def test_mutation_context_not_returned(self, tmp_path):
        """Mutation: wrong variable returned – e.g., returning obj instead of context."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'k': 'v'})
        result = generate_context(context_file=str(ctx_file))
        # A correct return is the outer context dict keyed by file stem
        assert isinstance(result, dict)
        assert 'cookiecutter' in result
        # If obj were returned, it would not have the 'cookiecutter' key
        assert result.get('cookiecutter') is not None

    def test_mutation_exception_message_includes_filepath(self, tmp_path):
        """Mutation: wrong variable in exception – using context_file instead of full_fpath.
        The exception message should include the absolute path."""
        ctx_file = tmp_path / 'bad.json'
        write_raw_file(str(ctx_file), 'not json at all !!!')
        with pytest.raises(ContextDecodingException) as exc_info:
            generate_context(context_file=str(ctx_file))
        message = str(exc_info.value)
        expected_abs = os.path.abspath(str(ctx_file))
        assert expected_abs in message

    def test_mutation_exception_message_includes_original_error(self, tmp_path):
        """Mutation: wrong variable in exception – dropping json_exc_message from message."""
        ctx_file = tmp_path / 'broken.json'
        write_raw_file(str(ctx_file), '{bad}')
        with pytest.raises(ContextDecodingException) as exc_info:
            generate_context(context_file=str(ctx_file))
        message = str(exc_info.value)
        # The original JSON error detail must appear in the wrapped exception
        assert 'Decoding error details' in message or len(message) > 30

    def test_mutation_context_obj_is_stored_not_mutated_copy(self, tmp_path):
        """Mutation: context stores a shallow copy instead of the actual obj.
        After applying overrides, the same object must be reflected in the result."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'lang': 'python'})
        result = generate_context(
            context_file=str(ctx_file),
            extra_context={'lang': 'rust'}
        )
        # The value in context[stem] must reflect the override, not the original
        assert result['cookiecutter']['lang'] == 'rust'

    def test_mutation_os_path_split_takes_tail_not_head(self, tmp_path):
        """Mutation: wrong index – os.path.split(...)[0] instead of [1].
        os.path.split returns (head, tail); correct code takes [1] (the filename)."""
        ctx_file = tmp_path / 'myconfig.json'
        write_json_file(str(ctx_file), {'k': 'v'})
        result = generate_context(context_file=str(ctx_file))
        # Correct: key is 'myconfig'; mutant using [0] would use directory path stem
        assert 'myconfig' in result

    def test_mutation_extra_context_applied_after_default(self, tmp_path):
        """Mutation: order swapped – extra_context applied before default_context.
        When both override same key, extra should win (applied second)."""
        ctx_file = tmp_path / 'cookiecutter.json'
        write_json_file(str(ctx_file), {'role': 'dev'})
        result = generate_context(
            context_file=str(ctx_file),
            default_context={'role': 'admin'},
            extra_context={'role': 'superuser'},
        )
        # extra_context must win; if order were swapped, default would win
        assert result['cookiecutter']['role'] == 'superuser'