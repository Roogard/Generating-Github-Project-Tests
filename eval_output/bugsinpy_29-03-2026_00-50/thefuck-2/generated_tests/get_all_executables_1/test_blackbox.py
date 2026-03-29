import os
import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from thefuck.utils import get_all_executables


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_file(name, is_dir=False):
    """Return a mock that looks like a pathlib.Path directory entry."""
    entry = MagicMock()
    entry.name = name
    entry.is_dir = MagicMock(return_value=is_dir)
    return entry


# ---------------------------------------------------------------------------
# BVA – Boundary Value Analysis
# ---------------------------------------------------------------------------

class TestBVA:

    def test_empty_path_env(self):
        """BVA: PATH is empty string → no path segments → bins should be empty."""
        with patch.dict(os.environ, {'PATH': ''}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.shell') as mock_shell:
                    mock_shell.get_aliases.return_value = []
                    result = get_all_executables()
        # bins come from PATH dirs; with empty PATH we expect only aliases portion
        assert isinstance(result, list)

    def test_path_with_single_directory_single_executable(self):
        """BVA: PATH has exactly one directory with exactly one non-dir file."""
        exe = _make_fake_file('git')
        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [exe]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert 'git' in result

    def test_path_with_single_directory_no_executables(self):
        """BVA: PATH has one directory that is empty → bins == []."""
        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = []
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert result == []

    def test_no_path_env_var_at_all(self):
        """BVA: PATH not set at all → os.environ.get returns '' → no bins."""
        env = {k: v for k, v in os.environ.items() if k != 'PATH'}
        with patch.dict(os.environ, env, clear=True):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.shell') as mock_shell:
                    mock_shell.get_aliases.return_value = []
                    result = get_all_executables()
        assert isinstance(result, list)

    def test_aliases_empty_list(self):
        """BVA: shell returns no aliases → result contains only bins."""
        exe = _make_fake_file('ls')
        with patch.dict(os.environ, {'PATH': '/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [exe]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert 'ls' in result

    def test_aliases_single_element(self):
        """BVA: exactly one alias that is not tf_alias."""
        with patch.dict(os.environ, {'PATH': ''}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.shell') as mock_shell:
                    mock_shell.get_aliases.return_value = ['ll']
                    result = get_all_executables()
        assert 'll' in result

    def test_large_number_of_executables(self):
        """BVA: PATH contains many files → all should appear (minus dirs/tf entries)."""
        exes = [_make_fake_file(f'cmd{i}') for i in range(200)]
        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = exes
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert len(result) == 200
        assert 'cmd0' in result
        assert 'cmd199' in result


# ---------------------------------------------------------------------------
# ECP – Equivalence Class Partitioning
# ---------------------------------------------------------------------------

class TestECP:

    def test_valid_normal_executables_returned(self):
        """ECP valid: normal executables that are not tf entry points are included."""
        exe = _make_fake_file('grep')
        with patch.dict(os.environ, {'PATH': '/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [exe]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert 'grep' in result

    def test_tf_entry_point_thefuck_excluded(self):
        """ECP invalid class: 'thefuck' binary must always be excluded from bins."""
        exe = _make_fake_file('thefuck')
        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [exe]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert 'thefuck' not in result

    def test_tf_entry_point_fuck_excluded(self):
        """ECP invalid class: 'fuck' binary must always be excluded from bins."""
        exe = _make_fake_file('fuck')
        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [exe]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert 'fuck' not in result

    def test_directory_entries_excluded_from_bins(self):
        """ECP: directory entries inside PATH dirs must not appear in result."""
        dir_entry = _make_fake_file('some_dir', is_dir=True)
        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [dir_entry]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert 'some_dir' not in result

    def test_tf_alias_excluded_from_aliases(self):
        """ECP: alias equal to tf_alias must be excluded from aliases list."""
        with patch.dict(os.environ, {'PATH': ''}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='my_alias'):
                with patch('thefuck.utils.shell') as mock_shell:
                    mock_shell.get_aliases.return_value = ['my_alias', 'll']
                    result = get_all_executables()
        assert 'my_alias' not in result
        assert 'll' in result

    def test_non_tf_alias_included(self):
        """ECP: alias that does not match tf_alias is included."""
        with patch.dict(os.environ, {'PATH': ''}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.shell') as mock_shell:
                    mock_shell.get_aliases.return_value = ['gs', 'gl']
                    result = get_all_executables()
        assert 'gs' in result
        assert 'gl' in result

    def test_result_is_bins_plus_aliases_concatenated(self):
        """ECP: result is bins first, then aliases (order property)."""
        exe = _make_fake_file('awk')
        with patch.dict(os.environ, {'PATH': '/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [exe]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = ['my_alias']
                        result = get_all_executables()
        # bins come before aliases
        assert result.index('awk') < result.index('my_alias')

    def test_oserror_from_iterdir_is_handled_gracefully(self):
        """ECP: OSError when iterating a PATH directory → treated as empty dir."""
        with patch.dict(os.environ, {'PATH': '/nonexistent'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.side_effect = OSError('no such dir')
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        # Should not raise
                        result = get_all_executables()
        assert isinstance(result, list)

    def test_oserror_from_is_dir_defaults_to_excluded(self):
        """ECP: OSError from is_dir → fallback True → entry treated as dir, excluded."""
        entry = MagicMock()
        entry.name = 'maybe_file'
        entry.is_dir = MagicMock(side_effect=OSError('permission denied'))
        with patch.dict(os.environ, {'PATH': '/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [entry]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        # When is_dir raises OSError, _safe returns True (fallback), so entry excluded
        assert 'maybe_file' not in result

    def test_multiple_path_directories_all_scanned(self):
        """ECP: multiple directories in PATH → executables from each are collected."""
        exe1 = _make_fake_file('curl')
        exe2 = _make_fake_file('wget')

        def fake_path(p):
            m = MagicMock()
            if p == '/usr/bin':
                m.iterdir.return_value = [exe1]
            else:
                m.iterdir.return_value = [exe2]
            return m

        with patch.dict(os.environ, {'PATH': '/usr/bin:/usr/local/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path', side_effect=fake_path):
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert 'curl' in result
        assert 'wget' in result

    def test_return_type_is_always_list(self):
        """ECP: regardless of inputs the return type must be list."""
        with patch.dict(os.environ, {'PATH': ''}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.shell') as mock_shell:
                    mock_shell.get_aliases.return_value = []
                    result = get_all_executables()
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Mutation Detection
# ---------------------------------------------------------------------------

class TestMutationDetection:

    def test_mutation_not_is_dir_check_negation(self):
        """Mutation: `not _safe(exe.is_dir, True)` negation flipped.
        A correct implementation MUST exclude entries where is_dir() returns True.
        If `not` were removed, directories would be included instead of files."""
        file_entry = _make_fake_file('real_exe', is_dir=False)
        dir_entry = _make_fake_file('a_directory', is_dir=True)
        with patch.dict(os.environ, {'PATH': '/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [file_entry, dir_entry]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert 'real_exe' in result      # files ARE included
        assert 'a_directory' not in result  # dirs are NOT included

    def test_mutation_tf_entry_points_list_thefuck_removed(self):
        """Mutation: tf_entry_points missing 'thefuck' → 'thefuck' binary would appear.
        A correct implementation MUST exclude 'thefuck' from bins."""
        exe = _make_fake_file('thefuck')
        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [exe]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert 'thefuck' not in result

    def test_mutation_tf_entry_points_list_fuck_removed(self):
        """Mutation: tf_entry_points missing 'fuck' → 'fuck' binary would appear.
        A correct implementation MUST exclude 'fuck' from bins."""
        exe = _make_fake_file('fuck')
        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [exe]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert 'fuck' not in result

    def test_mutation_alias_filter_uses_wrong_variable(self):
        """Mutation: `alias != tf_alias` replaced by `alias != tf_entry_points[0]`.
        A correct implementation MUST use tf_alias (from get_alias()) to filter,
        not a hardcoded string. Here tf_alias differs from 'thefuck'."""
        with patch.dict(os.environ, {'PATH': ''}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='custom_alias'):
                with patch('thefuck.utils.shell') as mock_shell:
                    mock_shell.get_aliases.return_value = ['custom_alias', 'safe_alias']
                    result = get_all_executables()
        # 'custom_alias' must be filtered; 'safe_alias' must remain
        assert 'custom_alias' not in result
        assert 'safe_alias' in result

    def test_mutation_path_split_wrong_separator(self):
        """Mutation: PATH split on ';' instead of ':' → whole PATH treated as one dir.
        A correct implementation MUST split on ':' so both dirs are visited."""
        exe1 = _make_fake_file('sed')
        exe2 = _make_fake_file('awk')

        call_args = []

        def fake_path(p):
            call_args.append(p)
            m = MagicMock()
            if p == '/usr/bin':
                m.iterdir.return_value = [exe1]
            elif p == '/bin':
                m.iterdir.return_value = [exe2]
            else:
                m.iterdir.return_value = []
            return m

        with patch.dict(os.environ, {'PATH': '/usr/bin:/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path', side_effect=fake_path):
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        # A correct implementation splitting on ':' gives exactly 2 path segments
        assert '/usr/bin' in call_args
        assert '/bin' in call_args
        assert 'sed' in result
        assert 'awk' in result

    def test_mutation_bins_and_aliases_not_concatenated(self):
        """Mutation: returning only bins or only aliases.
        A correct implementation MUST return bins + aliases combined."""
        exe = _make_fake_file('vim')
        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [exe]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = ['my_alias']
                        result = get_all_executables()
        assert 'vim' in result
        assert 'my_alias' in result

    def test_mutation_fallback_for_iterdir_wrong_value(self):
        """Mutation: fallback for _safe(iterdir) changed from [] to None.
        A correct implementation uses [] as fallback so iteration is safe."""
        with patch.dict(os.environ, {'PATH': '/bad'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.side_effect = OSError
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        # Must not raise TypeError (iterating None)
                        result = get_all_executables()
        assert isinstance(result, list)

    def test_mutation_is_dir_fallback_wrong_value_false(self):
        """Mutation: _safe(exe.is_dir, True) fallback changed to False.
        If fallback were False, a broken is_dir() would cause the entry to be
        INCLUDED (not excluded). A correct impl uses True so erroring entries
        are safely excluded."""
        entry = MagicMock()
        entry.name = 'suspicious'
        entry.is_dir = MagicMock(side_effect=OSError)
        with patch.dict(os.environ, {'PATH': '/bin'}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='fuck'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [entry]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        # With correct fallback=True, the entry is excluded (treated as dir)
        assert 'suspicious' not in result

    def test_mutation_get_alias_not_called(self):
        """Mutation: tf_alias set to a constant ('fuck') instead of get_alias().
        A correct implementation calls get_alias() so the real alias is filtered."""
        with patch.dict(os.environ, {'PATH': ''}, clear=False):
            with patch('thefuck.utils.get_alias', return_value='myfuck') as mock_ga:
                with patch('thefuck.utils.shell') as mock_shell:
                    mock_shell.get_aliases.return_value = ['myfuck', 'other']
                    result = get_all_executables()
            mock_ga.assert_called_once()
        assert 'myfuck' not in result
        assert 'other' in result

    def test_mutation_name_not_in_checks_wrong_collection(self):
        """Mutation: checking `exe.name not in [tf_alias]` instead of tf_entry_points.
        Both 'thefuck' and 'fuck' must be excluded regardless of tf_alias value."""
        thefuck_exe = _make_fake_file('thefuck')
        fuck_exe = _make_fake_file('fuck')
        safe_exe = _make_fake_file('git')
        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            # tf_alias is something unrelated
            with patch('thefuck.utils.get_alias', return_value='f'):
                with patch('thefuck.utils.Path') as MockPath:
                    MockPath.return_value.iterdir.return_value = [
                        thefuck_exe, fuck_exe, safe_exe
                    ]
                    with patch('thefuck.utils.shell') as mock_shell:
                        mock_shell.get_aliases.return_value = []
                        result = get_all_executables()
        assert 'thefuck' not in result
        assert 'fuck' not in result
        assert 'git' in result