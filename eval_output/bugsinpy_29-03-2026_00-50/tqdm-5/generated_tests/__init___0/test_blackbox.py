import sys
import io
import pytest
from tqdm._tqdm import tqdm


# Helper: create a tqdm instance with a StringIO file to avoid terminal deps
def make_tqdm(**kwargs):
    f = io.StringIO()
    kwargs.setdefault('file', f)
    return tqdm(**kwargs)


# --- BVA ---

# Boundary: iterable=None (no iterable provided)
def test_bva_iterable_none():
    t = make_tqdm(iterable=None)
    assert t.iterable is None
    assert t.total is None
    t.close()


# Boundary: iterable with a single element
def test_bva_iterable_single_element():
    t = make_tqdm(iterable=[42])
    assert t.iterable == [42]
    assert t.total == 1
    t.close()


# Boundary: iterable with zero elements (empty list)
def test_bva_iterable_empty():
    t = make_tqdm(iterable=[])
    assert t.iterable == []
    assert t.total == 0
    t.close()


# Boundary: iterable with many elements
def test_bva_iterable_large():
    data = list(range(10000))
    t = make_tqdm(iterable=data)
    assert t.total == 10000
    t.close()


# Boundary: initial=0 (minimum default)
def test_bva_initial_zero():
    t = make_tqdm(initial=0)
    assert t.n == 0
    assert t.last_print_n == 0
    t.close()


# Boundary: initial=1 (min+1)
def test_bva_initial_one():
    t = make_tqdm(initial=1)
    assert t.n == 1
    assert t.last_print_n == 1
    t.close()


# Boundary: initial large positive
def test_bva_initial_large():
    t = make_tqdm(initial=int(9e9))
    assert t.n == int(9e9)
    t.close()


# Boundary: mininterval=0 (minimum edge)
def test_bva_mininterval_zero():
    t = make_tqdm(mininterval=0)
    assert t.mininterval == 0
    t.close()


# Boundary: mininterval=None should become 0
def test_bva_mininterval_none():
    t = make_tqdm(mininterval=None)
    assert t.mininterval == 0
    t.close()


# Boundary: maxinterval=None should become 0
def test_bva_maxinterval_none():
    t = make_tqdm(maxinterval=None)
    assert t.maxinterval == 0
    t.close()


# Boundary: smoothing=0 (average speed)
def test_bva_smoothing_zero():
    t = make_tqdm(smoothing=0)
    assert t.smoothing == 0
    t.close()


# Boundary: smoothing=1 (instantaneous speed)
def test_bva_smoothing_one():
    t = make_tqdm(smoothing=1)
    assert t.smoothing == 1
    t.close()


# Boundary: smoothing=None should become 0
def test_bva_smoothing_none():
    t = make_tqdm(smoothing=None)
    assert t.smoothing == 0
    t.close()


# Boundary: desc=None -> empty string
def test_bva_desc_none():
    t = make_tqdm(desc=None)
    assert t.desc == ''
    t.close()


# Boundary: desc='' -> empty string
def test_bva_desc_empty_string():
    t = make_tqdm(desc='')
    assert t.desc == ''
    t.close()


# Boundary: desc single char
def test_bva_desc_single_char():
    t = make_tqdm(desc='x')
    assert t.desc == 'x'
    t.close()


# Boundary: position=0 (minimum)
def test_bva_position_zero():
    t = make_tqdm(position=0)
    # position=0 means pos = -0 = 0
    assert t.pos == 0
    t.close()


# Boundary: position=1
def test_bva_position_one():
    t = make_tqdm(position=1)
    # mark fixed positions as negative: pos = -position
    assert t.pos == -1
    t.close()


# --- ECP ---

# ECP: Valid — disable=True short-circuits init, sets n=initial
def test_ecp_valid_disable_true():
    f = io.StringIO()
    t = tqdm(iterable=[1, 2, 3], disable=True, initial=5, file=f)
    assert t.disable is True
    assert t.n == 5
    assert t.iterable == [1, 2, 3]


# ECP: Valid — disable=False (normal operation)
def test_ecp_valid_disable_false():
    t = make_tqdm(disable=False)
    assert t.disable is False
    t.close()


# ECP: Invalid — disable=None + non-TTY file => disable becomes True
def test_ecp_invalid_disable_none_non_tty():
    f = io.StringIO()  # not a TTY, has isatty() returning False
    t = tqdm(iterable=None, disable=None, file=f)
    assert t.disable is True


# ECP: Valid — miniters=None => 0 + dynamic_miniters=True
def test_ecp_valid_miniters_none():
    t = make_tqdm(miniters=None)
    assert t.miniters == 0
    assert t.dynamic_miniters is True
    t.close()


# ECP: Valid — miniters=5 => stored, dynamic_miniters=False
def test_ecp_valid_miniters_specified():
    t = make_tqdm(miniters=5)
    assert t.miniters == 5
    assert t.dynamic_miniters is False
    t.close()


# ECP: Valid — unit_scale=True
def test_ecp_valid_unit_scale_true():
    t = make_tqdm(unit_scale=True)
    assert t.unit_scale is True
    t.close()


# ECP: Valid — unit_scale=False
def test_ecp_valid_unit_scale_false():
    t = make_tqdm(unit_scale=False)
    assert t.unit_scale is False
    t.close()


# ECP: Valid — unit_scale=1024 (numeric), provide total to avoid TypeError in format_meter
def test_ecp_valid_unit_scale_numeric():
    t = make_tqdm(unit_scale=1024, total=1000)
    assert t.unit_scale == 1024
    t.close()


# ECP: Valid — leave=True
def test_ecp_valid_leave_true():
    t = make_tqdm(leave=True)
    assert t.leave is True
    t.close()


# ECP: Valid — leave=False
def test_ecp_valid_leave_false():
    t = make_tqdm(leave=False)
    assert t.leave is False
    t.close()


# ECP: Valid — total specified explicitly overrides len(iterable)
def test_ecp_valid_total_explicit():
    t = make_tqdm(iterable=[1, 2, 3], total=99)
    assert t.total == 99
    t.close()


# ECP: Valid — total inferred from len(iterable) when total=None
def test_ecp_valid_total_inferred():
    t = make_tqdm(iterable=[1, 2, 3], total=None)
    assert t.total == 3
    t.close()


# ECP: Valid — iterable without __len__ => total=None
def test_ecp_valid_iterable_no_len():
    def gen():
        yield 1
        yield 2
    t = make_tqdm(iterable=gen())
    assert t.total is None
    t.close()


# ECP: Invalid — unknown kwargs raises TqdmKeyError (not 'nested')
def test_ecp_invalid_unknown_kwarg():
    f = io.StringIO()
    with pytest.raises(Exception) as exc_info:
        tqdm(iterable=None, file=f, unknown_param=True)
    assert 'Unknown argument' in str(exc_info.value) or 'TqdmKeyError' in type(exc_info.value).__name__


# ECP: Invalid — 'nested' kwarg raises TqdmDeprecationWarning
def test_ecp_invalid_nested_kwarg():
    f = io.StringIO()
    with pytest.raises(Exception) as exc_info:
        tqdm(iterable=None, file=f, nested=True)
    assert 'nested' in str(exc_info.value).lower() or 'deprecated' in str(exc_info.value).lower()


# ECP: Valid — postfix as dict
def test_ecp_valid_postfix_dict():
    t = make_tqdm(postfix={'loss': 0.5})
    # postfix should be set (either via set_postfix or stored directly)
    assert t.postfix is not None
    t.close()


# ECP: Valid — postfix=None => stored as None
def test_ecp_valid_postfix_none():
    t = make_tqdm(postfix=None)
    assert t.postfix is None
    t.close()


# ECP: Valid — unit stored correctly
def test_ecp_valid_unit_string():
    t = make_tqdm(unit='MB')
    assert t.unit == 'MB'
    t.close()


# ECP: Valid — bar_format stored
def test_ecp_valid_bar_format():
    t = make_tqdm(bar_format='{l_bar}{bar}{r_bar}')
    assert t.bar_format is not None
    t.close()


# ECP: Valid — bar_format=None stored as None
def test_ecp_valid_bar_format_none():
    t = make_tqdm(bar_format=None)
    assert t.bar_format is None
    t.close()


# ECP: Valid — gui=True skips status_printer setup
def test_ecp_valid_gui_true():
    t = make_tqdm(gui=True)
    assert t.gui is True
    assert not hasattr(t, 'sp')
    t.close()


# ECP: Valid — gui=False (default) sets up sp
def test_ecp_valid_gui_false():
    t = make_tqdm(gui=False)
    assert t.gui is False
    assert hasattr(t, 'sp')
    t.close()


# ECP: Valid — unit_divisor stored
def test_ecp_valid_unit_divisor():
    t = make_tqdm(unit_divisor=1024)
    assert t.unit_divisor == 1024
    t.close()


# --- Mutation Detection ---

# Mutation: `if disable` branch — checks that disable=True does NOT set self.leave, self.desc etc.
# Detects: flipped boolean or missing early return
def test_mutation_disable_true_early_return():
    f = io.StringIO()
    t = tqdm(iterable=[1, 2], disable=True, file=f)
    # A correct implementation short-circuits; full attributes like 'desc', 'unit' should NOT be set
    assert not hasattr(t, 'desc'), "disable=True should cause early return before desc is set"
    assert not hasattr(t, 'unit'), "disable=True should cause early return before unit is set"


# Mutation: off-by-one in initial counter
# Detects: `self.n = initial + 1` or `self.last_print_n = initial - 1`
def test_mutation_initial_off_by_one():
    t = make_tqdm(initial=10)
    assert t.n == 10, "A correct __init__ SHOULD set self.n == initial exactly"
    assert t.last_print_n == 10, "A correct __init__ SHOULD set self.last_print_n == initial exactly"
    t.close()


# Mutation: wrong variable for n vs last_print_n
# Detects: `self.n = 0` ignoring initial
def test_mutation_n_uses_initial():
    t = make_tqdm(initial=7)
    assert t.n == 7
    assert t.last_print_n == 7
    t.close()


# Mutation: `miniters = 0` vs `miniters = 1` when miniters=None
# Detects constant error in default miniters
def test_mutation_miniters_default_value():
    t = make_tqdm(miniters=None)
    assert t.miniters == 0, "A correct __init__ SHOULD set miniters=0 when miniters=None"
    t.close()


# Mutation: dynamic_miniters=True vs False when miniters explicitly given
# Detects: `dynamic_miniters = True` regardless of miniters
def test_mutation_dynamic_miniters_when_miniters_given():
    t = make_tqdm(miniters=1)
    assert t.dynamic_miniters is False, \
        "A correct __init__ SHOULD set dynamic_miniters=False when miniters is explicitly provided"
    t.close()


# Mutation: `dynamic_miniters = not True` => False when miniters=None
def test_mutation_dynamic_miniters_when_miniters_none():
    t = make_tqdm(miniters=None)
    assert t.dynamic_miniters is True, \
        "A correct __init__ SHOULD set dynamic_miniters=True when miniters=None"
    t.close()


# Mutation: mininterval None handling — wrong branch `if mininterval is not None`
def test_mutation_mininterval_none_becomes_zero():
    t = make_tqdm(mininterval=None)
    assert t.mininterval == 0, "A correct __init__ SHOULD convert mininterval=None to 0"
    t.close()


# Mutation: maxinterval None handling
def test_mutation_maxinterval_none_becomes_zero():
    t = make_tqdm(maxinterval=None)
    assert t.maxinterval == 0, "A correct __init__ SHOULD convert maxinterval=None to 0"
    t.close()


# Mutation: smoothing None handling
def test_mutation_smoothing_none_becomes_zero():
    t = make_tqdm(smoothing=None)
    assert t.smoothing == 0, "A correct __init__ SHOULD convert smoothing=None to 0"
    t.close()


# Mutation: desc=None should become '' (not None)
# Detects: `self.desc = desc` instead of `self.desc = desc or ''`
def test_mutation_desc_none_becomes_empty_string():
    t = make_tqdm(desc=None)
    assert t.desc == '', "A correct __init__ SHOULD convert desc=None to empty string"
    t.close()


# Mutation: position marking — position should be stored as -position (negative)
# Detects: `self.pos = position` instead of `self.pos = -position`
def test_mutation_position_stored_negative():
    t = make_tqdm(position=3)
    assert t.pos == -3, "A correct __init__ SHOULD store fixed position as -position"
    t.close()


# Mutation: position=None => auto-assigned (not -None or exception)
def test_mutation_position_none_auto():
    t = make_tqdm(position=None)
    # pos should be an integer (auto-assigned)
    assert isinstance(t.pos, int)
    t.close()


# Mutation: total inferred correctly from len(iterable) — not len(iterable)+1
def test_mutation_total_from_len():
    data = [1, 2, 3, 4, 5]
    t = make_tqdm(iterable=data, total=None)
    assert t.total == len(data), "A correct __init__ SHOULD set total=len(iterable) when total is None"
    t.close()


# Mutation: total not overwritten when explicitly given
def test_mutation_total_not_overwritten():
    t = make_tqdm(iterable=[1, 2, 3], total=50)
    assert t.total == 50, "A correct __init__ SHOULD preserve explicitly given total"
    t.close()


# Mutation: disable=None + TTY should NOT disable
def test_mutation_disable_none_with_tty():
    class FakeTTY(io.StringIO):
        def isatty(self):
            return True
    f = FakeTTY()
    t = tqdm(iterable=[1, 2], disable=None, file=f)
    # On a TTY, disable=None should NOT set disable=True
    # The bar should be active (not disabled)
    assert t.disable is not True or t.disable is False or t.disable is None, \
        "disable=None on a TTY should not set disable=True"
    t.close()


# Mutation: start_t and last_print_t are both set (not zero or None)
def test_mutation_time_counters_initialized():
    import time as _time
    t = make_tqdm()
    before = _time.time()
    # Both should be numeric and reasonable
    assert isinstance(t.start_t, float), "A correct __init__ SHOULD set start_t to a float timestamp"
    assert isinstance(t.last_print_t, float)
    assert t.start_t <= before + 1, "start_t should be a recent timestamp"
    assert t.last_print_t == t.start_t, "last_print_t SHOULD equal start_t at init"
    t.close()


# Mutation: avg_time initialized to None (not 0 or some other value)
def test_mutation_avg_time_none():
    t = make_tqdm()
    assert t.avg_time is None, "A correct __init__ SHOULD initialize avg_time to None"
    t.close()


# Mutation: postfix initialized to None before set_postfix call
# If postfix kwarg is falsy (None/0/False/''), self.postfix should remain None
def test_mutation_postfix_falsy_stays_none():
    t = make_tqdm(postfix=None)
    assert t.postfix is None
    t.close()


# Mutation: `or` vs `and` in disable=None + isatty check
# If file has no isatty, disable=None should NOT become True
def test_mutation_disable_none_no_isatty_attr():
    class NoIsatty:
        def write(self, s):
            pass
        def flush(self):
            pass
    f = NoIsatty()
    t = tqdm(iterable=None, disable=None, file=f)
    # hasattr(file, 'isatty') is False => condition fails => disable stays None (not True)
    assert t.disable is not True, \
        "A correct __init__ SHOULD NOT set disable=True when file has no isatty attribute"