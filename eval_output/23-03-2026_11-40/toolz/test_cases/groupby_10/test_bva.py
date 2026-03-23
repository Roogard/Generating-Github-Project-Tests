import pytest
from toolz.itertoolz import nth

def test_nth_zero_index_list():
    assert nth(0, [10, 20, 30]) == 10

def test_nth_first_index_list():
    assert nth(1, [10, 20, 30]) == 20

def test_nth_last_index_list():
    seq = [10, 20, 30]
    assert nth(len(seq) - 1, seq) == 30

def test_nth_just_before_last_list():
    seq = [10, 20, 30]
    assert nth(len(seq) - 2, seq) == 20

def test_nth_zero_index_tuple():
    assert nth(0, (10, 20, 30)) == 10

def test_nth_last_index_tuple():
    tup = (10, 20, 30)
    assert nth(len(tup) - 1, tup) == 30

def test_nth_zero_index_string():
    assert nth(0, 'ABC') == 'A'

def test_nth_middle_index_string():
    assert nth(1, 'ABC') == 'B'

def test_nth_last_index_string():
    s = 'ABC'
    assert nth(len(s) - 1, s) == 'C'

def test_nth_zero_index_sequence():
    class MySeq(Sequence):
        def __init__(self, data):
            self.data = list(data)
        def __getitem__(self, idx):
            return self.data[idx]
        def __len__(self):
            return len(self.data)
    seq = MySeq([5, 6, 7])
    assert nth(0, seq) == 5
    assert nth(2, seq) == 7

def test_nth_with_iterator_at_zero():
    it = iter([100, 200, 300])
    assert nth(0, it) == 100

def test_nth_with_iterator_at_middle():
    it = iter([100, 200, 300])
    assert nth(1, it) == 200

def test_nth_with_iterator_at_last():
    it = iter([100, 200, 300])
    assert nth(2, it) == 300

def test_nth_with_iterator_consumes():
    it = iter([100, 200, 300])
    nth(1, it)
    assert next(it) == 300

def test_nth_negative_index_raises_for_iterator():
    it = iter([1, 2, 3])
    with pytest.raises(ValueError):
        nth(-1, it)

def test_nth_index_out_of_range_list_raises():
    with pytest.raises(IndexError):
        nth(5, [1, 2, 3])

def test_nth_index_out_of_range_iterator_raises():
    it = iter([1, 2, 3])
    with pytest.raises(StopIteration):
        nth(5, it)

def test_nth_empty_list_raises():
    with pytest.raises(IndexError):
        nth(0, [])

def test_nth_empty_iterator_raises():
    it = iter([])
    with pytest.raises(StopIteration):
        nth(0, it)

def test_nth_single_element_list():
    assert nth(0, [42]) == 42

def test_nth_single_element_iterator():
    it = iter([42])
    assert nth(0, it) == 42