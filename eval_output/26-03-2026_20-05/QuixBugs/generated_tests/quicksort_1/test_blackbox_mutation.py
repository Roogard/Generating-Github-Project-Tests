from python_programs.quicksort import quicksort

# catches: "not arr" mutated to "arr" (negation error) - base case inverted
def test_empty_list_returns_empty():
    assert quicksort([]) == []

# catches: "arr[0]" mutated to "arr[1]" (wrong index for pivot)
def test_single_element():
    assert quicksort([42]) == [42]

# catches: "x < pivot" mutated to "x <= pivot" (duplicates lost or wrong partition)
def test_duplicate_elements_preserved():
    result = quicksort([3, 1, 3, 2, 3])
    assert result == [1, 2, 3, 3, 3]

# catches: "x < pivot" mutated to "x > pivot" (lesser/greater swapped in filter)
def test_two_element_unsorted():
    assert quicksort([2, 1]) == [1, 2]

# catches: "x > pivot" mutated to "x < pivot" (greater filter wrong)
def test_two_element_sorted():
    assert quicksort([1, 2]) == [1, 2]

# catches: "lesser + [pivot] + greater" mutated to "greater + [pivot] + lesser" (wrong order)
def test_order_is_ascending():
    result = quicksort([3, 1, 4, 1, 5, 9, 2, 6])
    assert result == [1, 1, 2, 3, 4, 5, 6, 9]

# catches: "[pivot]" omitted or pivot dropped from result
def test_pivot_included_in_result():
    result = quicksort([5, 3, 7])
    assert result == [3, 5, 7]
    assert 5 in result

# catches: "arr[1:]" mutated to "arr[0:]" or "arr[2:]" (wrong slice for partition)
def test_partition_excludes_pivot():
    result = quicksort([2, 1, 3])
    assert result == [1, 2, 3]

# catches: "lesser + [pivot] + greater" mutated to "lesser + greater" (pivot missing)
def test_length_preserved():
    arr = [5, 3, 8, 1, 9, 2]
    result = quicksort(arr)
    assert len(result) == len(arr)

# catches: "x < pivot" mutated to "x <= pivot" (duplicate pivot values lost)
def test_all_same_elements():
    result = quicksort([7, 7, 7, 7])
    assert result == [7, 7, 7, 7]

# catches: missing return (function returns None instead of list)
def test_returns_list_type():
    result = quicksort([3, 1, 2])
    assert isinstance(result, list)

# catches: off-by-one returning empty base case too early
def test_two_identical_elements():
    assert quicksort([4, 4]) == [4, 4]

# catches: "greater" and "lesser" variable swap in return statement
def test_descending_input_sorted_ascending():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# catches: "x > pivot" mutated to "x >= pivot" (pivot duplicated in greater)
def test_no_duplicate_pivot_in_output():
    result = quicksort([3, 3, 1, 2])
    assert result.count(3) == 2

# catches: negative numbers handled correctly (boundary with zero)
def test_negative_numbers():
    assert quicksort([-3, -1, -2, 0]) == [-3, -2, -1, 0]

# catches: mixed positive and negative values with zero pivot
def test_mixed_sign_numbers():
    assert quicksort([0, -1, 1, -2, 2]) == [-2, -1, 0, 1, 2]