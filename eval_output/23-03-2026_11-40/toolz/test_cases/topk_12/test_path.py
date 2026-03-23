import pytest
from toolz.itertoolz import partition_all
from toolz.utils import no_default

# Path enumeration for partition_all:
# 1. seq empty -> next(it) raises StopIteration -> return (generator stops immediately)
# 2. seq non-empty, n >= len(seq) such that only one zip_longest tuple is produced:
#    - next(it) succeeds
#    - for loop over `it` has zero iterations (because only one tuple total)
#    - prev[-1] is no_default? -> branch into try/except TypeError or else
#        a. seq has __len__ -> try block executes -> yield prev[:end]
#        b. seq has no __len__ -> TypeError -> except block -> binary search -> yield prev[:lo]
#    - Note: For single tuple case, prev[-1] is no_default only if len(seq) % n != 0? Actually if n >= len(seq) and seq length < n, then prev[-1] is no_default.
# 3. seq non-empty, multiple zip_longest tuples produced (n < len(seq)):
#    - next(it) succeeds
#    - for loop over `it` has >=1 iterations
#    - after loop, prev is last tuple
#    - prev[-1] is no_default? -> branch into try/except or else
#        a. seq has __len__ -> try block -> yield prev[:end]
#        b. seq has no __len__ -> TypeError -> except block -> binary search -> yield prev[:lo]
#        c. prev[-1] is not no_default -> else branch -> yield prev
# 4. Additional considerations: The try block inside prev[-1] is no_default branch includes a validation check that may raise LookupError (path: validation fails).
#    This is a rare error path when seq.__len__ is wrong/misbehaving.

# We'll cover feasible paths:

# path: seq empty -> StopIteration -> generator stops
def test_partition_all_empty_seq():
    result = list(partition_all(3, []))
    assert result == []

# path: seq non-empty, n >= len(seq), single tuple, prev[-1] is no_default, seq has __len__, validation passes
def test_partition_all_single_chunk_with_pad_has_length():
    # n=5, seq length=3 -> one tuple of length 5 with 2 no_default at end
    result = list(partition_all(5, [1, 2, 3]))
    assert result == [(1, 2, 3)]

# path: seq non-empty, n >= len(seq), single tuple, prev[-1] is no_default, seq has no __len__, triggers TypeError -> binary search
def test_partition_all_single_chunk_with_pad_no_length():
    # Use a generator that doesn't have __len__
    gen = (x for x in [1, 2])  # length 2, n=3
    result = list(partition_all(3, gen))
    assert result == [(1, 2)]

# path: seq non-empty, n >= len(seq), single tuple, prev[-1] is NOT no_default (i.e., seq length exactly n) -> else branch
def test_partition_all_single_chunk_full():
    result = list(partition_all(3, [1, 2, 3]))
    assert result == [(1, 2, 3)]

# path: seq non-empty, multiple tuples (n < len(seq)), for loop iterates >=1, prev[-1] is no_default, seq has __len__, validation passes
def test_partition_all_multiple_chunks_last_partial_has_length():
    result = list(partition_all(2, [1, 2, 3, 4, 5]))
    assert result == [(1, 2), (3, 4), (5,)]

# path: seq non-empty, multiple tuples, for loop iterates >=1, prev[-1] is no_default, seq has no __len__, triggers TypeError -> binary search
def test_partition_all_multiple_chunks_last_partial_no_length():
    gen = (x for x in [1, 2, 3, 4, 5])
    result = list(partition_all(2, gen))
    assert result == [(1, 2), (3, 4), (5,)]

# path: seq non-empty, multiple tuples, for loop iterates >=1, prev[-1] is NOT no_default (i.e., seq length multiple of n) -> else branch
def test_partition_all_multiple_chunks_full():
    result = list(partition_all(2, [1, 2, 3, 4]))
    assert result == [(1, 2), (3, 4)]

# path: seq non-empty, single tuple, prev[-1] is no_default, seq has __len__, validation fails -> raises LookupError
def test_partition_all_broken_length():
    class BrokenLenSequence:
        def __init__(self, data):
            self.data = data
        def __iter__(self):
            return iter(self.data)
        def __len__(self):
            # Return wrong length, causing validation failure
            return len(self.data) + 1

    seq = BrokenLenSequence([1, 2])
    # n=3, seq length reported as 3 but actual iteration yields only 2 elements
    # The zip_longest will produce one tuple: (1, 2, no_default)
    # In try block: len(seq) % n = 3 % 3 = 0 -> end = 0 -> prev[end-1] is prev[-1] which is no_default -> raises LookupError
    with pytest.raises(LookupError):
        list(partition_all(3, seq))

# Additional path: for loop iterates exactly once (minimum multiple-tuple case)
def test_partition_all_two_chunks_last_full():
    # n=2, seq length=3 -> two tuples: first from next(it), second from single iteration of for loop
    result = list(partition_all(2, [1, 2, 3]))
    assert result == [(1, 2), (3,)]

# Additional path: for loop iterates many times (more than one iteration)
def test_partition_all_many_iterations():
    result = list(partition_all(2, [1, 2, 3, 4, 5, 6, 7]))
    assert result == [(1, 2), (3, 4), (5, 6), (7,)]