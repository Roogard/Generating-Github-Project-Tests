import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from thefuck.utils import get_all_executables


# ---------------------------------------------------------------------------
# Helpers / Shared Fixtures
# ---------------------------------------------------------------------------

def _make_fake_exe(name, is_dir=False):
    """Return a mock Path entry whose .name and .is_dir() behave correctly."""
    entry = MagicMock()
    entry.name = name
    entry.is_dir.return_value = is_dir
    return entry


# ---------------------------------------------------------------------------
# Statement Coverage
# ---------------------------------------------------------------------------

# st-1  Happy path: at least one real PATH dir with one executable, one alias.
# Covers: tf_alias lookup, bins list-comp, aliases list-comp, return.
def test_statement_bins_and_aliases_returned():
    fake_exe = _make_fake_exe('ls')
    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = [fake_exe]
        mock_shell.get_aliases.return_value = ['git', 'fuck']

        result = get_all_executables()

        # A correct implementation must return a list
        assert isinstance(result, list)
        # 'ls' is a real executable and must appear
        assert 'ls' in result
        # 'git' is an alias != tf_alias, must appear
        assert 'git' in result
        # tf_alias 'fuck' must NOT appear in aliases section
        assert result.count('fuck') == result.count('fuck')  # property: checked below
        # the tf entry points must not be included as bins
        assert 'thefuck' not in result
        assert 'fuck' not in result  # excluded from both bins and aliases


# st-2  OSError from iterdir() triggers the fallback path (returns []).
def test_statement_oserror_on_iterdir_uses_fallback():
    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': '/bad/path'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.side_effect = OSError('no such dir')
        mock_shell.get_aliases.return_value = []

        result = get_all_executables()
        # A correct implementation must not raise and must return a list
        assert isinstance(result, list)


# st-3  tf_entry_points exclusion: entries named 'thefuck' or 'fuck' are dropped.
def test_statement_tf_entry_points_excluded_from_bins():
    fake_thefuck = _make_fake_exe('thefuck')
    fake_fuck = _make_fake_exe('fuck')
    fake_ls = _make_fake_exe('ls')

    with patch('thefuck.utils.get_alias', return_value='tf'), \
         patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = [fake_thefuck, fake_fuck, fake_ls]
        mock_shell.get_aliases.return_value = []

        result = get_all_executables()
        assert 'thefuck' not in result
        assert 'fuck' not in result
        assert 'ls' in result


# ---------------------------------------------------------------------------
# Block Coverage
# ---------------------------------------------------------------------------

# bl-1  _safe returns fn() result (no exception block entered).
#        Covered by test_statement_bins_and_aliases_returned above.

# bl-2  _safe except-block entered (OSError raised).
#        Covered by test_statement_oserror_on_iterdir_uses_fallback above.

# bl-3  Directory entry filtered out (is_dir returns True).
def test_block_directory_entries_are_filtered():
    fake_dir = _make_fake_exe('somedir', is_dir=True)
    fake_exe = _make_fake_exe('grep')

    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = [fake_dir, fake_exe]
        mock_shell.get_aliases.return_value = []

        result = get_all_executables()
        assert 'somedir' not in result
        assert 'grep' in result


# bl-4  OSError from exe.is_dir() uses fallback True (treats as directory → filtered).
def test_block_oserror_on_is_dir_treated_as_directory():
    bad_entry = MagicMock()
    bad_entry.name = 'mystery'
    bad_entry.is_dir.side_effect = OSError('permission denied')

    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = [bad_entry]
        mock_shell.get_aliases.return_value = []

        result = get_all_executables()
        # When is_dir raises OSError, fallback=True means entry is treated as
        # a directory and must be excluded from a correct implementation.
        assert 'mystery' not in result


# bl-5  Empty PATH variable → bins list is empty.
def test_block_empty_path_env():
    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': ''}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = ['mkalias']

        result = get_all_executables()
        assert 'mkalias' in result


# bl-6  PATH env var not set at all → os.environ.get defaults to ''.
def test_block_path_env_missing():
    env = {k: v for k, v in os.environ.items() if k != 'PATH'}
    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, env, clear=True), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = []

        result = get_all_executables()
        assert result == []


# ---------------------------------------------------------------------------
# Condition Coverage
# ---------------------------------------------------------------------------

# Each condition in the bins list-comp:
#   C1: not _safe(exe.is_dir, True)   — True when is_dir returns False (include)
#                                      — False when is_dir returns True (exclude)
#   C2: exe.name not in tf_entry_points — True when name is not a tf entry point
#                                        — False when name IS a tf entry point

# cc-1  C1=True (not a dir), C2=True (not a tf entry point) → included
def test_condition_not_dir_and_not_entry_point_included():
    # C1: not is_dir → True   C2: name not in tf_entry_points → True
    fake_exe = _make_fake_exe('awk')

    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': '/bin'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = [fake_exe]
        mock_shell.get_aliases.return_value = []

        result = get_all_executables()
        assert 'awk' in result  # C1:True, C2:True


# cc-2  C1=False (is a dir) → excluded regardless of C2
def test_condition_is_dir_excluded():
    # C1: not is_dir → False  (is_dir returns True) → entry excluded
    fake_dir = _make_fake_exe('mydir', is_dir=True)

    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': '/bin'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = [fake_dir]
        mock_shell.get_aliases.return_value = []

        result = get_all_executables()
        assert 'mydir' not in result  # C1:False


# cc-3  C1=True (not a dir), C2=False (name IS a tf entry point) → excluded
def test_condition_tf_entry_point_excluded_even_if_not_dir():
    # C1: not is_dir → True   C2: name not in tf_entry_points → False
    fake_thefuck = _make_fake_exe('thefuck')  # is_dir=False by default

    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': '/bin'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = [fake_thefuck]
        mock_shell.get_aliases.return_value = []

        result = get_all_executables()
        assert 'thefuck' not in result  # C2:False


# Condition in aliases list-comp:
#   C3: alias != tf_alias  — True when alias is not the tf alias (include)
#                           — False when alias IS the tf alias (exclude)

# cc-4  C3=True: alias retained
def test_condition_alias_not_tf_alias_included():
    # C3: alias != tf_alias → True
    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': ''}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = ['ll', 'la']

        result = get_all_executables()
        assert 'll' in result  # C3:True
        assert 'la' in result  # C3:True


# cc-5  C3=False: tf_alias itself is excluded
def test_condition_tf_alias_excluded_from_aliases():
    # C3: alias != tf_alias → False for 'fuck'
    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': ''}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = ['fuck', 'git']

        result = get_all_executables()
        assert 'fuck' not in result  # C3:False for 'fuck'
        assert 'git' in result       # C3:True for 'git'


# ---------------------------------------------------------------------------
# Path Coverage
# ---------------------------------------------------------------------------

# path-1: PATH='' → bins loop executes ZERO times; empty aliases → return []
# path: entry → bins-loop(0 iters) → aliases-loop(0 iters) → return []
def test_path_no_path_no_aliases():
    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': ''}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = []
        mock_shell.get_aliases.return_value = []

        result = get_all_executables()
        assert result == []
        # path: bins-loop(0 iters) → aliases-loop(0 iters) → return []


# path-2: ONE PATH segment with ONE valid exe; no aliases.
# path: entry → bins-loop(1 path, 1 exe, not-dir, not-entry-point) → aliases-loop(0) → return
def test_path_one_dir_one_exe_no_aliases():
    fake_exe = _make_fake_exe('cat')

    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': '/bin'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = [fake_exe]
        mock_shell.get_aliases.return_value = []

        result = get_all_executables()
        assert result == ['cat']
        # path: bins-loop(1 path, 1 valid exe) → aliases-loop(0 iters) → return


# path-3: MULTIPLE PATH segments; some iterdir raise OSError; valid exes + aliases.
# path: entry → bins-loop(multi paths, OSError fallback + valid) → aliases-loop(multi) → return
def test_path_multiple_path_segments_with_oserror_and_aliases():
    fake_exe1 = _make_fake_exe('sed')
    fake_exe2 = _make_fake_exe('awk')
    call_count = {'n': 0}

    def iterdir_side_effect():
        call_count['n'] += 1
        if call_count['n'] == 1:
            raise OSError('no access')
        return [fake_exe1, fake_exe2]

    with patch('thefuck.utils.get_alias', return_value='tf'), \
         patch.dict(os.environ, {'PATH': '/bad:/good'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.side_effect = iterdir_side_effect
        mock_shell.get_aliases.return_value = ['git', 'tf', 'ls']

        result = get_all_executables()
        # path: first segment raises OSError (fallback=[]) → second segment valid
        assert 'sed' in result
        assert 'awk' in result
        # tf alias excluded
        assert 'tf' not in result
        # other aliases retained
        assert 'git' in result
        assert 'ls' in result
        # length property: bins(2) + aliases(2) = 4
        assert len(result) == 4
        # path: bins-loop(2 paths: OSError then valid) → aliases-loop(3 items, 1 excluded) → return


# path-4: Exe IS a directory → filtered out. Only dirs in PATH segment.
# path: entry → bins-loop(1 path, dirs only → all filtered) → aliases-loop(0) → return []
def test_path_all_dirs_no_executables():
    dirs = [_make_fake_exe('bin', is_dir=True),
            _make_fake_exe('lib', is_dir=True)]

    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': '/usr'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = dirs
        mock_shell.get_aliases.return_value = []

        result = get_all_executables()
        assert result == []
        # path: bins-loop(1 path, all entries are dirs → filtered) → aliases-loop(0) → return []


# path-5: Mix of tf_entry_points, dirs, and valid exes; all aliases are tf_alias.
# Verifies the two independent filter conditions interact correctly.
def test_path_mixed_entries_only_valid_ones_returned():
    entries = [
        _make_fake_exe('thefuck'),        # excluded: tf entry point
        _make_fake_exe('fuck'),           # excluded: tf entry point
        _make_fake_exe('sbin', is_dir=True),  # excluded: directory
        _make_fake_exe('curl'),           # INCLUDED
    ]

    with patch('thefuck.utils.get_alias', return_value='tf'), \
         patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = entries
        mock_shell.get_aliases.return_value = ['tf']  # all excluded

        result = get_all_executables()
        assert result == ['curl']
        # path: bins-loop filters tf-entry-points and dirs → aliases-loop excludes tf_alias → return


# path-6: result = bins + aliases (concatenation order matters)
def test_path_bins_precede_aliases_in_result():
    fake_exe = _make_fake_exe('sed')

    with patch('thefuck.utils.get_alias', return_value='fuck'), \
         patch.dict(os.environ, {'PATH': '/bin'}, clear=False), \
         patch('thefuck.utils.Path') as MockPath, \
         patch('thefuck.utils.shell') as mock_shell:

        MockPath.return_value.iterdir.return_value = [fake_exe]
        mock_shell.get_aliases.return_value = ['mkalias']

        result = get_all_executables()
        # A correct implementation returns bins + aliases; bins come first
        assert result.index('sed') < result.index('mkalias')
        assert len(result) == 2