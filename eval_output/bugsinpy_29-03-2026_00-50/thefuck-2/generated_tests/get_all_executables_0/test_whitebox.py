import os
import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from thefuck.utils import get_all_executables


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_exe(name, is_dir=False):
    """Return a mock path entry whose .name and .is_dir() behave correctly."""
    entry = MagicMock()
    entry.name = name
    entry.is_dir = MagicMock(return_value=is_dir)
    return entry


def _reset_memoize():
    """
    get_all_executables is decorated with @memoize.
    Clear its cache before every test so each test runs the real function.
    """
    try:
        get_all_executables.cache.clear()
    except AttributeError:
        pass
    # Some memoize implementations store the cache on _cache or similar names
    for attr in ('_cache', 'cache', '__cache__'):
        cache = getattr(get_all_executables, attr, None)
        if isinstance(cache, dict):
            cache.clear()


# ---------------------------------------------------------------------------
# Shared patch targets
# ---------------------------------------------------------------------------

PATCH_ALIAS   = 'thefuck.utils.get_alias'
PATCH_PATH    = 'thefuck.utils.Path'
PATCH_SHELL   = 'thefuck.shells.shell'
PATCH_ENVIRON = 'os.environ'


# ---------------------------------------------------------------------------
# Statement Coverage
# ---------------------------------------------------------------------------

class TestStatementCoverage:

    def setup_method(self):
        _reset_memoize()

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_basic_returns_list(self, mock_shell, mock_path_cls, mock_alias):
        """All main statements execute: alias fetch, PATH split, iterdir, is_dir, name."""
        exe_ls = _make_exe('ls', is_dir=False)
        exe_dir = _make_exe('somedir', is_dir=True)
        mock_path_cls.return_value.iterdir.return_value = [exe_ls, exe_dir]
        mock_shell.get_aliases.return_value = ['git', 'fuck']

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert isinstance(result, list)
        assert 'ls' in result          # normal executable is included
        assert 'somedir' not in result # directories are excluded
        assert 'fuck' not in result    # tf_entry_points excluded from bins
        assert 'thefuck' not in result # tf_entry_points excluded from bins
        # 'fuck' alias equals tf_alias so excluded; 'git' should be present
        assert 'git' in result

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_tf_entry_points_excluded_from_bins(self, mock_shell, mock_path_cls, mock_alias):
        """Executables named 'thefuck' or 'fuck' are excluded from bins."""
        exe_thefuck = _make_exe('thefuck', is_dir=False)
        exe_fuck    = _make_exe('fuck',    is_dir=False)
        exe_normal  = _make_exe('grep',    is_dir=False)
        mock_path_cls.return_value.iterdir.return_value = [exe_thefuck, exe_fuck, exe_normal]
        mock_shell.get_aliases.return_value = []

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert 'thefuck' not in result
        assert 'fuck' not in result
        assert 'grep' in result

    @patch('thefuck.utils.get_alias', return_value='tf')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_alias_equal_to_tf_alias_excluded(self, mock_shell, mock_path_cls, mock_alias):
        """An alias that matches tf_alias must be excluded from aliases list."""
        mock_path_cls.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = ['tf', 'git']

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert 'tf' not in result
        assert 'git' in result

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_empty_path_env_no_bins(self, mock_shell, mock_path_cls, mock_alias):
        """When PATH is empty string, split(':') yields [''], iterdir returns empty."""
        mock_path_cls.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = ['git']

        with patch.dict(os.environ, {'PATH': ''}, clear=False):
            result = get_all_executables()

        # No filesystem executables but aliases should be present
        assert 'git' in result

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_missing_path_env(self, mock_shell, mock_path_cls, mock_alias):
        """When PATH is not set, os.environ.get defaults to '' → no bins."""
        mock_path_cls.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = ['git']

        env_without_path = {k: v for k, v in os.environ.items() if k != 'PATH'}
        with patch.dict(os.environ, env_without_path, clear=True):
            result = get_all_executables()

        assert 'git' in result


# ---------------------------------------------------------------------------
# Block Coverage
# ---------------------------------------------------------------------------

class TestBlockCoverage:

    def setup_method(self):
        _reset_memoize()

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_iterdir_raises_oserror_fallback_empty(self, mock_shell, mock_path_cls, mock_alias):
        """
        _safe(fn, fallback): OSError branch → returns fallback [].
        The except block inside _safe is exercised here.
        """
        mock_path_cls.return_value.iterdir.side_effect = OSError("permission denied")
        mock_shell.get_aliases.return_value = ['git']

        with patch.dict(os.environ, {'PATH': '/restricted'}, clear=False):
            result = get_all_executables()

        # No bins due to OSError; aliases still work
        assert 'git' in result
        # Result is still a list (correct type)
        assert isinstance(result, list)

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_is_dir_raises_oserror_treated_as_dir(self, mock_shell, mock_path_cls, mock_alias):
        """
        _safe(exe.is_dir, True): OSError → fallback True → treated as directory → excluded.
        This exercises the fallback=True path of _safe.
        """
        exe = MagicMock()
        exe.name = 'mystery'
        exe.is_dir = MagicMock(side_effect=OSError("stat failed"))
        mock_path_cls.return_value.iterdir.return_value = [exe]
        mock_shell.get_aliases.return_value = []

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        # A correct implementation treats OSError on is_dir as directory (fallback True)
        assert 'mystery' not in result

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_multiple_path_entries(self, mock_shell, mock_path_cls, mock_alias):
        """Multiple PATH entries → iterdir called per entry; all blocks in loop execute."""
        exe_bin    = _make_exe('cat',  is_dir=False)
        exe_local  = _make_exe('brew', is_dir=False)

        def path_side_effect(p):
            m = MagicMock()
            if p == '/usr/bin':
                m.iterdir.return_value = [exe_bin]
            else:
                m.iterdir.return_value = [exe_local]
            return m

        mock_path_cls.side_effect = path_side_effect
        mock_shell.get_aliases.return_value = []

        with patch.dict(os.environ, {'PATH': '/usr/bin:/usr/local/bin'}, clear=False):
            result = get_all_executables()

        assert 'cat' in result
        assert 'brew' in result

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_directory_entry_excluded_block(self, mock_shell, mock_path_cls, mock_alias):
        """
        is_dir() == True branch: the entry is skipped.
        Ensures the not-_safe(exe.is_dir, True) False-branch block is entered.
        """
        exe_dir  = _make_exe('subdir', is_dir=True)
        exe_file = _make_exe('awk',    is_dir=False)
        mock_path_cls.return_value.iterdir.return_value = [exe_dir, exe_file]
        mock_shell.get_aliases.return_value = []

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert 'subdir' not in result
        assert 'awk' in result


# ---------------------------------------------------------------------------
# Condition Coverage
# ---------------------------------------------------------------------------

class TestConditionCoverage:

    def setup_method(self):
        _reset_memoize()

    # Condition: `not _safe(exe.is_dir, True) and exe.name not in tf_entry_points`

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_is_dir_false_name_not_in_entry_points(self, mock_shell, mock_path_cls, mock_alias):
        """
        # is_dir: False (not True → True), name not in tf_entry_points: True
        Both sub-conditions True → exe included.
        """
        exe = _make_exe('sed', is_dir=False)
        mock_path_cls.return_value.iterdir.return_value = [exe]
        mock_shell.get_aliases.return_value = []

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert 'sed' in result  # correct impl SHOULD include normal exe  # is_dir:False, entry_point:False

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_is_dir_true_short_circuits(self, mock_shell, mock_path_cls, mock_alias):
        """
        # is_dir: True (not True → False) → short-circuit, exe excluded
        """
        exe = _make_exe('subdir', is_dir=True)
        mock_path_cls.return_value.iterdir.return_value = [exe]
        mock_shell.get_aliases.return_value = []

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert 'subdir' not in result  # is_dir:True → excluded

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_is_dir_false_name_in_entry_points(self, mock_shell, mock_path_cls, mock_alias):
        """
        # is_dir: False (not True → True), name in tf_entry_points: True (not in → False)
        Second sub-condition False → exe excluded.
        """
        exe = _make_exe('thefuck', is_dir=False)
        mock_path_cls.return_value.iterdir.return_value = [exe]
        mock_shell.get_aliases.return_value = []

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert 'thefuck' not in result  # is_dir:False, entry_point:True → excluded

    # Condition: `alias != tf_alias`

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_alias_not_equal_to_tf_alias_included(self, mock_shell, mock_path_cls, mock_alias):
        """# alias != tf_alias: True → alias included"""
        mock_path_cls.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = ['git']

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert 'git' in result  # alias != tf_alias → True → included

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_alias_equal_to_tf_alias_excluded(self, mock_shell, mock_path_cls, mock_alias):
        """# alias != tf_alias: False → alias excluded"""
        mock_path_cls.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = ['fuck', 'ls']

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert 'fuck' not in result  # alias == tf_alias → False → excluded
        assert 'ls' in result


# ---------------------------------------------------------------------------
# Path Coverage
# ---------------------------------------------------------------------------

class TestPathCoverage:

    def setup_method(self):
        _reset_memoize()

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_path_no_path_dirs_no_aliases(self, mock_shell, mock_path_cls, mock_alias):
        """
        # path: PATH='' → zero PATH dirs, zero aliases → return []
        Zero-iteration path for both loops.
        """
        mock_path_cls.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = []

        env_without_path = {k: v for k, v in os.environ.items() if k != 'PATH'}
        with patch.dict(os.environ, env_without_path, clear=True):
            result = get_all_executables()

        assert isinstance(result, list)
        # A correct implementation returns empty list when nothing is available
        assert result == []

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_path_one_dir_one_exe_no_aliases(self, mock_shell, mock_path_cls, mock_alias):
        """
        # path: one PATH dir → one exe (not dir, not entry-point) → bins=[exe], aliases=[]
        One-iteration path for bin loop, zero-iteration for aliases.
        """
        exe = _make_exe('nano', is_dir=False)
        mock_path_cls.return_value.iterdir.return_value = [exe]
        mock_shell.get_aliases.return_value = []

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert result == ['nano']

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_path_multiple_dirs_mixed_exes_and_aliases(self, mock_shell, mock_path_cls, mock_alias):
        """
        # path: multiple PATH dirs, mix of files/dirs/entry-points, multiple aliases
        Multi-iteration path for both loops; exercises all filter branches.
        """
        exe_cat     = _make_exe('cat',     is_dir=False)
        exe_dir     = _make_exe('subdir',  is_dir=True)
        exe_thefuck = _make_exe('thefuck', is_dir=False)
        exe_vim     = _make_exe('vim',     is_dir=False)

        def path_side(p):
            m = MagicMock()
            if p == '/usr/bin':
                m.iterdir.return_value = [exe_cat, exe_dir, exe_thefuck]
            else:
                m.iterdir.return_value = [exe_vim]
            return m

        mock_path_cls.side_effect = path_side
        mock_shell.get_aliases.return_value = ['fuck', 'git', 'ls']

        with patch.dict(os.environ, {'PATH': '/usr/bin:/usr/local/bin'}, clear=False):
            result = get_all_executables()

        # Bins: cat, vim (subdir excluded as dir, thefuck excluded as entry-point)
        assert 'cat' in result
        assert 'vim' in result
        assert 'subdir' not in result
        assert 'thefuck' not in result
        # Aliases: git, ls (fuck == tf_alias excluded)
        assert 'git' in result
        assert 'ls' in result
        assert 'fuck' not in result
        # Total length check: bins=[cat,vim] + aliases=[git,ls] = 4
        assert len(result) == 4

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_path_iterdir_oserror_then_valid_dir(self, mock_shell, mock_path_cls, mock_alias):
        """
        # path: first PATH dir → OSError on iterdir (fallback []) →
        #       second PATH dir → valid exe
        # Exercises: _safe try-block (success) and _safe except-block (OSError).
        """
        exe_good = _make_exe('grep', is_dir=False)

        call_count = {'n': 0}

        def path_side(p):
            m = MagicMock()
            call_count['n'] += 1
            if call_count['n'] == 1:
                m.iterdir.side_effect = OSError("nope")
            else:
                m.iterdir.return_value = [exe_good]
            return m

        mock_path_cls.side_effect = path_side
        mock_shell.get_aliases.return_value = []

        with patch.dict(os.environ, {'PATH': '/no/access:/usr/bin'}, clear=False):
            result = get_all_executables()

        assert 'grep' in result

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_path_all_exes_are_dirs(self, mock_shell, mock_path_cls, mock_alias):
        """
        # path: one PATH dir → all entries are directories → bins=[]
        Loop body executes but every exe is filtered; aliases provide results.
        """
        exes = [_make_exe(f'dir{i}', is_dir=True) for i in range(3)]
        mock_path_cls.return_value.iterdir.return_value = exes
        mock_shell.get_aliases.return_value = ['git']

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        for i in range(3):
            assert f'dir{i}' not in result
        assert 'git' in result

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_path_bins_and_aliases_concatenated(self, mock_shell, mock_path_cls, mock_alias):
        """
        # path: bins + aliases concatenation preserved in result order.
        A correct implementation returns bins first, then aliases.
        """
        exe_cat = _make_exe('cat', is_dir=False)
        mock_path_cls.return_value.iterdir.return_value = [exe_cat]
        mock_shell.get_aliases.return_value = ['git']

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert result.index('cat') < result.index('git')

    @patch('thefuck.utils.get_alias', return_value='fuck')
    @patch('thefuck.utils.Path')
    @patch('thefuck.shells.shell')
    def test_path_no_bins_only_aliases(self, mock_shell, mock_path_cls, mock_alias):
        """
        # path: empty iterdir everywhere → bins=[], aliases=[git] → return ['git']
        Zero-iteration bin loop, one-iteration alias loop.
        """
        mock_path_cls.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = ['git']

        with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
            result = get_all_executables()

        assert result == ['git']