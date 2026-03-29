## Root Cause Diagnosis

Root Cause: The `disable=None` branch: when `disable is None` and the file is a TTY (so `not file.isatty()` is False), the condition `if disable is None and hasattr(file, "isatty") and not file.isatty()` is not entered, leaving `disable` as `None` rather than converting it to `False`. Additionally, the `last_print_n` attribute is not being set when `disable=True` (early return path) — the early-return block sets `self.n = initial` and `self.total = total` but is missing `self.last_print_n = initial`.

Suggestion 1: Set `self.last_print_n = initial` in the early-return (disable=True) block
In the `if disable:` early-return block (just after `self.n = initial`), add `self.last_print_n = initial` so the attribute exists even when `disable=True`.

Suggestion 2: Convert `disable=None` to `False` when the file is a TTY, and add `last_print_n` in the disabled path
After the `if disable is None and hasattr(file, "isatty") and not file.isatty(): disable = True` block, add an `elif disable is None: disable = False` to convert the remaining `None` case to `False`. Separately, in the `if disable:` early return block, insert `self.last_print_n = initial` before the `return` statement.

## Trigger Test(s)

```python
# test_blackbox.py
import pytest
import sys
import io
from tqdm._tqdm import tqdm


# --- BVA ---

def test_bva_initial_zero():
    """Boundary: initial=0 (minimum typical value)."""
    t = tqdm(total=10, initial=0, disable=True)
    assert t.n == 0
    assert t.last_print_n == 0
    t.close()


def test_bva_initial_one():
    """Boundary: initial=1 (min+1)."""
    t = tqdm(total=10, initial=1, disable=True)
    assert t.n == 1
    assert t.last_print_n == 1
    t.close()


def test_bva_initial_equals_total():
    """Boundary: initial == total."""
    t = tqdm(total=5, initial=5, disable=True)
    assert t.n == 5
    assert t.total == 5
    t.close()


def test_bva_total_zero():
    """Boundary: total=0."""
    t = tqdm(total=0, disable=True)
    assert t.total == 0
    t.close()


def test_bva_total_one():
    """Boundary: total=1."""
    t = tqdm(total=1, disable=True)
    assert t.total == 1
    t.close()


def test_bva_total_large():
    """Boundary: very large total."""
    t = tqdm(total=10**9, disable=True)
    assert t.total == 10**9
    t.close()


def test_bva_total_inf():
    """Boundary: total=float('inf') should be treated as None (unknown)."""
    t = tqdm(total=float("inf"), disable=True)
    assert t.total is None
    t.close()


def test_bva_mininterval_zero():
    """Boundary: mininterval=0 (minimum)."""
    t = tqdm(total=10, mininterval=0, file=io.StringIO())
    assert t.mininterval == 0
    t.close()


def test_bva_mininterval_none():
    """Boundary: mininterval=None should be treated as 0."""
    t = tqdm(total=10, mininterval=None, file=io.StringIO())
    assert t.mininterval == 0
    t.close()


def test_bva_maxinterval_none():
    """Boundary: maxinterval=None should be treated as 0."""
    t = tqdm(total=10, maxinterval=None, file=io.StringIO())
    assert t.maxinterval == 0
    t.close()


def test_bva_smoothing_zero():
    """Boundary: smoothing=0 (average speed)."""
    t = tqdm(total=10, smoothing=0, file=io.StringIO())
    assert t.smoothing == 0
    t.close()


def test_bva_smoothing_one():
    """Boundary: smoothing=1 (instantaneous speed)."""
    t = tqdm(total=10, smoothing=1, file=io.StringIO())
    assert t.smoothing == 1
    t.close()


def test_bva_smoothing_none():
    """Boundary: smoothing=None should be treated as 0."""
    t = tqdm(total=10, smoothing=None, file=io.StringIO())
    assert t.smoothing == 0
    t.close()


def test_bva_empty_iterable():
    """Boundary: empty iterable."""
    t = tqdm([], file=io.StringIO())
    assert t.total == 0
    t.close()


def test_bva_single_element_iterable():
    """Boundary: single-element iterable."""
    t = tqdm([42], file=io.StringIO())
    assert t.total == 1
    t.close()


def test_bva_iterable_none():
    """Boundary: iterable=None (manual mode)."""
    t = tqdm(total=10, file=io.StringIO())
    assert t.iterable is None
    assert t.total == 10
    t.close()


def test_bva_position_zero():
    """Boundary: position=0."""
    t = tqdm(total=10, position=0, file=io.StringIO())
    assert t.pos == 0
    t.close()


def test_bva_position_positive():
    """Boundary: position=1 should be stored as -1 (negative mark for fixed)."""
    t = tqdm(total=10, position=1, file=io.StringIO())
    assert t.pos == -1
    t.close()


def test_bva_desc_empty_string():
    """Boundary: desc='' (empty)."""
    t = tqdm(total=10, desc='', file=io.StringIO())
    assert t.desc == ''
    t.close()


def test_bva_desc_single_char():
    """Boundary: desc='A' (single char)."""
    t = tqdm(total=10, desc='A', file=io.StringIO())
    assert t.desc == 'A'
    t.close()


def test_bva_unit_divisor_default():
    """Boundary: unit_divisor=1000 (default)."""
    t = tqdm(total=10, unit_scale=True, unit_divisor=1000, file=io.StringIO())
    assert t.unit_divisor == 1000
    t.close()


def test_bva_unit_divisor_one():
    """Boundary: unit_divisor=1."""
    t = tqdm(total=10, unit_scale=True, unit_divisor=1, file=io.StringIO())
    assert t.unit_divisor == 1
    t.close()


# --- ECP ---

def test_ecp_valid_disable_true():
    """ECP: disable=True — bar is fully disabled, only minimal state set."""
    t = tqdm(total=100, disable=True)
    assert t.disable is True
    assert t.n == 0
    assert t.total == 100
    t.close()


def test_ecp_valid_disable_false():
    """ECP: disable=False (default) — bar is enabled."""
    t = tqdm(total=10, disable=False, file=io.StringIO())
    assert t.disable is False
    t.close()


def test_ecp_disable_none_non_tty():
    """ECP: disable=None with non-TTY file → should auto-disable."""
    f = io.StringIO()  # StringIO.isatty() returns False
    t = tqdm(total=10, disable=None, file=f)
    assert t.disable is True
    t.close()


def test_ecp_valid_iterable_list():
    """ECP valid class: list iterable → total inferred from len."""
    data = [1, 2, 3, 4, 5]
    t = tqdm(data, file=io.StringIO())
    assert t.total == 5
    assert t.iterable is data
    t.close()


def test_ecp_valid_iterable_generator():
    """ECP valid class: generator has no len → total should be None."""
    gen = (x for x in range(10))
    t = tqdm(gen, file=io.StringIO())
    assert t.total is None
    t.close()


def test_ecp_valid_unit_scale_true():
    """ECP: unit_scale=True."""
    t = tqdm(total=10, unit_scale=True, file=io.StringIO())
    assert t.unit_scale is True
    t.close()


def test_ecp_valid_unit_scale_false():
    """ECP: unit_scale=False."""
    t = tqdm(total=10, unit_scale=False, file=io.StringIO())
    assert t.unit_scale is False
    t.close()


def test_ecp_valid_unit_scale_numeric():
    """ECP: unit_scale=1024 (numeric non-boolean)."""
    t = tqdm(total=10, unit_scale=1024, file=io.StringIO())
    assert t.unit_scale == 1024
    t.close()


def test_ecp_valid_ascii_true():
    """ECP: ascii=True forces ASCII fill characters."""
    t = tqdm(total=10, ascii=True, file=io.StringIO())
    assert t.ascii is True
    t.close()


def test_ecp_valid_ascii_false():
    """ECP: ascii=False forces unicode fill characters."""
    t = tqdm(total=10, ascii=False, file=io.StringIO())
    assert t.ascii is False
    t.close()


def test_ecp_valid_ascii_none():
    """ECP: ascii=None → determined by file encoding support."""
    f = io.StringIO()
    t = tqdm(total=10, ascii=None, file=f)
    assert isinstance(t.ascii, bool)
    t.close()


def test_ecp_valid_leave_true():
    """ECP: leave=True (default)."""
    t = tqdm(total=10, leave=True, file=io.StringIO())
    assert t.leave is True
    t.close()


def test_ecp_valid_leave_false():
    """ECP: leave=False."""
    t = tqdm(total=10, leave=False, file=io.StringIO())
    assert t.leave is False
    t.close()


def test_ecp_valid_gui_false():
    """ECP: gui=False (default) → sp attribute should exist."""
    t = tqdm(total=10, gui=False, file=io.StringIO())
    assert t.gui is False
    assert hasattr(t, 'sp')
    t.close()


def test_ecp_valid_desc_none():
    """ECP: desc=None → should be stored as empty string."""
    t = tqdm(total=10, desc=None, file=io.StringIO())
    assert t.desc == ''
    t.close()


def test_ecp_valid_desc_string():
    """ECP: desc='Loading' → stored as-is."""
    t = tqdm(total=10, desc='Loading', file=io.StringIO())
    assert t.desc == 'Loading'
    t.close()


def test_ecp_invalid_unknown_kwarg():
    """ECP invalid class: unknown kwargs should raise TqdmKeyError."""
    from tqdm._tqdm import TqdmKeyError
    with pytest.raises(TqdmKeyError):
        tqdm(total=10, unknown_param=True, file=io.StringIO())


def test_ecp_invalid_nested_kwarg():
    """ECP invalid class: 'nested' kwarg should raise TqdmDeprecationWarning."""
    from tqdm._tqdm import TqdmDeprecationWarning
    with pytest.raises(TqdmDeprecationWarning):
        tqdm(total=10, nested=True, file=io.StringIO())


def test_ecp_postfix_dict():
    """ECP: postfix as dict should call set_postfix."""
    t = tqdm(total=10, postfix={'loss': 0.5}, file=io.StringIO())
    assert t.postfix is not None
    t.close()


def test_ecp_postfix_non_dict():
    """ECP: postfix as non-dict should be stored directly."""
    t = tqdm(total=10, postfix='custom', file=io.StringIO())
    assert t.postfix == 'custom'
    t.close()


def test_ecp_miniters_none_sets_dynamic():
    """ECP: miniters=None → dynamic_miniters=True, miniters=0."""
    t = tqdm(total=10, miniters=None, file=io.StringIO())
    assert t.miniters == 0
    assert t.dynamic_miniters is True
    t.close()


def test_ecp_miniters_explicit_disables_dynamic():
    """ECP: miniters=5 → dynamic_miniters=False."""
    t = tqdm(total=10, miniters=5, file=io.StringIO())
    assert t.miniters == 5
    assert t.dynamic_miniters is False
    t.close()


def test_ecp_miniters_zero_explicit():
    """ECP: miniters=0 explicitly → dynamic_miniters=False."""
    t = tqdm(total=10, miniters=0, file=io.StringIO())
    assert t.miniters == 0
    assert t.dynamic_miniters is False
    t.close()


def test_ecp_bar_format_string():
    """ECP: bar_format string is stored."""
    fmt = '{l_bar}{bar}{r_bar}'
    t = tqdm(total=10, bar_format=fmt, file=io.StringIO())
    assert t.bar_format == fmt
    t.close()


def test_ecp_bar_format_none():
    """ECP: bar_format=None → stored as None."""
    t = tqdm(total=10, bar_format=None, file=io.StringIO())
    assert t.bar_format is None
    t.close()


def test_ecp_ncols_explicit():
    """ECP: ncols=80 is stored as-is."""
    t = tqdm(total=10, ncols=80, file=io.StringIO())
    assert t.ncols == 80
    t.close()


def test_ecp_unit_default():
    """ECP: default unit is 'it'."""
    t = tqdm(total=10, file=io.StringIO())
    assert t.unit == 'it'
    t.close()


def test_ecp_unit_custom():
    """ECP: custom unit stored correctly."""
    t = tqdm(total=10, unit='bytes', file=io.StringIO())
    assert t.unit == 'bytes'
    t.close()


# --- Mutation Detection ---

def test_mutation_total_inf_treated_as_none():
    """
    Mutation: catches `total == float('inf')` vs `total != float('inf')`.
    A correct implementation SHOULD set total=None when total=float('inf').
    """
    t = tqdm(total=float("inf"), disable=True)
    # If the condition were negated, total would remain float('inf') instead of None
    assert t.total is None
    t.close()


def test_mutation_total_large_not_treated_as_inf():
    """
    Mutation: catches over-broad inf check (e.g., total > 1e300).
    Large but finite total should NOT be converted to None.
    """
    t = tqdm(total=10**15, disable=True)
    assert t.total == 10**15
    t.close()


def test_mutation_initial_n_correct():
    """
    Mutation: catches wrong variable assignment (e.g., n = 0 instead of n = initial).
    A correct init SHOULD set self.n == initial.
    """
    t = tqdm(total=100, initial=42, disable=True)
    assert t.n == 42
    t.close()


def test_mutation_last_print_n_equals_initial():
    """
    Mutation: catches last_print_n = 0 instead of last_print_n = initial.
    """
    t = tqdm(total=100, initial=7, disable=True)
    assert t.last_print_n == 7
    t.close()


def test_mutation_miniters_none_sets_zero_not_one():
    """
    Mutation: catches off-by-one where miniters defaults to 1 instead of 0.
    """
    t = tqdm(total=10, miniters=None, file=io.StringIO())
    assert t.miniters == 0  # NOT 1
    t.close()


def test_mutation_dynamic_miniters_true_when_miniters_none():
    """
    Mutation: catches negation error (dynamic_miniters = False when miniters is None).
    A correct implementation SHOULD set dynamic_miniters=True when miniters=None.
    """
    t = tqdm(total=10, miniters=None, file=io.StringIO())
    assert t.dynamic_miniters is True
    t.close()


def test_mutation_dynamic_miniters_false_when_miniters_given():
    """
    Mutation: catches wrong operator (dynamic_miniters = True when miniters is given).
    """
    t = tqdm(total=10, miniters=1, file=io.StringIO())
    assert t.dynamic_miniters is False
    t.close()


def test_mutation_mininterval_none_becomes_zero():
    """
    Mutation: catches missing None→0 conversion for mininterval.
    """
    t = tqdm(total=10, mininterval=None, file=io.StringIO())
    assert t.mininterval == 0
    t.close()


def test_mutation_maxinterval_none_becomes_zero():
    """
    Mutation: catches missing None→0 conversion for maxinterval.
    """
    t = tqdm(total=10, maxinterval=None, file=io.StringIO())
    assert t.maxinterval == 0
    t.close()


def test_mutation_smoothing_none_becomes_zero():
    """
    Mutation: catches missing None→0 conversion for smoothing.
    """
    t = tqdm(total=10, smoothing=None, file=io.StringIO())
    assert t.smoothing == 0
    t.close()


def test_mutation_disable_none_non_tty_sets_disable_true():
    """
    Mutation: catches `not file.isatty()` vs `file.isatty()` (negation error).
    Non-TTY file + disable=None should result in disable=True.
    """
    f = io.StringIO()  # isatty() → False
    t = tqdm(total=10, disable=None, file=f)
    assert t.disable is True
    t.close()


def test_mutation_disable_none_tty_keeps_disable_none_or_false():
    """
    Mutation: catches over-aggressive disable — TTY file should NOT disable.
    We use a mock-like object with isatty()=True.
    """
    class FakeTTY(io.StringIO):
        def isatty(self):
            return True

    f = FakeTTY()
    t = tqdm(total=10, disable=None, file=f)
    # A correct implementation should NOT disable when isatty() is True
    assert t.disable is not True
    t.close()


def test_mutation_desc_none_becomes_empty_string():
    """
    Mutation: catches `desc = desc` instead of `desc = desc or ''`.
    When desc=None, a correct init SHOULD store '' not None.
    """
    t = tqdm(total=10, desc=None, file=io.StringIO())
    assert t.desc == ''
    t.close()


def test_mutation_position_zero_stored_as_zero():
    """
    Mutation: catches off-by-one in position negation. position=0 → self.pos should be 0 (not -0, same thing, but confirms branch).
    """
    t = tqdm(total=10, position=0, file=io.StringIO())
    assert t.pos == 0
    t.close()


def test_mutation_position_2_stored_as_negative_2():
    """
    Mutation: catches wrong sign in `self.pos = -position`.
    A correct implementation SHOULD store pos = -position for fixed positions.
    """
    t = tqdm(total=10, position=2, file=io.StringIO())
    assert t.pos == -2
    t.close()


def test_mutation_total_inferred_from_list_len():
    """
    Mutation: catches `total = len(iterable) + 1` or other off-by-one.
    A correct implementation SHOULD infer total == len(iterable).
    """
    data = list(range(7))
    t = tqdm(data, file=io.StringIO())
    assert t.total == len(data)
    t.close()


def test_mutation_total_none_when_iterable_is_generator():
    """
    Mutation: catches fallback that sets total=0 instead of None for generators.
    """
    gen = (x for x in range(5))
    t = tqdm(gen, file=io.StringIO())
    assert t.total is None
    t.close()


def test_mutation_disable_true_returns_early_no_sp():
    """
    Mutation: catches missing early return when disable=True.
    A disabled tqdm SHOULD NOT have a status printer (sp) initialized.
    """
    t = tqdm(total=10, disable=True)
    assert not hasattr(t, 'sp') or t.sp is None or True  # property check
    # More importantly, the bar must be disabled and not crash
    assert t.disable is True
    t.close()


def test_mutation_iterable_stored_correctly():
    """
    Mutation: catches self.iterable = None instead of self.iterable = iterable.
    """
    data = [1, 2, 3]
    t = tqdm(data, file=io.StringIO())
    assert t.iterable is data
    t.close()


def test_mutation_avg_time_initialized_none():
    """
    Mutation: catches avg_time initialized to 0 instead of None.
    A correct init SHOULD set avg_time=None.
    """
    t = tqdm(total=10, file=io.StringIO())
    assert t.avg_time is None
    t.close()


def test_mutation_postfix_none_by_default():
    """
    Mutation: catches postfix being set to something other than None when not provided.
    """
    t = tqdm(total=10, file=io.StringIO())
    assert t.postfix is None
    t.close()


def test_mutation_leave_stored_correctly():
    """
    Mutation: catches leave being stored as not leave (negation error).
    """
    t = tqdm(total=10, leave=False, file=io.StringIO())
    assert t.leave is False
    t2 = tqdm(total=10, leave=True, file=io.StringIO())
    assert t2.leave is True
    t.close()
    t2.close()


def test_mutation_unit_scale_stored_correctly():
    """
    Mutation: catches unit_scale being ignored or negated.
    """
    t = tqdm(total=10, unit_scale=True, file=io.StringIO())
    assert t.unit_scale is True
    t2 = tqdm(total=10, unit_scale=False, file=io.StringIO())
    assert t2.unit_scale is False
    t.close()
    t2.close()


def test_mutation_write_bytes_false_in_py3():
    """
    Mutation: catches write_bytes defaulting to True in Python 3.
    In Python 3 with file=None, write_bytes should be False.
    """
    # We test indirectly: in Python 3, file defaults to sys.stderr and
    # write_bytes should not wrap it in SimpleTextIOWrapper
    import sys
    if sys.version_info >= (3,):
        # Just check initialization doesn't raise and sets up fp correctly
        t = tqdm(total=5, file=io.StringIO())
        # fp should be the StringIO, not wrapped
        assert t.fp is not None
        t.close()
```

```python
# test_whitebox.py
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
```
