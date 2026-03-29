import os
import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from thefuck.utils import get_all_executables


# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

def _make_fake_path_entry(name, is_dir=False):
    """Return a mock object that behaves like a pathlib.Path directory entry."""
    entry = MagicMock()
    # .name must be a plain str (Python 3 path)
    entry.name = name
    entry.is_dir = MagicMock(return_value=is_dir)
    return entry


def _run(monkeypatch, path_env, path_entries_map, aliases, tf_alias='fuck'):
    """
    Drive get_all_executables() with fully controlled inputs.

    path_env          – string for os.environ['PATH']
    path_entries_map  – dict { path_component: [fake entries] }
    aliases           – list of alias strings returned by shell.get_aliases()
    tf_alias          – what get_alias() returns
    """
    # get_all_executables is memoized; clear cache before every call
    try:
        get_all_executables.cache_clear()          # if it uses functools.lru_cache
    except AttributeError:
        try:
            get_all_executables._cache.clear()     # thefuck's own memoize
        except AttributeError:
            pass

    def fake_path_iterdir(path_str):
        return path_entries_map.get(path_str, [])

    mock_shell = MagicMock()
    mock_shell.get_aliases.return_value = aliases

    with patch.dict(os.environ, {'PATH': path_env}, clear=False), \
         patch('thefuck.utils.get_alias', return_value=tf_alias), \
         patch('thefuck.utils.shell', mock_shell), \
         patch('thefuck.utils.Path') as MockPath:

        def path_side_effect(p):
            mock_p = MagicMock()
            mock_p.iterdir.return_value = fake_path_iterdir(p)
            return mock_p

        MockPath.side_effect = path_side_effect

        result = get_all_executables()
    return result


# ---------------------------------------------------------------------------
# Ensure cache is cleared between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_cache():
    """Always clear the memoize cache before each test."""
    try:
        get_all_executables.cache_clear()
    except AttributeError:
        pass
    try:
        get_all_executables._cache.clear()
    except AttributeError:
        pass
    yield
    try:
        get_all_executables.cache_clear()
    except AttributeError:
        pass
    try:
        get_all_executables._cache.clear()
    except AttributeError:
        pass


# ---------------------------------------------------------------------------
# --- BVA ---
# ---------------------------------------------------------------------------

class TestBVA:

    def test_empty_path_env(self):
        """BVA: PATH is empty string → no bins collected from filesystem."""
        result = _run(
            path_env='',
            path_entries_map={},
            aliases=[],
            tf_alias='fuck',
        )
        # With an empty PATH, split(':') gives [''], and no entries → only
        # aliases contribute; here aliases is also empty.
        assert isinstance(result, list)
        # No filesystem executables should be present.
        assert result == []

    def test_single_path_component_single_executable(self):
        """BVA: PATH with exactly one component containing exactly one file."""
        entry = _make_fake_path_entry('git', is_dir=False)
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': [entry]},
            aliases=[],
            tf_alias='fuck',
        )
        assert 'git' in result

    def test_single_path_component_single_directory_skipped(self):
        """BVA: single entry that is a directory must be excluded from bins."""
        entry = _make_fake_path_entry('somedir', is_dir=True)
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': [entry]},
            aliases=[],
            tf_alias='fuck',
        )
        assert 'somedir' not in result

    def test_path_component_with_no_entries(self):
        """BVA: a PATH component that yields an empty directory."""
        result = _run(
            path_env='/empty',
            path_entries_map={'/empty': []},
            aliases=[],
        )
        assert result == []

    def test_tf_entry_point_thefuck_excluded(self):
        """BVA: entry named 'thefuck' must never appear in the result."""
        entry = _make_fake_path_entry('thefuck', is_dir=False)
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': [entry]},
            aliases=[],
        )
        assert 'thefuck' not in result

    def test_tf_entry_point_fuck_excluded(self):
        """BVA: entry named 'fuck' must never appear in the result."""
        entry = _make_fake_path_entry('fuck', is_dir=False)
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': [entry]},
            aliases=[],
        )
        assert 'fuck' not in result

    def test_single_alias_equal_to_tf_alias_excluded(self):
        """BVA: the one alias returned equals tf_alias → must be excluded."""
        result = _run(
            path_env='',
            path_entries_map={},
            aliases=['fuck'],
            tf_alias='fuck',
        )
        assert 'fuck' not in result

    def test_single_alias_not_equal_to_tf_alias_included(self):
        """BVA: a single alias that is not the tf_alias must be included."""
        result = _run(
            path_env='',
            path_entries_map={},
            aliases=['ll'],
            tf_alias='fuck',
        )
        assert 'll' in result

    def test_large_number_of_executables(self):
        """BVA: many entries → result length should match number of valid entries."""
        entries = [_make_fake_path_entry(f'cmd{i}', is_dir=False) for i in range(500)]
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': entries},
            aliases=[],
        )
        assert len(result) == 500
        assert all(f'cmd{i}' in result for i in range(500))

    def test_path_with_multiple_components(self):
        """BVA: PATH has two components, each with one executable."""
        e1 = _make_fake_path_entry('ls', is_dir=False)
        e2 = _make_fake_path_entry('grep', is_dir=False)
        result = _run(
            path_env='/usr/bin:/bin',
            path_entries_map={'/usr/bin': [e1], '/bin': [e2]},
            aliases=[],
        )
        assert 'ls' in result
        assert 'grep' in result


# ---------------------------------------------------------------------------
# --- ECP ---
# ---------------------------------------------------------------------------

class TestECP:

    def test_valid_normal_executables_included(self):
        """ECP valid: regular files in PATH → all included in result."""
        entries = [_make_fake_path_entry(n) for n in ('curl', 'wget', 'ssh')]
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': entries},
            aliases=[],
        )
        assert 'curl' in result
        assert 'wget' in result
        assert 'ssh' in result

    def test_invalid_directories_excluded(self):
        """ECP invalid: directory entries in PATH must not appear in result."""
        entries = [_make_fake_path_entry('d', is_dir=True) for d in ('dir1', 'dir2')]
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': entries},
            aliases=[],
        )
        for entry in entries:
            assert entry.name not in result

    def test_valid_aliases_included(self):
        """ECP valid: aliases that are not the tf_alias appear in result."""
        aliases = ['gs', 'gst', 'gco']
        result = _run(
            path_env='',
            path_entries_map={},
            aliases=aliases,
            tf_alias='fuck',
        )
        for alias in aliases:
            assert alias in result

    def test_invalid_tf_alias_excluded_from_aliases(self):
        """ECP invalid: tf_alias inside alias list must be excluded."""
        result = _run(
            path_env='',
            path_entries_map={},
            aliases=['fuck', 'gs'],
            tf_alias='fuck',
        )
        assert 'fuck' not in result
        assert 'gs' in result

    def test_invalid_tf_entry_points_excluded_from_bins(self):
        """ECP invalid: 'thefuck' and 'fuck' entries in PATH never appear."""
        entries = [
            _make_fake_path_entry('thefuck', is_dir=False),
            _make_fake_path_entry('fuck', is_dir=False),
            _make_fake_path_entry('git', is_dir=False),
        ]
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': entries},
            aliases=[],
        )
        assert 'thefuck' not in result
        assert 'fuck' not in result
        assert 'git' in result

    def test_oserror_in_iterdir_returns_empty_fallback(self):
        """ECP invalid: OSError from iterdir → treated as empty; no crash."""
        mock_shell = MagicMock()
        mock_shell.get_aliases.return_value = []

        try:
            get_all_executables.cache_clear()
        except AttributeError:
            pass
        try:
            get_all_executables._cache.clear()
        except AttributeError:
            pass

        with patch.dict(os.environ, {'PATH': '/bad'}, clear=False), \
             patch('thefuck.utils.get_alias', return_value='fuck'), \
             patch('thefuck.utils.shell', mock_shell), \
             patch('thefuck.utils.Path') as MockPath:

            mock_p = MagicMock()
            mock_p.iterdir.side_effect = OSError("permission denied")
            MockPath.return_value = mock_p

            result = get_all_executables()

        assert isinstance(result, list)
        # No executables from the broken path; no crash.
        assert result == []

    def test_oserror_in_is_dir_treats_entry_as_dir(self):
        """ECP invalid: OSError from is_dir → fallback True → entry excluded."""
        entry = MagicMock()
        entry.name = 'mystery'
        entry.is_dir = MagicMock(side_effect=OSError("no access"))

        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': [entry]},
            aliases=[],
        )
        # Fallback is True (treat as directory) → must be excluded.
        assert 'mystery' not in result

    def test_combined_bins_and_aliases(self):
        """ECP valid: result is concatenation of valid bins then valid aliases."""
        entry = _make_fake_path_entry('curl', is_dir=False)
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': [entry]},
            aliases=['ll', 'la'],
            tf_alias='fuck',
        )
        assert 'curl' in result
        assert 'll' in result
        assert 'la' in result
        # bins come before aliases per the implementation spec
        curl_idx = result.index('curl')
        ll_idx = result.index('ll')
        assert curl_idx < ll_idx

    def test_no_path_env_variable(self):
        """ECP: PATH not set at all → treated as empty string."""
        env = os.environ.copy()
        env.pop('PATH', None)

        mock_shell = MagicMock()
        mock_shell.get_aliases.return_value = []

        try:
            get_all_executables.cache_clear()
        except AttributeError:
            pass
        try:
            get_all_executables._cache.clear()
        except AttributeError:
            pass

        with patch.dict(os.environ, env, clear=True), \
             patch('thefuck.utils.get_alias', return_value='fuck'), \
             patch('thefuck.utils.shell', mock_shell), \
             patch('thefuck.utils.Path') as MockPath:

            mock_p = MagicMock()
            mock_p.iterdir.return_value = []
            MockPath.return_value = mock_p

            result = get_all_executables()

        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# --- Mutation Detection ---
# ---------------------------------------------------------------------------

class TestMutationDetection:

    def test_not_dir_condition_is_dir_false_included(self):
        """
        Mutation: `not _safe(exe.is_dir, True)` flipped to `_safe(exe.is_dir, True)`.
        A file (is_dir=False) MUST be included; a dir (is_dir=True) MUST be excluded.
        """
        file_entry = _make_fake_path_entry('file_exe', is_dir=False)
        dir_entry = _make_fake_path_entry('dir_exe', is_dir=True)
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': [file_entry, dir_entry]},
            aliases=[],
        )
        assert 'file_exe' in result      # correct: not is_dir → include
        assert 'dir_exe' not in result   # correct: is_dir → exclude

    def test_tf_entry_points_exact_match_not_substring(self):
        """
        Mutation: `not in` changed to `in` (inverted guard).
        Only 'thefuck' and 'fuck' exactly should be excluded, not others containing them.
        """
        entry = _make_fake_path_entry('thefuck2', is_dir=False)
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': [entry]},
            aliases=[],
        )
        # 'thefuck2' is NOT in tf_entry_points → must be included
        assert 'thefuck2' in result

    def test_alias_exclusion_exact_match(self):
        """
        Mutation: `alias != tf_alias` changed to `alias == tf_alias` (include only tf_alias).
        All aliases that are NOT the tf_alias must be present.
        """
        result = _run(
            path_env='',
            path_entries_map={},
            aliases=['myfuck', 'fuckme', 'fuck'],
            tf_alias='fuck',
        )
        # Correct: only 'fuck' (the tf_alias) is excluded
        assert 'myfuck' in result
        assert 'fuckme' in result
        assert 'fuck' not in result

    def test_bins_before_aliases_ordering(self):
        """
        Mutation: `bins + aliases` changed to `aliases + bins`.
        A correct implementation returns bins first, then aliases.
        """
        entry = _make_fake_path_entry('zzz_bin', is_dir=False)
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': [entry]},
            aliases=['aaa_alias'],
            tf_alias='fuck',
        )
        bin_idx = result.index('zzz_bin')
        alias_idx = result.index('aaa_alias')
        assert bin_idx < alias_idx  # bins come before aliases

    def test_all_elements_present_no_duplication_or_loss(self):
        """
        Mutation: off-by-one in list comprehension losing last element.
        Total count must equal valid bins + valid aliases.
        """
        entries = [_make_fake_path_entry(f'exe{i}', is_dir=False) for i in range(10)]
        aliases = [f'alias{i}' for i in range(5)]
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': entries},
            aliases=aliases,
            tf_alias='fuck',
        )
        assert len(result) == 15

    def test_oserror_fallback_true_excludes_entry(self):
        """
        Mutation: fallback changed from True to False in `_safe(exe.is_dir, True)`.
        When is_dir raises OSError, the fallback must be True (exclude the entry).
        """
        entry = MagicMock()
        entry.name = 'ambiguous'
        entry.is_dir = MagicMock(side_effect=OSError("fail"))
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': [entry]},
            aliases=[],
        )
        # Correct fallback is True → treated as dir → excluded
        assert 'ambiguous' not in result

    def test_path_split_on_colon(self):
        """
        Mutation: PATH split character changed from ':' to ';' or ' '.
        Correct implementation must split on ':'.
        """
        e1 = _make_fake_path_entry('git', is_dir=False)
        e2 = _make_fake_path_entry('curl', is_dir=False)
        result = _run(
            path_env='/usr/bin:/bin',
            path_entries_map={'/usr/bin': [e1], '/bin': [e2]},
            aliases=[],
        )
        assert 'git' in result
        assert 'curl' in result

    def test_tf_alias_exclusion_not_all_aliases(self):
        """
        Mutation: filter `alias != tf_alias` dropped entirely (include everything).
        The tf_alias must NOT appear in the result even when present in alias list.
        """
        tf_alias = 'fuck'
        all_aliases = [tf_alias, 'gs', 'gco']
        result = _run(
            path_env='',
            path_entries_map={},
            aliases=all_aliases,
            tf_alias=tf_alias,
        )
        assert tf_alias not in result
        assert 'gs' in result
        assert 'gco' in result

    def test_both_thefuck_and_fuck_excluded_independently(self):
        """
        Mutation: tf_entry_points list contains only one of the two names.
        Both 'thefuck' and 'fuck' must be excluded regardless of order.
        """
        entries = [
            _make_fake_path_entry('thefuck', is_dir=False),
            _make_fake_path_entry('fuck', is_dir=False),
        ]
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': entries},
            aliases=[],
            tf_alias='something_else',
        )
        assert 'thefuck' not in result
        assert 'fuck' not in result

    def test_is_dir_check_uses_entry_not_wrong_variable(self):
        """
        Mutation: wrong variable used in is_dir check (e.g., always same entry).
        Each entry's own is_dir must be consulted individually.
        """
        file1 = _make_fake_path_entry('file1', is_dir=False)
        dir1 = _make_fake_path_entry('dir1', is_dir=True)
        file2 = _make_fake_path_entry('file2', is_dir=False)
        result = _run(
            path_env='/usr/bin',
            path_entries_map={'/usr/bin': [file1, dir1, file2]},
            aliases=[],
        )
        assert 'file1' in result
        assert 'dir1' not in result
        assert 'file2' in result