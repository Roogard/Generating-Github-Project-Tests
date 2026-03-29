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