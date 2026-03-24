from correct_python_programs.quicksort import quicksort

# catches: "if not arr:" mutated to "if arr:" (negation error)
def test_empty_array():
    assert quicksort([]) == []

# catches: "if not arr:" mutated to "if len(arr) == 0:" (still correct) or "if arr == []:" (still correct) - but also catches missing return for empty case
def test_single_element():
    assert quicksort([5]) == [5]

# catches: "x < pivot" mutated to "x <= pivot" (off-by-one/operator swap)
def test_all_equal_elements():
    assert quicksort([3, 3, 3]) == [3, 3, 3]

# catches: "x >= pivot" mutated to "x > pivot" (operator swap)
def test_pivot_duplicate_in_greater():
    assert quicksort([2, 4, 2, 1]) == [1, 2, 2, 4]

# catches: "arr[0]" mutated to "arr[-1]" or wrong index (wrong variable)
def test_pivot_is_minimum():
    assert quicksort([1, 5, 3, 9]) == [1, 3, 5, 9]

# catches: "arr[0]" mutated to "arr[1]" (off-by-one index)
def test_pivot_is_maximum():
    assert quicksort([9, 5, 3, 1]) == [1, 3, 5, 9]

# catches: "arr[1:]" mutated to "arr[2:]" or "arr[:]" (slicing error)
def test_two_elements_unsorted():
    assert quicksort([2, 1]) == [1, 2]

# catches: "lesser + [pivot] + greater" mutated to "[pivot] + lesser + greater" (order swap)
def test_three_elements_middle_pivot():
    assert quicksort([2, 1, 3]) == [1, 2, 3]

# catches: "x < pivot" mutated to "x > pivot" (operator reversal)
def test_strictly_decreasing():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# catches: "x >= pivot" mutated to "x <= pivot" (operator reversal)
def test_strictly_increasing():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# catches: missing recursion on lesser/greater (e.g., return [pivot] + arr[1:])
def test_already_sorted_with_duplicates():
    assert quicksort([1, 2, 2, 3, 4]) == [1, 2, 2, 3, 4]

# catches: "lesser = quicksort([...])" mutated to "lesser = [...]" (missing recursion)
def test_complex_unsorted():
    assert quicksort([3, 6, 8, 10, 1, 2, 1]) == [1, 1, 2, 3, 6, 8, 10]