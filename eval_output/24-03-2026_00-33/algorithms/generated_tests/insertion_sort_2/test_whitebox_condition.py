from algorithms.sorting.insertion_sort import insertion_sort

# condition: pos>0: True, array[pos-1]>cursor: True → while loop executes
def test_insertion_sort_while_both_true():
    array = [3, 1, 2]
    result = insertion_sort(array)
    assert result == [1, 2, 3]

# condition: pos>0: True, array[pos-1]>cursor: False → while loop does not execute
def test_insertion_sort_while_first_true_second_false():
    array = [1, 3, 2]
    result = insertion_sort(array)
    assert result == [1, 2, 3]

# condition: pos>0: False, array[pos-1]>cursor: True → while loop does not execute (short-circuit)
def test_insertion_sort_while_first_false():
    array = [5]
    result = insertion_sort(array)
    assert result == [5]

# condition: pos>0: False, array[pos-1]>cursor: False → while loop does not execute
def test_insertion_sort_while_both_false():
    array = []
    result = insertion_sort(array)
    assert result == []