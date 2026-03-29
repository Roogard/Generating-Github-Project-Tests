import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from black import EmptyLineTracker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_tracker():
    """Return a freshly constructed EmptyLineTracker."""
    return EmptyLineTracker()


def make_line(is_decorator=False, is_def=False, is_class=False,
              is_stub=False, is_flow_control=False, is_import=False,
              is_yield=False, depth=0, leaves=None):
    """
    Build a minimal MagicMock that looks enough like a black.Line
    for EmptyLineTracker to consume.
    """
    line = MagicMock()
    line.is_decorator = is_decorator
    line.is_def = is_def
    line.is_class = is_class
    line.is_stub = is_stub
    line.is_flow_control = is_flow_control
    line.is_import = is_import
    line.is_yield = is_yield
    line.depth = depth
    # .leaves is needed by some paths inside _maybe_empty_lines
    line.leaves = leaves if leaves is not None else []
    # Some branches check line.is_comment, line.is_triple_quoted_string, etc.
    line.is_comment = False
    line.is_triple_quoted_string = False
    return line


# ---------------------------------------------------------------------------
# Statement Coverage
# ---------------------------------------------------------------------------

# SC-1: Happy-path: _maybe_empty_lines returns (2, 0), previous_after == 0
#   → before = 2 - 0 = 2, after = 0, state updated
def test_statement_basic_before_after():
    tracker = make_tracker()
    # Patch the internal helper so we control its output precisely
    line = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 0)):
        before, after = tracker.maybe_empty_lines(line)
    # A correct implementation must subtract previous_after from before
    assert before == 2
    assert after == 0

# SC-2: previous_line is updated to current_line after the call
def test_statement_previous_line_updated():
    tracker = make_tracker()
    line = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 1)):
        tracker.maybe_empty_lines(line)
    assert tracker.previous_line is line

# SC-3: previous_after is updated to the new `after` value
def test_statement_previous_after_updated():
    tracker = make_tracker()
    line = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(0, 2)):
        tracker.maybe_empty_lines(line)
    assert tracker.previous_after == 2

# SC-4: The subtraction statement (before -= self.previous_after) executes;
#        previous_after from prior call reduces before in the next call.
def test_statement_subtraction_executes():
    tracker = make_tracker()
    line1 = make_line()
    line2 = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 1)):
        tracker.maybe_empty_lines(line1)      # sets previous_after = 1
    with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 0)):
        before, after = tracker.maybe_empty_lines(line2)
    # before should be 2 - 1 = 1
    assert before == 1
    assert after == 0


# ---------------------------------------------------------------------------
# Block Coverage
# ---------------------------------------------------------------------------

# The function is a single basic block (no branching at this level).
# The interesting block distinctions live in _maybe_empty_lines; we cover
# the entry block of maybe_empty_lines itself, ensuring every statement runs.

# BC-1: Entry block – first call, previous_after starts at 0
def test_block_entry_first_call():
    tracker = make_tracker()
    line = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(0, 0)):
        before, after = tracker.maybe_empty_lines(line)
    assert before == 0
    assert after == 0
    assert tracker.previous_after == 0
    assert tracker.previous_line is line

# BC-2: Continuation block – second call uses state set by first call
def test_block_continuation_second_call():
    tracker = make_tracker()
    line1 = make_line()
    line2 = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(3, 1)):
        tracker.maybe_empty_lines(line1)     # previous_after becomes 1
    with patch.object(tracker, '_maybe_empty_lines', return_value=(3, 0)):
        before, after = tracker.maybe_empty_lines(line2)
    # 3 - 1 = 2
    assert before == 2
    assert tracker.previous_line is line2

# BC-3: Result-assignment block produces correct tuple
def test_block_return_tuple():
    tracker = make_tracker()
    line = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(4, 2)):
        result = tracker.maybe_empty_lines(line)
    assert isinstance(result, tuple)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# Condition Coverage
# ---------------------------------------------------------------------------

# maybe_empty_lines itself contains no explicit boolean conditions; all
# branching resides inside _maybe_empty_lines.  We cover the one implicit
# condition that drives observable behavior: whether before - previous_after
# results in a positive, zero, or negative value (which a correct
# implementation should clamp to 0 or pass through, depending on contract).

# CC-1: before > previous_after  → subtraction yields positive  # before>pa: True
def test_condition_before_greater_than_previous_after():
    tracker = make_tracker()
    line = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 1)):
        tracker.maybe_empty_lines(line)   # previous_after = 1
    with patch.object(tracker, '_maybe_empty_lines', return_value=(3, 0)):
        before, _ = tracker.maybe_empty_lines(make_line())
    # 3 - 1 = 2  (positive)  # before>pa: True
    assert before == 2

# CC-2: before == previous_after  → subtraction yields zero  # before>pa: False (equal)
def test_condition_before_equals_previous_after():
    tracker = make_tracker()
    line = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(0, 2)):
        tracker.maybe_empty_lines(line)   # previous_after = 2
    with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 0)):
        before, _ = tracker.maybe_empty_lines(make_line())
    # 2 - 2 = 0  # before==pa: True (equal), difference is zero
    assert before == 0

# CC-3: before < previous_after  → subtraction yields negative  # before<pa: True
#   A correct implementation should NOT produce negative blank lines in output,
#   but the raw arithmetic is what the method returns before any clamping at
#   a higher level.  We assert the mathematical result is negative as a
#   property, so we know the subtraction was performed.
def test_condition_before_less_than_previous_after():
    tracker = make_tracker()
    line = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(0, 3)):
        tracker.maybe_empty_lines(line)   # previous_after = 3
    with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 0)):
        before, _ = tracker.maybe_empty_lines(make_line())
    # 1 - 3 = -2  # before<pa: True
    # The function performs arithmetic subtraction regardless of sign
    assert before == 1 - 3

# CC-4: after is True-y vs False-y (previous_after propagation)
#   after != 0  # after_nonzero: True
def test_condition_after_nonzero_propagates():
    tracker = make_tracker()
    line = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 2)):
        tracker.maybe_empty_lines(line)
    assert tracker.previous_after == 2   # nonzero propagated correctly

#   after == 0  # after_nonzero: False
def test_condition_after_zero_propagates():
    tracker = make_tracker()
    line = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 0)):
        tracker.maybe_empty_lines(line)
    assert tracker.previous_after == 0


# ---------------------------------------------------------------------------
# Path Coverage
# ---------------------------------------------------------------------------

# The function has a single linear path (no branches).  Path variety comes
# from the sequence of calls and the varying state of previous_after.

# PATH-1: Single call, previous_after starts at 0
#   path: entry → _maybe_empty_lines(1,0) → subtract 0 → store after=0 → return(1,0)
def test_path_single_call_no_prior_after():
    tracker = make_tracker()
    line = make_line()
    with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 0)):
        before, after = tracker.maybe_empty_lines(line)
    # path: entry → subtract(1-0) → return  # path: single call, pa=0
    assert before == 1
    assert after == 0

# PATH-2: Two calls; first sets previous_after, second is adjusted
#   path: call1 → store after=2 → call2 → subtract(3-2) → return(1,0)
def test_path_two_calls_adjustment():
    tracker = make_tracker()
    line1 = make_line()
    line2 = make_line()
    # path: call1 → pa becomes 2  # path: first call sets previous_after=2
    with patch.object(tracker, '_maybe_empty_lines', return_value=(0, 2)):
        tracker.maybe_empty_lines(line1)
    # path: call2 → before=3, subtract pa=2 → before=1  # path: second call pa=2
    with patch.object(tracker, '_maybe_empty_lines', return_value=(3, 0)):
        before, after = tracker.maybe_empty_lines(line2)
    assert before == 1
    assert after == 0
    assert tracker.previous_after == 0
    assert tracker.previous_line is line2

# PATH-3: Three calls – chain of state transitions
#   path: call1(pa→1) → call2(before 2-1=1, pa→3) → call3(before 4-3=1)
def test_path_three_call_chain():
    tracker = make_tracker()
    lines = [make_line(), make_line(), make_line()]
    results = []
    side_effects = [(1, 1), (2, 3), (4, 0)]
    for line, se in zip(lines, side_effects):
        with patch.object(tracker, '_maybe_empty_lines', return_value=se):
            results.append(tracker.maybe_empty_lines(line))
    # path: call1 before=1-0=1, pa→1; call2 before=2-1=1, pa→3; call3 before=4-3=1, pa→0
    assert results[0] == (1, 1)
    assert results[1] == (1, 3)
    assert results[2] == (1, 0)

# PATH-4: Verify previous_line tracks correctly across multiple calls
#   path: entry → update previous_line each call  # path: state update chain
def test_path_previous_line_chain():
    tracker = make_tracker()
    lines = [make_line(), make_line(), make_line()]
    for line in lines:
        with patch.object(tracker, '_maybe_empty_lines', return_value=(0, 0)):
            tracker.maybe_empty_lines(line)
    # A correct implementation must set previous_line to the most recent line
    assert tracker.previous_line is lines[-1]

# PATH-5: Zero-extra-lines path – both before and after are 0 throughout
#   path: entry → _maybe_empty_lines(0,0) → subtract 0 → return(0,0)
def test_path_all_zeros():
    tracker = make_tracker()
    for _ in range(3):
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(0, 0)):
            before, after = tracker.maybe_empty_lines(line)
        # path: all zero  # path: no blank lines ever
        assert before == 0
        assert after == 0

# PATH-6: Return value is always a 2-tuple regardless of inputs
#   path: any inputs → always returns Tuple[int, int]  # path: return type invariant
def test_path_return_is_always_tuple():
    tracker = make_tracker()
    for raw in [(0, 0), (1, 0), (2, 1), (0, 2)]:
        with patch.object(tracker, '_maybe_empty_lines', return_value=raw):
            result = tracker.maybe_empty_lines(make_line())
        assert isinstance(result, tuple) and len(result) == 2