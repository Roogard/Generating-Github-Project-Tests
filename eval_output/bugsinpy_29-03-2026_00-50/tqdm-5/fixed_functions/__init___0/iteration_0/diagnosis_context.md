## Trigger Test(s)

```python
# test_blackbox.py
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


# ECP: Valid — unit_scale=1024 (numeric)
def test_ecp_valid_unit_scale_numeric():
    t = make_tqdm(unit_scale=1024)
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
```

```python
# test_whitebox.py
import sys
import io
import pytest
from tqdm._tqdm import tqdm

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_file():
    """Return a StringIO that looks like a real TTY-like stream."""
    f = io.StringIO()
    # tqdm checks isatty; default StringIO has no isatty, so add one
    f.isatty = lambda: True
    return f


def close(t):
    """Close a tqdm instance silently."""
    try:
        t.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Statement Coverage
# ---------------------------------------------------------------------------
# Every executable statement should be reached at least once.

def test_stmt_basic_no_iterable():
    # path: file=None → stderr, disable=False, no kwargs, no iterable,
    #       all defaults, gui=False branch
    f = make_file()
    t = tqdm(file=f)
    # A correct tqdm SHOULD initialise n to initial (default 0)
    assert t.n == 0
    assert t.disable is False
    assert t.iterable is None
    close(t)


def test_stmt_disable_true_early_return():
    # path: disable=True → early return after setting minimal attrs
    f = make_file()
    t = tqdm(iterable=[1, 2, 3], disable=True, initial=5, file=f)
    assert t.disable is True
    assert t.n == 5
    assert t.iterable == [1, 2, 3]
    close(t)


def test_stmt_disable_none_non_tty():
    # path: disable=None + file without isatty returning False → disable=True
    f = io.StringIO()          # no isatty attribute at all on plain StringIO
    f.isatty = lambda: False   # explicitly non-TTY
    t = tqdm(iterable=range(3), disable=None, file=f)
    assert t.disable is True
    close(t)


def test_stmt_disable_none_tty():
    # path: disable=None + file.isatty() == True → NOT disabled
    f = make_file()
    t = tqdm(iterable=[1], disable=None, file=f)
    assert t.disable is False
    close(t)


def test_stmt_kwargs_nested_deprecation():
    # path: kwargs present with "nested" key → TqdmDeprecationWarning raised
    f = make_file()
    from tqdm._tqdm import TqdmDeprecationWarning
    with pytest.raises(TqdmDeprecationWarning):
        tqdm(file=f, nested=True)


def test_stmt_kwargs_unknown():
    # path: kwargs present WITHOUT "nested" → TqdmKeyError raised
    f = make_file()
    from tqdm._tqdm import TqdmKeyError
    with pytest.raises(TqdmKeyError):
        tqdm(file=f, unknown_arg=42)


def test_stmt_total_from_len():
    # path: total=None, iterable has __len__ → total set from len()
    f = make_file()
    lst = [1, 2, 3, 4]
    t = tqdm(iterable=lst, file=f)
    assert t.total == len(lst)
    close(t)


def test_stmt_total_no_len():
    # path: total=None, iterable has no __len__ → total stays None
    f = make_file()

    def gen():
        yield 1

    t = tqdm(iterable=gen(), file=f)
    assert t.total is None
    close(t)


def test_stmt_miniters_none():
    # path: miniters=None → miniters=0, dynamic_miniters=True
    f = make_file()
    t = tqdm(file=f, miniters=None)
    assert t.miniters == 0
    assert t.dynamic_miniters is True
    close(t)


def test_stmt_miniters_given():
    # path: miniters given → dynamic_miniters=False
    f = make_file()
    t = tqdm(file=f, miniters=5)
    assert t.miniters == 5
    assert t.dynamic_miniters is False
    close(t)


def test_stmt_mininterval_none():
    # path: mininterval=None → mininterval=0
    f = make_file()
    t = tqdm(file=f, mininterval=None)
    assert t.mininterval == 0
    close(t)


def test_stmt_maxinterval_none():
    # path: maxinterval=None → maxinterval=0
    f = make_file()
    t = tqdm(file=f, maxinterval=None)
    assert t.maxinterval == 0
    close(t)


def test_stmt_smoothing_none():
    # path: smoothing=None → smoothing=0
    f = make_file()
    t = tqdm(file=f, smoothing=None)
    assert t.smoothing == 0
    close(t)


def test_stmt_bar_format_unicode():
    # path: bar_format given + ascii=False → bar_format converted to unicode
    f = make_file()
    t = tqdm(file=f, bar_format='{l_bar}{bar}', ascii=False)
    assert isinstance(t.bar_format, str)
    close(t)


def test_stmt_postfix_dict():
    # path: postfix is a dict → set_postfix called
    f = make_file()
    t = tqdm(file=f, postfix={'key': 'val'})
    # A correct tqdm SHOULD store postfix information
    assert t.postfix is not None
    close(t)


def test_stmt_postfix_non_dict():
    # path: postfix is truthy but not a dict → TypeError in set_postfix
    #       → self.postfix = postfix (raw assignment)
    f = make_file()
    t = tqdm(file=f, postfix="raw_string")
    assert t.postfix == "raw_string"
    close(t)


def test_stmt_position_none():
    # path: position=None → _get_free_pos used
    f = make_file()
    t = tqdm(file=f, position=None)
    # pos should be a non-negative int (free position)
    assert isinstance(t.pos, int)
    assert t.pos >= 0
    close(t)


def test_stmt_position_given():
    # path: position explicitly set → pos = -position
    f = make_file()
    t = tqdm(file=f, position=2)
    # A correct tqdm SHOULD store position as -position internally
    assert t.pos == -2
    close(t)


def test_stmt_gui_false_printer():
    # path: gui=False → status_printer initialised (sp attribute exists)
    f = make_file()
    t = tqdm(file=f, gui=False)
    assert hasattr(t, 'sp')
    close(t)


def test_stmt_gui_true_no_printer():
    # path: gui=True → sp NOT set
    f = make_file()
    t = tqdm(file=f, gui=True)
    assert not hasattr(t, 'sp')
    close(t)


def test_stmt_initial_nonzero():
    # path: initial != 0 → last_print_n and n both set to initial
    f = make_file()
    t = tqdm(file=f, initial=10, total=100)
    assert t.n == 10
    assert t.last_print_n == 10
    close(t)


def test_stmt_start_t_set():
    # start_t and last_print_t must be set (not None) after init
    f = make_file()
    t = tqdm(file=f)
    assert t.start_t is not None
    assert t.last_print_t is not None
    close(t)


# ---------------------------------------------------------------------------
# Block Coverage
# ---------------------------------------------------------------------------
# Every basic block (contiguous straight-line code between branch points)
# must be executed at least once.

# Most blocks are already exercised above. The following tests target blocks
# that are *not* fully covered by the statement tests.

def test_block_disable_none_no_isatty_attr():
    # disable=None + file has NO isatty attr → hasattr check is False
    # → disable stays None (not True), progress bar is NOT disabled
    # (disable=None is falsy, so the if-disable block is skipped)
    f = io.StringIO()          # no isatty at all
    # We must add isatty returning True so non-TTY branch is NOT taken
    f.isatty = lambda: True
    t = tqdm(iterable=[1], disable=None, file=f)
    assert t.disable is False   # a correct tqdm should not disable on TTY
    close(t)


def test_block_bar_format_with_ascii_true():
    # path: bar_format given BUT ascii=True → conversion block NOT entered
    f = make_file()
    t = tqdm(file=f, bar_format='{l_bar}{bar}', ascii=True)
    # bar_format should still be set
    assert t.bar_format == '{l_bar}{bar}'
    close(t)


def test_block_bar_format_none():
    # path: bar_format=None → conversion block NOT entered
    f = make_file()
    t = tqdm(file=f, bar_format=None, ascii=False)
    assert t.bar_format is None
    close(t)


def test_block_desc_empty():
    # desc=None → self.desc = ''
    f = make_file()
    t = tqdm(file=f, desc=None)
    assert t.desc == ''
    close(t)


def test_block_desc_given():
    # desc non-None → self.desc = desc
    f = make_file()
    t = tqdm(file=f, desc='Loading')
    assert t.desc == 'Loading'
    close(t)


def test_block_gui_true_pos_nonzero():
    # gui=True + position=1 → pos set negative, but moveto block skipped
    f = make_file()
    t = tqdm(file=f, gui=True, position=1)
    assert t.pos == -1
    assert not hasattr(t, 'sp')
    close(t)


# ---------------------------------------------------------------------------
# Condition Coverage
# ---------------------------------------------------------------------------
# Each boolean sub-expression must be True in some test and False in another.

# Condition: `disable is None and hasattr(file, "isatty") and not file.isatty()`
# Sub-expressions: A = (disable is None), B = hasattr(file, "isatty"), C = not file.isatty()

def test_cond_disable_none_has_isatty_not_tty():
    # A=True, B=True, C=True → disable becomes True
    f = io.StringIO()
    f.isatty = lambda: False
    t = tqdm(iterable=[], disable=None, file=f)
    assert t.disable is True
    close(t)


def test_cond_disable_not_none():
    # A=False (disable=False, not None) → whole condition is False
    f = make_file()
    t = tqdm(iterable=[], disable=False, file=f)
    assert t.disable is False
    close(t)


def test_cond_disable_none_tty():
    # A=True, B=True, C=False → condition False, disable stays None→False
    f = make_file()  # isatty() returns True
    t = tqdm(iterable=[], disable=None, file=f)
    assert t.disable is False
    close(t)


# Condition: `if disable:`
def test_cond_disable_true():
    # disable=True → early return
    f = make_file()
    t = tqdm(disable=True, file=f)
    assert t.disable is True
    close(t)


def test_cond_disable_false():
    # disable=False → normal init
    f = make_file()
    t = tqdm(disable=False, file=f)
    assert t.disable is False
    close(t)


# Condition: `if kwargs:` — "nested" sub-condition
def test_cond_kwargs_nested_key():
    # kwargs truthy, "nested" in kwargs → TqdmDeprecationWarning
    from tqdm._tqdm import TqdmDeprecationWarning
    f = make_file()
    with pytest.raises(TqdmDeprecationWarning):
        tqdm(file=f, nested=True)  # "nested" in kwargs: True


def test_cond_kwargs_no_nested_key():
    # kwargs truthy, "nested" NOT in kwargs → TqdmKeyError
    from tqdm._tqdm import TqdmKeyError
    f = make_file()
    with pytest.raises(TqdmKeyError):
        tqdm(file=f, foo=1)  # "nested" in kwargs: False


# Condition: `if total is None and iterable is not None:`
def test_cond_total_none_iterable_not_none():
    # total=None (True), iterable not None (True) → try len()
    f = make_file()
    t = tqdm(iterable=[1, 2], total=None, file=f)
    assert t.total == 2
    close(t)


def test_cond_total_given():
    # total not None (False) → block skipped
    f = make_file()
    t = tqdm(iterable=[1, 2], total=99, file=f)
    assert t.total == 99
    close(t)


def test_cond_total_none_iterable_none():
    # total=None (True), iterable=None (False) → block skipped
    f = make_file()
    t = tqdm(iterable=None, total=None, file=f)
    assert t.total is None
    close(t)


# Condition: `if miniters is None:`
def test_cond_miniters_none_true():
    # miniters=None → dynamic_miniters=True
    f = make_file()
    t = tqdm(file=f, miniters=None)
    assert t.dynamic_miniters is True
    close(t)


def test_cond_miniters_none_false():
    # miniters=2 → dynamic_miniters=False
    f = make_file()
    t = tqdm(file=f, miniters=2)
    assert t.dynamic_miniters is False
    close(t)


# Condition: `if mininterval is None:`
def test_cond_mininterval_none_true():
    f = make_file()
    t = tqdm(file=f, mininterval=None)
    assert t.mininterval == 0
    close(t)


def test_cond_mininterval_none_false():
    f = make_file()
    t = tqdm(file=f, mininterval=0.5)
    assert t.mininterval == 0.5
    close(t)


# Condition: `if maxinterval is None:`
def test_cond_maxinterval_none_true():
    f = make_file()
    t = tqdm(file=f, maxinterval=None)
    assert t.maxinterval == 0
    close(t)


def test_cond_maxinterval_none_false():
    f = make_file()
    t = tqdm(file=f, maxinterval=20.0)
    assert t.maxinterval == 20.0
    close(t)


# Condition: `if ascii is None:`
def test_cond_ascii_none():
    # ascii=None → derived from _supports_unicode(file)
    f = make_file()
    t = tqdm(file=f, ascii=None)
    assert isinstance(t.ascii, bool)
    close(t)


def test_cond_ascii_given_true():
    # ascii=True → used directly
    f = make_file()
    t = tqdm(file=f, ascii=True)
    assert t.ascii is True
    close(t)


def test_cond_ascii_given_false():
    # ascii=False → used directly
    f = make_file()
    t = tqdm(file=f, ascii=False)
    assert t.ascii is False
    close(t)


# Condition: `if bar_format and not ascii:`
def test_cond_bar_format_and_not_ascii_both_true():
    # bar_format truthy (True) AND not ascii → True → convert to unicode
    f = make_file()
    t = tqdm(file=f, bar_format='{bar}', ascii=False)
    assert t.bar_format is not None
    close(t)


def test_cond_bar_format_false():
    # bar_format=None → condition False; no conversion
    f = make_file()
    t = tqdm(file=f, bar_format=None, ascii=False)
    assert t.bar_format is None
    close(t)


def test_cond_bar_format_ascii_true():
    # bar_format truthy BUT ascii=True → not ascii is False → no conversion
    f = make_file()
    t = tqdm(file=f, bar_format='{bar}', ascii=True)
    assert t.bar_format == '{bar}'
    close(t)


# Condition: `if smoothing is None:`
def test_cond_smoothing_none_true():
    f = make_file()
    t = tqdm(file=f, smoothing=None)
    assert t.smoothing == 0
    close(t)


def test_cond_smoothing_none_false():
    f = make_file()
    t = tqdm(file=f, smoothing=0.5)
    assert t.smoothing == 0.5
    close(t)


# Condition: `if postfix:`
def test_cond_postfix_truthy():
    # postfix is truthy (dict) → set_postfix path
    f = make_file()
    t = tqdm(file=f, postfix={'a': 1})
    assert t.postfix is not None
    close(t)


def test_cond_postfix_falsy():
    # postfix=None → block skipped, self.postfix stays None
    f = make_file()
    t = tqdm(file=f, postfix=None)
    assert t.postfix is None
    close(t)


# Condition: `if position is None:`
def test_cond_position_none_true():
    f = make_file()
    t = tqdm(file=f, position=None)
    assert t.pos >= 0
    close(t)


def test_cond_position_none_false():
    f = make_file()
    t = tqdm(file=f, position=3)
    assert t.pos == -3   # stored as -position
    close(t)


# Condition: `if not gui:`
def test_cond_gui_false_sp_exists():
    # not gui → True → sp initialised
    f = make_file()
    t = tqdm(file=f, gui=False)
    assert hasattr(t, 'sp')
    close(t)


def test_cond_gui_true_sp_missing():
    # not gui → False → sp NOT initialised
    f = make_file()
    t = tqdm(file=f, gui=True)
    assert not hasattr(t, 'sp')
    close(t)


# ---------------------------------------------------------------------------
# Path Coverage
# ---------------------------------------------------------------------------

def test_path_disable_true_early_exit():
    # path: file default (stderr) → disable=True → early return
    t = tqdm(iterable=[1], disable=True)
    assert t.disable is True
    assert t.n == 0
    close(t)


def test_path_disable_none_non_tty_early_exit():
    # path: disable=None → non-TTY file → disable=True → early return
    f = io.StringIO()
    f.isatty = lambda: False
    t = tqdm(iterable=range(5), disable=None, file=f)
    assert t.disable is True
    close(t)


def test_path_kwargs_nested_raises():
    # path: not disabled → kwargs with "nested" → raise TqdmDeprecationWarning
    from tqdm._tqdm import TqdmDeprecationWarning
    with pytest.raises(TqdmDeprecationWarning):
        tqdm(nested=True, file=make_file())


def test_path_kwargs_unknown_raises():
    # path: not disabled → kwargs without "nested" → raise TqdmKeyError
    from tqdm._tqdm import TqdmKeyError
    with pytest.raises(TqdmKeyError):
        tqdm(file=make_file(), bogus=99)


def test_path_full_normal_with_iterable():
    # path: no disable, no kwargs, iterable with len, all defaults, gui=False
    # → full init including sp, moveto (pos==0 so inner if-pos skipped)
    f = make_file()
    data = list(range(10))
    t = tqdm(iterable=data, file=f)
    assert t.total == len(data)
    assert t.n == 0
    assert t.disable is False
    assert hasattr(t, 'sp')
    assert t.start_t is not None
    close(t)


def test_path_full_normal_no_iterable():
    # path: no disable, no kwargs, iterable=None → total=None, gui=False
    f = make_file()
    t = tqdm(file=f)
    assert t.total is None
    assert t.iterable is None
    assert hasattr(t, 'sp')
    close(t)


def test_path_generator_iterable_no_total():
    # path: iterable without __len__ → total remains None after try/except
    f = make_file()
    t = tqdm(iterable=(x for x in range(3)), file=f)
    assert t.total is None
    close(t)


def test_path_gui_true_no_sp():
    # path: all normal, gui=True → sp block skipped entirely
    f = make_file()
    t = tqdm(file=f, gui=True, total=5)
    assert not hasattr(t, 'sp')
    assert t.gui is True
    close(t)


def test_path_position_given_nonzero_gui_false():
    # path: position=1 → pos=-1 (nonzero) → gui=False → moveto calls executed
    f = make_file()
    t = tqdm(file=f, position=1, total=10)
    assert t.pos == -1
    assert hasattr(t, 'sp')
    close(t)


def test_path_all_none_overrides():
    # path: mininterval=None, maxinterval=None, smoothing=None, miniters=None
    #       → all set to 0; dynamic_miniters=True
    f = make_file()
    t = tqdm(file=f, mininterval=None, maxinterval=None,
             smoothing=None, miniters=None)
    assert t.mininterval == 0
    assert t.maxinterval == 0
    assert t.smoothing == 0
    assert t.miniters == 0
    assert t.dynamic_miniters is True
    close(t)


def test_path_postfix_dict_then_set_postfix():
    # path: postfix is dict → set_postfix(refresh=False, **postfix) called
    f = make_file()
    t = tqdm(file=f, total=10, postfix={'loss': 0.5})
    assert t.postfix is not None
    close(t)


def test_path_postfix_non_dict_typeerror():
    # path: postfix truthy but not dict → TypeError in set_postfix
    #       → self.postfix = postfix (raw value assigned)
    f = make_file()
    t = tqdm(file=f, total=10, postfix=42)
    assert t.postfix == 42
    close(t)


def test_path_initial_nonzero_counters():
    # path: initial=7 → last_print_n=7, n=7 throughout
    f = make_file()
    t = tqdm(file=f, total=100, initial=7)
    assert t.n == 7
    assert t.last_print_n == 7
    close(t)


def test_path_desc_given_stored():
    # path: desc='Test' → self.desc = 'Test'
    f = make_file()
    t = tqdm(file=f, desc='Test')
    assert t.desc == 'Test'
    close(t)


def test_path_unit_scale_set():
    # path: unit_scale=True → stored directly
    f = make_file()
    t = tqdm(file=f, unit_scale=True, total=1000)
    assert t.unit_scale is True
    close(t)


def test_path_avg_time_none_on_init():
    # A freshly created tqdm SHOULD have avg_time=None (no speed data yet)
    f = make_file()
    t = tqdm(file=f)
    assert t.avg_time is None
    close(t)
```

## Error Message(s)

### [FAILURE] test_ecp_valid_unit_scale_numeric (type: blackbox)
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-5\generated_tests\__init___0\test_blackbox.py:207: in test_ecp_valid_unit_scale_numeric
    t = make_tqdm(unit_scale=1024)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^
eval_output\bugsinpy_29-03-2026_00-50\tqdm-5\generated_tests\__init___0\test_blackbox.py:11: in make_tqdm
    return tqdm(**kwargs)
           ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpjexh75yk\tqdm\_tqdm.py:859: in __init__
    self.sp(self.__repr__(elapsed=0))
            ^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpjexh75yk\tqdm\_tqdm.py:885: in __repr__
    return self.format_meter(
..\..\..\..\AppData\Local\Temp\tmpjexh75yk\tqdm\_tqdm.py:267: in format_meter
    total *= unit_scale
E   TypeError: unsupported operand type(s) for *=: 'NoneType' and 'int'
```

### [FAILURE] test_stmt_disable_none_tty (type: whitebox)
Assertion: assert t.disable is False
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-5\generated_tests\__init___0\test_whitebox.py:66: in test_stmt_disable_none_tty
    assert t.disable is False
E   assert None is False
E    +  where None =   0%|          | 0/1 [00:00<?, ?it/s].disable
```

### [FAILURE] test_block_disable_none_no_isatty_attr (type: whitebox)
Assertion: assert t.disable is False   # a correct tqdm should not disable on TTY
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-5\generated_tests\__init___0\test_whitebox.py:245: in test_block_disable_none_no_isatty_attr
    assert t.disable is False   # a correct tqdm should not disable on TTY
    ^^^^^^^^^^^^^^^^^^^^^^^^^
E   assert None is False
E    +  where None =   0%|          | 0/1 [00:00<?, ?it/s].disable
```

### [FAILURE] test_cond_disable_none_tty (type: whitebox)
Assertion: assert t.disable is False
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-5\generated_tests\__init___0\test_whitebox.py:320: in test_cond_disable_none_tty
    assert t.disable is False
E   assert None is False
E    +  where None = 0it [00:00, ?it/s].disable
```
