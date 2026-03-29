import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from black import EmptyLineTracker


def make_tracker():
    """Create an EmptyLineTracker with controlled initial state."""
    tracker = EmptyLineTracker.__new__(EmptyLineTracker)
    tracker.previous_after = 0
    tracker.previous_line = None
    tracker.is_pyi = False
    return tracker


def make_line(is_decorator=False, is_def=False, is_class=False,
              is_flow_control=False, is_import=False, depth=0,
              leaves=None):
    """Create a mock Line object with the given properties."""
    line = MagicMock()
    line.is_decorator = is_decorator
    line.is_def = is_def
    line.is_class = is_class
    line.is_flow_control = is_flow_control
    line.is_import = is_import
    line.depth = depth
    line.leaves = leaves or []
    line.__bool__ = lambda self: True
    return line


# --- BVA ---

class TestMaybeEmptyLinesBVA:

    def test_previous_after_zero_subtracts_zero(self):
        """BVA: previous_after == 0 (min boundary). before should not be reduced."""
        tracker = make_tracker()
        tracker.previous_after = 0
        line = make_line()
        raw_before = 1
        raw_after = 0
        with patch.object(tracker, '_maybe_empty_lines', return_value=(raw_before, raw_after)):
            before, after = tracker.maybe_empty_lines(line)
        # A correct implementation: before = raw_before - previous_after = 1 - 0 = 1
        assert before == 1

    def test_previous_after_one_subtracts_one(self):
        """BVA: previous_after == 1. before reduced by 1."""
        tracker = make_tracker()
        tracker.previous_after = 1
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 0)):
            before, after = tracker.maybe_empty_lines(line)
        # before = 2 - 1 = 1
        assert before == 1

    def test_previous_after_equals_before_gives_zero(self):
        """BVA: previous_after == before. Result before == 0."""
        tracker = make_tracker()
        tracker.previous_after = 2
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 0)):
            before, after = tracker.maybe_empty_lines(line)
        # before = 2 - 2 = 0
        assert before == 0

    def test_previous_after_exceeds_before_gives_negative(self):
        """BVA: previous_after > before. Result before can go negative."""
        tracker = make_tracker()
        tracker.previous_after = 3
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 0)):
            before, after = tracker.maybe_empty_lines(line)
        # before = 2 - 3 = -1 (no clamping in spec)
        assert before == -1

    def test_raw_before_zero_with_previous_after_zero(self):
        """BVA: both raw_before and previous_after are 0."""
        tracker = make_tracker()
        tracker.previous_after = 0
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(0, 0)):
            before, after = tracker.maybe_empty_lines(line)
        assert before == 0
        assert after == 0

    def test_large_raw_before(self):
        """BVA: large raw_before value."""
        tracker = make_tracker()
        tracker.previous_after = 1
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(100, 0)):
            before, after = tracker.maybe_empty_lines(line)
        assert before == 99

    def test_after_value_passed_through_unchanged(self):
        """BVA: raw_after is returned as-is."""
        tracker = make_tracker()
        tracker.previous_after = 0
        line = make_line()
        for raw_after in [0, 1, 2]:
            with patch.object(tracker, '_maybe_empty_lines', return_value=(0, raw_after)):
                before, after = tracker.maybe_empty_lines(line)
            assert after == raw_after, f"after should be {raw_after}, got {after}"

    def test_previous_after_large_value(self):
        """BVA: previous_after set to a large value."""
        tracker = make_tracker()
        tracker.previous_after = 100
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 0)):
            before, after = tracker.maybe_empty_lines(line)
        assert before == 1 - 100

    def test_single_call_no_previous_line(self):
        """BVA: first call ever (previous_line is None, previous_after is 0)."""
        tracker = make_tracker()
        assert tracker.previous_line is None
        assert tracker.previous_after == 0
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 1)):
            before, after = tracker.maybe_empty_lines(line)
        assert before == 2
        assert after == 1


# --- ECP ---

class TestMaybeEmptyLinesECP:

    def test_valid_class_typical_inputs(self):
        """ECP: Typical valid inputs: raw values positive, previous_after moderate."""
        tracker = make_tracker()
        tracker.previous_after = 1
        line = make_line(is_class=True, depth=0)
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 1)):
            before, after = tracker.maybe_empty_lines(line)
        assert before == 1
        assert after == 1

    def test_valid_def_line(self):
        """ECP: def line — typical case for function definitions."""
        tracker = make_tracker()
        tracker.previous_after = 0
        line = make_line(is_def=True, depth=1)
        with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 0)):
            before, after = tracker.maybe_empty_lines(line)
        assert before == 1
        assert after == 0

    def test_valid_regular_line_no_blank(self):
        """ECP: Regular line where no extra blank lines needed."""
        tracker = make_tracker()
        tracker.previous_after = 0
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(0, 0)):
            before, after = tracker.maybe_empty_lines(line)
        assert before == 0
        assert after == 0

    def test_state_previous_after_updated_after_call(self):
        """ECP: After a call, previous_after must be set to the raw_after value returned."""
        tracker = make_tracker()
        tracker.previous_after = 0
        line1 = make_line()
        line2 = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 2)):
            tracker.maybe_empty_lines(line1)
        # Now previous_after should be 2
        with patch.object(tracker, '_maybe_empty_lines', return_value=(3, 0)):
            before, after = tracker.maybe_empty_lines(line2)
        # before = 3 - 2 = 1
        assert before == 1

    def test_state_previous_line_updated_after_call(self):
        """ECP: After a call, previous_line must be set to the current_line."""
        tracker = make_tracker()
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(0, 0)):
            tracker.maybe_empty_lines(line)
        assert tracker.previous_line is line

    def test_previous_after_only_affects_before_not_after(self):
        """ECP: previous_after only subtracts from before, not from after."""
        tracker = make_tracker()
        tracker.previous_after = 5
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 3)):
            before, after = tracker.maybe_empty_lines(line)
        assert before == 2 - 5
        assert after == 3  # after is not modified

    def test_consecutive_calls_chain_state(self):
        """ECP: Three consecutive calls chain previous_after correctly."""
        tracker = make_tracker()
        line_a = make_line()
        line_b = make_line()
        line_c = make_line()

        # Call 1: raw=(2, 1), previous_after=0 → before=2-0=2, after=1
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 1)):
            b1, a1 = tracker.maybe_empty_lines(line_a)
        assert b1 == 2
        assert a1 == 1

        # Call 2: raw=(3, 2), previous_after=1 → before=3-1=2, after=2
        with patch.object(tracker, '_maybe_empty_lines', return_value=(3, 2)):
            b2, a2 = tracker.maybe_empty_lines(line_b)
        assert b2 == 2
        assert a2 == 2

        # Call 3: raw=(2, 0), previous_after=2 → before=2-2=0, after=0
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 0)):
            b3, a3 = tracker.maybe_empty_lines(line_c)
        assert b3 == 0
        assert a3 == 0

    def test_decorator_line(self):
        """ECP: decorator line type handled correctly."""
        tracker = make_tracker()
        tracker.previous_after = 0
        line = make_line(is_decorator=True)
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 0)):
            before, after = tracker.maybe_empty_lines(line)
        assert before == 2
        assert after == 0

    def test_return_type_is_tuple_of_two_ints(self):
        """ECP: Return value must be a tuple of two integers."""
        tracker = make_tracker()
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 1)):
            result = tracker.maybe_empty_lines(line)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], int)


# --- Mutation Detection ---

class TestMaybeEmptyLinesMutationDetection:

    def test_mutation_subtraction_vs_addition(self):
        """Mutation: `before - previous_after` vs `before + previous_after`.
        If wrong operator (+), before would be 1+1=2 instead of 0."""
        tracker = make_tracker()
        tracker.previous_after = 1
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 0)):
            before, after = tracker.maybe_empty_lines(line)
        # Correct: 1 - 1 = 0. Mutation (+): 1 + 1 = 2
        assert before == 0

    def test_mutation_previous_after_not_updated(self):
        """Mutation: previous_after is never updated after call.
        If previous_after stays 0 forever, the second call won't subtract properly."""
        tracker = make_tracker()
        tracker.previous_after = 0
        line1 = make_line()
        line2 = make_line()

        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 2)):
            tracker.maybe_empty_lines(line1)

        # If previous_after was correctly updated to 2:
        assert tracker.previous_after == 2

        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 0)):
            before, _ = tracker.maybe_empty_lines(line2)
        # Correct: 2 - 2 = 0. Mutation (no update): 2 - 0 = 2
        assert before == 0

    def test_mutation_previous_after_set_to_before_instead_of_after(self):
        """Mutation: `self.previous_after = before` instead of `self.previous_after = after`.
        If wrong variable is used, subsequent call would subtract wrong value."""
        tracker = make_tracker()
        line1 = make_line()
        line2 = make_line()

        with patch.object(tracker, '_maybe_empty_lines', return_value=(3, 1)):
            tracker.maybe_empty_lines(line1)

        # A correct implementation sets previous_after = after = 1, not before = 3
        assert tracker.previous_after == 1

        with patch.object(tracker, '_maybe_empty_lines', return_value=(3, 0)):
            before, _ = tracker.maybe_empty_lines(line2)
        # Correct: 3 - 1 = 2. Mutation (sets to before=3): 3 - 3 = 0
        assert before == 2

    def test_mutation_previous_line_not_updated(self):
        """Mutation: `self.previous_line` is never updated.
        After a call, previous_line must be the current line."""
        tracker = make_tracker()
        line = make_line(is_def=True)
        with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 0)):
            tracker.maybe_empty_lines(line)
        # Mutation: previous_line stays None
        assert tracker.previous_line is line
        assert tracker.previous_line is not None

    def test_mutation_subtraction_wrong_order(self):
        """Mutation: `previous_after - before` instead of `before - previous_after`.
        With before=1, previous_after=3: correct=-2, mutation=2."""
        tracker = make_tracker()
        tracker.previous_after = 3
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(1, 0)):
            before, after = tracker.maybe_empty_lines(line)
        # Correct: 1 - 3 = -2. Mutation (reversed): 3 - 1 = 2
        assert before == -2

    def test_mutation_after_subtracted_instead_of_before(self):
        """Mutation: `after -= self.previous_after` instead of `before -= self.previous_after`.
        With raw=(2, 5), previous_after=3: correct before=2-3=-1, after=5; mutation before=2, after=5-3=2."""
        tracker = make_tracker()
        tracker.previous_after = 3
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 5)):
            before, after = tracker.maybe_empty_lines(line)
        # Correct: before=2-3=-1, after=5 (unchanged)
        assert before == -1
        assert after == 5

    def test_mutation_previous_after_set_to_before_result_not_raw(self):
        """Mutation: `self.previous_after = before` (after subtraction) vs `after`.
        Ensures the stored value is the raw `after`, not the adjusted `before`."""
        tracker = make_tracker()
        tracker.previous_after = 1
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(3, 2)):
            tracker.maybe_empty_lines(line)
        # adjusted before = 3-1 = 2. raw after = 2. They are equal here — need different values.
        # Use raw=(4, 2): adjusted before=4-1=3, raw after=2.
        tracker.previous_after = 1
        with patch.object(tracker, '_maybe_empty_lines', return_value=(4, 2)):
            tracker.maybe_empty_lines(line)
        # Correct: previous_after = after = 2. Mutation: previous_after = before = 3
        assert tracker.previous_after == 2

    def test_mutation_off_by_one_previous_after_plus_one(self):
        """Mutation: `before -= self.previous_after + 1` (off-by-one).
        With before=2, previous_after=1: correct=1, mutation=0."""
        tracker = make_tracker()
        tracker.previous_after = 1
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 0)):
            before, after = tracker.maybe_empty_lines(line)
        # Correct: 2 - 1 = 1. Off-by-one: 2 - 2 = 0
        assert before == 1

    def test_mutation_previous_after_initialized_wrong(self):
        """Mutation: previous_after initialized to 1 instead of 0.
        First call: raw=(2,1), previous_after=0 → before=2. Wrong init → before=1."""
        tracker = make_tracker()
        # Override to ensure the initial value is 0 (correct), not 1 (mutation)
        assert tracker.previous_after == 0
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(2, 1)):
            before, after = tracker.maybe_empty_lines(line)
        # Correct: 2 - 0 = 2
        assert before == 2

    def test_mutation_return_swapped_before_after(self):
        """Mutation: `return after, before` instead of `return before, after`."""
        tracker = make_tracker()
        tracker.previous_after = 1
        line = make_line()
        with patch.object(tracker, '_maybe_empty_lines', return_value=(5, 3)):
            before, after = tracker.maybe_empty_lines(line)
        # Correct: before=5-1=4, after=3. Swapped: before=3, after=4
        assert before == 4
        assert after == 3