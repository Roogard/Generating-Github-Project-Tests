import pytest
from toolz.itertoolz import nth
from collections.abc import Sequence

# path: isinstance -> True -> return seq[n] (valid index)
def test_nth_list_valid_index():
    assert nth(1, [10, 20, 30]) == 20

# path: isinstance -> True -> return seq[n] (index 0)
def test_nth_tuple_zero_index():
    assert nth(0, (5, 6, 7)) == 5

# path: isinstance -> True -> raises IndexError (out of bounds)
def test_nth_list_index_error():
    with pytest.raises(IndexError):
        nth(5, [1, 2, 3])

# path: isinstance -> False -> next with islice -> successful retrieval
def test_nth_iterator_valid():
    it = iter(range(10, 40, 10))
    assert nth(1, it) == 20

# path: isinstance -> False -> next with islice -> StopIteration (iterator exhausted)
def test_nth_iterator_stop_iteration():
    it = iter([100])
    with pytest.raises(StopIteration):
        nth(1, it)

# path: isinstance -> False -> next with islice -> n=0 (first element)
def test_nth_iterator_zero_index():
    it = iter('abc')
    assert nth(0, it) == 'a'

# path: isinstance -> True -> return seq[n] with Sequence subclass
def test_nth_sequence_subclass():
    class MySeq(Sequence):
        def __init__(self, data):
            self.data = data
        def __getitem__(self, idx):
            return self.data[idx]
        def __len__(self):
            return len(self.data)
    seq = MySeq([9, 8, 7])
    assert nth(2, seq) == 7