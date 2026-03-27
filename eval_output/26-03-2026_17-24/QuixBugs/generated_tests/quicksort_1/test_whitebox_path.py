from python_programs.quicksort import quicksort

# path: empty check → True → return []
def test_quicksort_empty():
    assert quicksort([]) == []

# path: empty check → False → single element → lesser=[], greater=[] → return [pivot]
def test_quicksort_single():
    assert quicksort([1]) == [1]

# path: empty check → False → two elements → pivot larger → lesser has element, greater empty
def test_quicksort_two_ascending():
    assert quicksort([1, 2]) == [1, 2]

# path: empty check → False → two elements → pivot smaller → lesser empty, greater has element
def test_quicksort_two_descending():
    assert quicksort([2, 1]) == [1, 2]

# path: empty check → False → multiple elements → all lesser (pivot is max)
def test_quicksort_pivot_is_max():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# path: empty check → False → multiple elements → all greater (pivot is min)
def test_quicksort_pivot_is_min():
    assert quicksort([1, 3, 2]) == [1, 2, 3]

# path: empty check → False → multiple elements → elements on both sides of pivot
def test_quicksort_mixed():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# path: empty check → False → duplicate elements equal to pivot → lesser=[], greater=[] (duplicates excluded)
def test_quicksort_all_duplicates():
    assert quicksort([5, 5, 5]) == [5, 5, 5]

# path: empty check → False → already sorted input → recursive calls with progressively smaller arrays
def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: empty check → False → reverse sorted input → recursive calls with progressively smaller arrays
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# path: empty check → False → negative numbers mixed with positives
def test_quicksort_negative_numbers():
    assert quicksort([-3, 1, -1, 2, 0]) == [-3, -1, 0, 1, 2]

# path: empty check → False → single element repeated with unique pivot
def test_quicksort_duplicates_with_unique():
    assert quicksort([2, 2, 1, 2, 3]) == [1, 2, 2, 2, 3]