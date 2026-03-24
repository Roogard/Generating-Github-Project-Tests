from algorithms.sorting.insertion_sort import insertion_sort

# catches: "range(len(array))" mutated to "range(len(array)-1)" (off-by-one, misses last element)
def test_insertion_sort_single_element():
    assert insertion_sort([5]) == [5]

# catches: "pos > 0" mutated to "pos >= 0" (infinite loop or index -1)
def test_insertion_sort_two_elements_already_sorted():
    assert insertion_sort([1, 2]) == [1, 2]

# catches: "pos > 0" mutated to "pos > 1" (off-by-one, stops too early)
def test_insertion_sort_two_elements_reversed():
    assert insertion_sort([2, 1]) == [1, 2]

# catches: "array[pos - 1] > cursor" mutated to "array[pos - 1] >= cursor" (stable property lost)
def test_insertion_sort_duplicate_elements():
    assert insertion_sort([3, 1, 3, 2]) == [1, 2, 3, 3]

# catches: "array[pos] = array[pos - 1]" mutated to "array[pos] = cursor" (swap logic broken)
def test_insertion_sort_multiple_shifts_needed():
    assert insertion_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# catches: "pos -= 1" mutated to "pos += 1" (infinite loop)
def test_insertion_sort_already_sorted_large():
    assert insertion_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# catches: "array[pos] = cursor" placed outside while loop (missing final assignment)
def test_insertion_sort_cursor_at_correct_position_initially():
    assert insertion_sort([0, 10, 20]) == [0, 10, 20]

# catches: "while pos > 0 and array[pos - 1] > cursor:" mutated to "while pos >= 0 and array[pos - 1] > cursor:" (index error)
def test_insertion_sort_first_element_largest():
    assert insertion_sort([10, 1, 2, 3]) == [1, 2, 3, 10]

# catches: "array[pos] = array[pos - 1]" mutated to "array[pos] = array[pos]" (no shift)
def test_insertion_sort_element_needs_one_shift():
    assert insertion_sort([1, 3, 2]) == [1, 2, 3]

# catches: "cursor = array[i]" mutated to "cursor = array[0]" (wrong variable)
def test_insertion_sort_all_elements_same():
    assert insertion_sort([7, 7, 7]) == [7, 7, 7]