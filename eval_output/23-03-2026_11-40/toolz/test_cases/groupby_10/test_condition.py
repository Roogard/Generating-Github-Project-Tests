from toolz.itertoolz import nth
import pytest

# condition: isinstance(seq, (tuple, list, Sequence)): True
def test_nth_with_list_true():
    # seq is list → condition True
    assert nth(1, [10, 20, 30]) == 20

# condition: isinstance(seq, (tuple, list, Sequence)): True
def test_nth_with_tuple_true():
    # seq is tuple → condition True
    assert nth(0, (5, 6, 7)) == 5

# condition: isinstance(seq, (tuple, list, Sequence)): True
def test_nth_with_sequence_subclass_true():
    # seq is a Sequence subclass → condition True
    class MySeq(Sequence):
        def __init__(self, data):
            self.data = list(data)
        def __getitem__(self, i):
            return self.data[i]
        def __len__(self):
            return len(self.data)
    ms = MySeq([100, 200, 300])
    assert nth(2, ms) == 300

# condition: isinstance(seq, (tuple, list, Sequence)): False
def test_nth_with_iterator_false():
    # seq is iterator → condition False
    assert nth(2, iter(range(10))) == 2

# condition: isinstance(seq, (tuple, list, Sequence)): False
def test_nth_with_generator_false():
    # seq is generator → condition False
    gen = (i*2 for i in range(5))
    assert nth(3, gen) == 6

# additional test for negative index (still condition True)
def test_nth_negative_index_true():
    # seq is list → condition True, negative index works
    assert nth(-1, [10, 20, 30]) == 30

# additional test for out-of-range (condition True) raises IndexError
def test_nth_index_error_true():
    with pytest.raises(IndexError):
        nth(10, [1, 2, 3])

# additional test for out-of-range (condition False) raises StopIteration
def test_nth_stop_iteration_false():
    with pytest.raises(StopIteration):
        nth(10, iter(range(5)))