from python_programs.quicksort import quicksort

# catches: "x < pivot" mutated to "x <= pivot" (drops duplicates into lesser, loses them from output)
def test_duplicates_preserved():
    arr = [3, 3, 3]
    result = quicksort(arr)
    assert result == [3, 3, 3]

# catches: "x > pivot" mutated to "x >= pivot" (duplicates appear twice in greater)
def test_duplicates_not_duplicated():
    arr = [2, 2, 1]
    result = quicksort(arr)
    assert len(result) == 3

# catches: "arr[0]" mutated to "arr[-1]" (wrong pivot selection, still sorts but let's use a specific case)
def test_basic_sort_order():
    arr = [3, 1, 2]
    result = quicksort(arr)
    assert result == [1, 2, 3]

# catches: "not arr" mutated to "arr" (base case inverted, infinite recursion or wrong return)
def test_empty_list():
    assert quicksort([]) == []

# catches: "return []" mutated to "return arr" (wrong base case return value)
def test_single_element():
    assert quicksort([42]) == [42]

# catches: "lesser + [pivot] + greater" mutated to "greater + [pivot] + lesser" (reversed order)
def test_descending_input_sorted_ascending():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == [1, 2, 3, 4, 5]

# catches: "[pivot]" omitted or pivot not included in result
def test_pivot_included_in_result():
    arr = [10, 5, 15]
    result = quicksort(arr)
    assert 10 in result

# catches: "arr[1:]" mutated to "arr" (includes pivot in recursive calls, infinite recursion or wrong output)
def test_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == [1, 2, 3, 4, 5]

# catches: "x < pivot" mutated to "x > pivot" and "x > pivot" mutated to "x < pivot" (swapped conditions)
def test_two_elements_unsorted():
    arr = [2, 1]
    result = quicksort(arr)
    assert result == [1, 2]

# catches: "x < pivot" mutated to "x <= pivot" — element equal to pivot disappears from output
def test_duplicate_with_different_elements():
    arr = [3, 1, 3, 2]
    result = quicksort(arr)
    assert result == [1, 2, 3, 3]

# catches: multiset preservation — no elements dropped or added
def test_multiset_preserved():
    arr = [5, 3, 8, 3, 1, 9, 2]
    result = quicksort(arr)
    assert sorted(result) == sorted(arr)
    assert len(result) == len(arr)

# catches: result is actually sorted (monotonically non-decreasing)
def test_result_is_sorted():
    arr = [9, 7, 5, 3, 1, 2, 4, 6, 8]
    result = quicksort(arr)
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))

# catches: "lesser + [pivot] + greater" mutated to "lesser + greater" (pivot dropped)
def test_pivot_not_dropped():
    arr = [5, 1, 9]
    result = quicksort(arr)
    assert result == [1, 5, 9]

# catches: negative numbers handled correctly (boundary with zero)
def test_negative_numbers():
    arr = [-3, -1, -2, 0]
    result = quicksort(arr)
    assert result == [-3, -2, -1, 0]

# catches: "x < pivot" mutated to "x <= pivot" with single duplicate pair
def test_two_equal_elements():
    arr = [7, 7]
    result = quicksort(arr)
    assert result == [7, 7]