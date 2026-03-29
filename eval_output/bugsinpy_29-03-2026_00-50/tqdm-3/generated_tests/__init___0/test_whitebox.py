import io
import sys
import pytest
from tqdm._tqdm import tqdm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_file():
    """Return a StringIO that pretends to be a TTY so disable=None stays False."""
    f = io.StringIO()
    f.isatty = lambda: True
    return f


# ---------------------------------------------------------------------------
# Statement Coverage
# ---------------------------------------------------------------------------

# --- Statement Coverage ---

def test_sc_basic_no_iterable():
    """Minimal init: no iterable, explicit file to avoid stderr."""
    # path: write_bytes=False, file given, disable=False, no kwargs
    f = make_file()
    t = tqdm(file=f, disable=False)
    assert t.disable is False
    assert t.iterable is None
    assert t.n == 0
    t.close()


def test_sc_with_iterable_has_len():
    """total inferred from len(iterable)."""
    f = make_file()
    t = tqdm([1, 2, 3], file=f)
    # A correct tqdm SHOULD infer total=3 from the list
    assert t.total == 3
    t.close()


def test_sc_with_iterable_no_len():
    """total stays None when iterable has no __len__."""
    f = make_file()
    t = tqdm(iter([1, 2, 3]), file=f)
    assert t.total is None
    t.close()


def test_sc_total_inf_becomes_none():
    """total=float('inf') should be treated as unknown (None)."""
    f = make_file()
    t = tqdm(total=float("inf"), file=f)
    assert t.total is None
    t.close()


def test_sc_disable_true_early_return():
    """disable=True triggers early return; fields still set."""
    f = make_file()
    t = tqdm([1, 2, 3], file=f, disable=True)
    assert t.disable is True
    assert t.n == 0
    assert t.total == 3
    t.close()


def test_sc_disable_none_non_tty():
    """disable=None + non-tty file => disable becomes True."""
    f = io.StringIO()
    # StringIO has no isatty or isatty() returns False
    t = tqdm(file=f, disable=None)
    assert t.disable is True
    t.close()


def test_sc_miniters_none_sets_dynamic():
    """miniters=None => miniters=0 and dynamic_miniters=True."""
    f = make_file()
    t = tqdm(file=f, miniters=None)
    assert t.miniters == 0
    assert t.dynamic_miniters is True
    t.close()


def test_sc_miniters_given_no_dynamic():
    """miniters given => dynamic_miniters=False."""
    f = make_file()
    t = tqdm(file=f, miniters=5)
    assert t.miniters == 5
    assert t.dynamic_miniters is False
    t.close()


def test_sc_mininterval_none():
    """mininterval=None => 0."""
    f = make_file()
    t = tqdm(file=f, mininterval=None)
    assert t.mininterval == 0
    t.close()


def test_sc_maxinterval_none():
    """maxinterval=None => 0."""
    f = make_file()
    t = tqdm(file=f, maxinterval=None)
    assert t.maxinterval == 0
    t.close()


def test_sc_smoothing_none():
    """smoothing=None => 0."""
    f = make_file()
    t = tqdm(file=f, smoothing=None)
    assert t.smoothing == 0
    t.close()


def test_sc_postfix_dict():
    """postfix as dict => set_postfix called."""
    f = make_file()
    t = tqdm(file=f, postfix={"loss": 0.5})
    # A correctly initialised tqdm with a dict postfix should have postfix set
    assert t.postfix is not None
    t.close()


def test_sc_postfix_non_dict():
    """postfix as non-dict (TypeError from set_postfix) => stored directly."""
    f = make_file()
    t = tqdm(file=f, postfix="raw_string")
    assert t.postfix == "raw_string"
    t.close()


def test_sc_position_fixed():
    """position given => pos = -position."""
    f = make_file()
    t = tqdm(file=f, position=2)
    assert t.pos == -2
    t.close()


def test_sc_position_none_auto():
    """position=None => automatic pos via _get_free_pos."""
    f = make_file()
    t = tqdm(file=f, position=None)
    # pos should be a non-negative integer for the first bar
    assert isinstance(t.pos, int)
    assert t.pos >= 0
    t.close()


def test_sc_initial_nonzero():
    """initial != 0 => n and last_print_n start at initial."""
    f = make_file()
    t = tqdm(file=f, initial=10)
    assert t.n == 10
    assert t.last_print_n == 10
    t.close()


def test_sc_kwargs_nested_deprecation():
    """Passing 'nested' kwarg => TqdmDeprecationWarning raised."""
    f = make_file()
    from tqdm._tqdm import TqdmDeprecationWarning
    with pytest.raises(TqdmDeprecationWarning):
        tqdm(file=f, nested=True)


def test_sc_kwargs_unknown_key():
    """Unknown kwarg => TqdmKeyError raised."""
    f = make_file()
    from tqdm._tqdm import TqdmKeyError
    with pytest.raises(TqdmKeyError):
        tqdm(file=f, totally_unknown_param=99)


# ---------------------------------------------------------------------------
# Block Coverage
# ---------------------------------------------------------------------------

# --- Block Coverage ---

def test_bc_write_bytes_false_no_wrapper():
    """Python 3 + file given: write_bytes stays False, no SimpleTextIOWrapper."""
    f = make_file()
    t = tqdm(file=f)
    # fp should be the file we passed (not wrapped) — or at least be writable
    assert hasattr(t.fp, 'write')
    t.close()


def test_bc_bar_format_unicode():
    """bar_format given + ascii=False + non-pure-ascii bar => bar_format converted."""
    # ascii=False and bar_format with non-ascii content
    f = make_file()
    bar_fmt = u"{l_bar}{bar}{r_bar}"
    t = tqdm(file=f, bar_format=bar_fmt, ascii=False)
    # A correct tqdm SHOULD store the bar_format (possibly as unicode)
    assert t.bar_format == bar_fmt
    t.close()


def test_bc_bar_format_ascii_true_no_convert():
    """bar_format given + ascii=True => no unicode conversion branch."""
    f = make_file()
    bar_fmt = "{l_bar}{bar}{r_bar}"
    t = tqdm(file=f, bar_format=bar_fmt, ascii=True)
    assert t.bar_format == bar_fmt
    t.close()


def test_bc_no_bar_format():
    """bar_format=None => conversion block skipped entirely."""
    f = make_file()
    t = tqdm(file=f, bar_format=None)
    assert t.bar_format is None
    t.close()


def test_bc_gui_true_skips_sp():
    """gui=True => status_printer block and display() skipped; sp not set."""
    f = make_file()
    t = tqdm(file=f, gui=True)
    assert t.gui is True
    assert not hasattr(t, 'sp')
    t.close()


def test_bc_gui_false_sets_sp():
    """gui=False => status_printer set and display called."""
    f = make_file()
    t = tqdm(file=f, gui=False)
    assert hasattr(t, 'sp')
    assert callable(t.sp)
    t.close()


def test_bc_desc_empty_string():
    """desc=None => self.desc is ''."""
    f = make_file()
    t = tqdm(file=f, desc=None)
    assert t.desc == ''
    t.close()


def test_bc_desc_given():
    """desc given => self.desc is that string."""
    f = make_file()
    t = tqdm(file=f, desc="loading")
    assert t.desc == "loading"
    t.close()


def test_bc_disable_false_full_init():
    """disable=False => full init path, start_t and last_print_t set."""
    f = make_file()
    t = tqdm(file=f, disable=False)
    assert hasattr(t, 'start_t')
    assert hasattr(t, 'last_print_t')
    assert t.start_t <= t.last_print_t + 1  # sanity
    t.close()


# ---------------------------------------------------------------------------
# Condition Coverage
# ---------------------------------------------------------------------------

# --- Condition Coverage ---

# Condition: write_bytes is None AND file is None AND sys.version_info < (3,)
# In Python 3: version check is False => write_bytes = False
def test_cc_write_bytes_none_file_none_py3():
    """write_bytes=None, file=None => write_bytes=False on Python 3.
    # write_bytes is None: True, file is None: True, version < (3,): False
    """
    # Just check we don't crash and write_bytes doesn't cause wrapping
    t = tqdm(disable=True)
    assert t.disable is True
    t.close()


def test_cc_write_bytes_given_true():
    """write_bytes=True (not None) => SimpleTextIOWrapper applied.
    # write_bytes is None: False
    """
    f = io.StringIO()
    f.isatty = lambda: True
    t = tqdm(file=f, write_bytes=True, disable=True)
    assert t.disable is True
    t.close()


# Condition: disable is None AND hasattr(file, 'isatty') AND not file.isatty()
def test_cc_disable_none_has_isatty_returns_false():
    """disable=None, file has isatty returning False => disable becomes True.
    # disable is None: True, hasattr isatty: True, not isatty(): True
    """
    f = io.StringIO()
    t = tqdm(file=f, disable=None)
    assert t.disable is True
    t.close()


def test_cc_disable_none_has_isatty_returns_true():
    """disable=None, file is a TTY => disable stays None (=> False path).
    # disable is None: True, hasattr isatty: True, not isatty(): False
    """
    f = make_file()
    t = tqdm(file=f, disable=None)
    assert t.disable is False
    t.close()


def test_cc_disable_false_skips_check():
    """disable=False => condition block not entered.
    # disable is None: False
    """
    f = make_file()
    t = tqdm(file=f, disable=False)
    assert t.disable is False
    t.close()


# Condition: total is None AND iterable is not None
def test_cc_total_none_iterable_not_none():
    """total=None, iterable given => try len(iterable).
    # total is None: True, iterable is not None: True
    """
    f = make_file()
    t = tqdm([1, 2], file=f)
    assert t.total == 2
    t.close()


def test_cc_total_given_iterable_not_none():
    """total given => skip len inference.
    # total is None: False
    """
    f = make_file()
    t = tqdm([1, 2], total=5, file=f)
    assert t.total == 5
    t.close()


def test_cc_total_none_iterable_none():
    """total=None, iterable=None => total stays None.
    # total is None: True, iterable is not None: False
    """
    f = make_file()
    t = tqdm(file=f)
    assert t.total is None
    t.close()


# Condition: total == float("inf")
def test_cc_total_is_inf():
    """total=inf => treated as None.
    # total == float('inf'): True
    """
    f = make_file()
    t = tqdm(total=float("inf"), file=f)
    assert t.total is None
    t.close()


def test_cc_total_finite():
    """total=5 => not inf, stays 5.
    # total == float('inf'): False
    """
    f = make_file()
    t = tqdm(total=5, file=f)
    assert t.total == 5
    t.close()


# Condition: miniters is None
def test_cc_miniters_is_none():
    """miniters=None => dynamic_miniters=True, miniters=0.
    # miniters is None: True
    """
    f = make_file()
    t = tqdm(file=f, miniters=None)
    assert t.miniters == 0
    assert t.dynamic_miniters is True
    t.close()


def test_cc_miniters_not_none():
    """miniters=2 => dynamic_miniters=False.
    # miniters is None: False
    """
    f = make_file()
    t = tqdm(file=f, miniters=2)
    assert t.miniters == 2
    assert t.dynamic_miniters is False
    t.close()


# Condition: ascii is None
def test_cc_ascii_none():
    """ascii=None => determined by _supports_unicode.
    # ascii is None: True
    """
    f = make_file()
    t = tqdm(file=f, ascii=None)
    assert isinstance(t.ascii, bool)
    t.close()


def test_cc_ascii_given_true():
    """ascii=True => stored directly.
    # ascii is None: False
    """
    f = make_file()
    t = tqdm(file=f, ascii=True)
    assert t.ascii is True
    t.close()


# Condition: bar_format AND NOT ((ascii is True) OR _is_ascii(ascii))
def test_cc_bar_format_needs_unicode_conversion():
    """bar_format set, ascii=False => unicode conversion attempted.
    # bar_format: True, (ascii is True): False, _is_ascii(ascii): False (for ascii=False)
    """
    f = make_file()
    t = tqdm(file=f, bar_format="{l_bar}", ascii=False)
    assert t.bar_format is not None
    t.close()


def test_cc_bar_format_ascii_true_no_conversion():
    """bar_format set, ascii=True => no conversion.
    # bar_format: True, (ascii is True): True
    """
    f = make_file()
    t = tqdm(file=f, bar_format="{l_bar}", ascii=True)
    assert t.bar_format == "{l_bar}"
    t.close()


# Condition: smoothing is None
def test_cc_smoothing_none():
    """smoothing=None => set to 0.
    # smoothing is None: True
    """
    f = make_file()
    t = tqdm(file=f, smoothing=None)
    assert t.smoothing == 0
    t.close()


def test_cc_smoothing_given():
    """smoothing=0.5 => stored as-is.
    # smoothing is None: False
    """
    f = make_file()
    t = tqdm(file=f, smoothing=0.5)
    assert t.smoothing == 0.5
    t.close()


# Condition: postfix truthy => set_postfix called
def test_cc_postfix_truthy_dict():
    """postfix is a dict => set_postfix(**postfix).
    # postfix truthy: True
    """
    f = make_file()
    t = tqdm(file=f, postfix={"k": 1})
    assert t.postfix is not None
    t.close()


def test_cc_postfix_falsy():
    """postfix=None => postfix stays None.
    # postfix truthy: False
    """
    f = make_file()
    t = tqdm(file=f, postfix=None)
    assert t.postfix is None
    t.close()


# Condition: position is None
def test_cc_position_none_auto():
    """position=None => auto pos.
    # position is None: True
    """
    f = make_file()
    t = tqdm(file=f, position=None)
    assert t.pos >= 0
    t.close()


def test_cc_position_given():
    """position=1 => pos = -1.
    # position is None: False
    """
    f = make_file()
    t = tqdm(file=f, position=1)
    assert t.pos == -1
    t.close()


# Condition: not gui
def test_cc_gui_false_sp_created():
    """not gui: True => sp created and display() called.
    # not gui: True
    """
    f = make_file()
    t = tqdm(file=f, gui=False)
    assert hasattr(t, 'sp')
    t.close()


def test_cc_gui_true_no_sp():
    """not gui: False => sp block skipped.
    # not gui: False
    """
    f = make_file()
    t = tqdm(file=f, gui=True)
    assert not hasattr(t, 'sp')
    t.close()


# ---------------------------------------------------------------------------
# Path Coverage
# ---------------------------------------------------------------------------

# --- Path Coverage ---

def test_path_disable_true_early_return():
    """path: write_bytes=False → file=stderr → disable=True → early return
    # disable branch taken; no further attribute setup
    """
    f = make_file()
    t = tqdm([1, 2, 3], file=f, disable=True, initial=5)
    # A correctly disabled tqdm SHOULD still expose n=initial and total
    assert t.n == 5
    assert t.total == 3
    assert t.disable is True
    assert not hasattr(t, 'sp')
    t.close()


def test_path_kwargs_nested_raises():
    """path: → kwargs non-empty → 'nested' in kwargs → TqdmDeprecationWarning
    # kwargs block taken, nested branch
    """
    f = make_file()
    from tqdm._tqdm import TqdmDeprecationWarning
    with pytest.raises(TqdmDeprecationWarning):
        tqdm(file=f, nested=True)


def test_path_kwargs_unknown_raises():
    """path: → kwargs non-empty → unknown key → TqdmKeyError
    # kwargs block taken, else branch
    """
    f = make_file()
    from tqdm._tqdm import TqdmKeyError
    with pytest.raises(TqdmKeyError):
        tqdm(file=f, bad_kwarg=1)


def test_path_full_init_with_iterable_and_postfix():
    """path: normal flow → iterable with len → miniters=None → postfix dict → gui=False
    # Full initialisation path with all major branches exercised
    """
    f = make_file()
    t = tqdm(
        [1, 2, 3], file=f,
        desc="test", total=None,
        miniters=None, ascii=True,
        bar_format=None, smoothing=0.3,
        postfix={"loss": 0.1}, position=None,
        gui=False
    )
    assert t.total == 3
    assert t.desc == "test"
    assert t.miniters == 0
    assert t.dynamic_miniters is True
    assert t.ascii is True
    assert t.postfix is not None
    assert t.pos >= 0
    assert hasattr(t, 'sp')
    assert hasattr(t, 'start_t')
    t.close()


def test_path_full_init_no_iterable_miniters_given_position_fixed():
    """path: no iterable → total=None → miniters=5 → position=3 → gui=False
    # alternative sub-path: miniters given, fixed position
    """
    f = make_file()
    t = tqdm(
        file=f, miniters=5, position=3,
        ascii=False, bar_format="{l_bar}", gui=False
    )
    assert t.total is None
    assert t.miniters == 5
    assert t.dynamic_miniters is False
    assert t.pos == -3
    assert hasattr(t, 'sp')
    t.close()


def test_path_disable_none_non_tty_early_disable():
    """path: disable=None → file non-tty → disable=True → early return
    # disable=None path leading to disable=True
    """
    f = io.StringIO()  # no isatty => treated as non-tty
    t = tqdm(file=f, disable=None, total=10)
    assert t.disable is True
    t.close()


def test_path_total_inf_then_disable():
    """path: iterable given → total=inf → total=None → normal init
    # total=inf normalised then full init
    """
    f = make_file()
    t = tqdm([1, 2, 3], total=float("inf"), file=f)
    assert t.total is None
    assert t.n == 0
    t.close()


def test_path_iterable_no_len_total_none():
    """path: iterable has no len → TypeError caught → total=None → full init
    # generator path: zero iterations possible at iter-time (not init)
    """
    f = make_file()
    gen = (x for x in range(5))
    t = tqdm(gen, file=f)
    assert t.total is None
    t.close()


def test_path_gui_true_no_sp_block():
    """path: full init → gui=True → skip sp block → set start_t
    # gui=True path: sp never created, display never called
    """
    f = make_file()
    t = tqdm(file=f, gui=True, disable=False)
    assert not hasattr(t, 'sp')
    assert hasattr(t, 'start_t')
    t.close()


def test_path_postfix_non_dict_type_error():
    """path: postfix truthy → set_postfix raises TypeError → store as-is
    # TypeError except block in postfix handling
    """
    f = make_file()
    t = tqdm(file=f, postfix="plain_string")
    assert t.postfix == "plain_string"
    t.close()


def test_path_smoothing_none_sets_zero():
    """path: smoothing=None → set to 0 → rest of init
    # smoothing=None sub-path
    """
    f = make_file()
    t = tqdm(file=f, smoothing=None)
    assert t.smoothing == 0
    assert hasattr(t, 'start_t')
    t.close()


def test_path_mininterval_none_maxinterval_none():
    """path: mininterval=None → 0, maxinterval=None → 0
    # both interval none paths
    """
    f = make_file()
    t = tqdm(file=f, mininterval=None, maxinterval=None)
    assert t.mininterval == 0
    assert t.maxinterval == 0
    t.close()


def test_path_bar_format_ascii_string():
    """path: bar_format set, ascii is an ASCII-only string => no unicode convert
    # _is_ascii(ascii) True branch
    """
    f = make_file()
    t = tqdm(file=f, bar_format="{l_bar}", ascii=" 123456789#")
    assert t.bar_format == "{l_bar}"
    t.close()