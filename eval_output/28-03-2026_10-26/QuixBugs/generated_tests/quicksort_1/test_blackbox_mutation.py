from python_programs.quicksort import quicksort

# catches: "x < pivot" mutated to "x <= pivot" (drops equal elements into lesser, not preserving duplicates correctly)
def test_duplicates_preserved():
    arr = [3, 3, 3]
    result = quicksort(arr)
    assert result == [3, 3, 3]

# catches: "x > pivot" mutated to "x >= pivot" (drops pivot or duplicates from result)
def test_duplicates_two_elements():
    arr = [2, 2]
    result = quicksort(arr)
    assert result == [2, 2]

# catches: "x < pivot" mutated to "x <= pivot" (pivot would appear twice, losing one instance)
def test_duplicate_with_other_elements():
    arr = [1, 2, 2, 3]
    result = quicksort(arr)
    assert result == [1, 2, 2, 3]

# catches: lesser + [pivot] + greater order mutation (e.g., greater + [pivot] + lesser)
def test_basic_sort_order():
    arr = [3, 1, 2]
    result = quicksort(arr)
    assert result == [1, 2, 3]

# catches: arr[0] mutated to arr[1] as pivot selection (wrong variable/index)
def test_single_element():
    arr = [42]
    result = quicksort(arr)
    assert result == [42]

# catches: "not arr" mutated to "arr" (base case inverted - recurses forever or returns wrong)
def test_empty_list():
    result = quicksort([])
    assert result == []

# catches: arr[1:] mutated to arr[:] (includes pivot in recursive calls, infinite recursion or wrong result)
def test_sorted_result_excludes_no_elements():
    arr = [5, 3, 8, 1, 9, 2]
    result = quicksort(arr)
    assert result == [1, 2, 3, 5, 8, 9]

# catches: "lesser + [pivot] + greater" mutated to "lesser + greater" (drops pivot)
def test_all_elements_preserved():
    arr = [4, 2, 7, 1, 5]
    result = quicksort(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# catches: "x < pivot" mutated to "x > pivot" (lesser and greater swapped, wrong order)
def test_reverse_sorted_input():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == [1, 2, 3, 4, 5]

# catches: off-by-one in arr[1:] mutated to arr[0:] or arr[2:]
def test_two_element_unsorted():
    arr = [2, 1]
    result = quicksort(arr)
    assert result == [1, 2]

# catches: multiset property - no elements dropped or added
def test_multiset_preserved_with_duplicates():
    arr = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
    result = quicksort(arr)
    assert sorted(result) == sorted(arr)
    assert len(result) == len(arr)

# catches: "x < pivot" mutated to "x <= pivot" causing duplicates of pivot to be misplaced
def test_pivot_duplicates_correct_position():
    arr = [3, 1, 3, 2, 3]
    result = quicksort(arr)
    assert result == [1, 2, 3, 3, 3]

# catches: "return []" mutated to "return arr" (base case returns non-empty)
def test_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == [1, 2, 3, 4, 5]

# catches: "lesser + [pivot] + greater" mutated to "[pivot] + lesser + greater"
def test_negative_numbers():
    arr = [-3, -1, -2]
    result = quicksort(arr)
    assert result == [-3, -2, -1]

# catches: property - result must be non-decreasing
def test_sorted_property_holds():
    arr = [10, 3, 7, 1, 8, 5, 2, 9, 4, 6]
    result = quicksort(arr)
    for i in range(len(result) - 1):
        assert result[i] <= result[i + 1]