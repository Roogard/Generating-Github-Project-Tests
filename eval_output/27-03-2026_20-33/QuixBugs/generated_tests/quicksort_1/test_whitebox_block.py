from python_programs.quicksort import quicksort

# covers: block 1 (empty array -> return [])
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# covers: block 2 (non-empty array, single element, lesser and greater both empty)
def test_quicksort_single_element():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

# covers: block 2 (non-empty), recursive lesser and greater branches, return lesser+pivot+greater
def test_quicksort_two_elements_sorted():
    input_list = [1, 2]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# covers: block 2, recursive calls with both lesser and greater non-empty
def test_quicksort_two_elements_reverse():
    input_list = [2, 1]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# covers: block 2, multiple recursive calls, both lesser and greater non-empty
def test_quicksort_multiple_elements():
    input_list = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    # duplicates: note quicksort here drops duplicates (x < pivot, x > pivot only)
    # property: result is sorted
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))

# covers: block 2 with all elements less than pivot (greater is empty)
def test_quicksort_descending():
    input_list = [5, 4, 3, 2, 1]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# covers: block 2 with all elements greater than pivot (lesser is empty)
def test_quicksort_ascending():
    input_list = [1, 2, 3, 4, 5]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# covers: block 2 with negative numbers, both lesser and greater populated
def test_quicksort_negative_numbers():
    input_list = [-3, -1, -4, -1, -5]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))

# covers: block 2 with mixed positive and negative, deeper recursion
def test_quicksort_mixed():
    input_list = [0, -1, 3, -2, 5, 2]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# covers: duplicate elements (duplicates are dropped since neither < nor > pivot)
def test_quicksort_all_same():
    input_list = [7, 7, 7, 7]
    result = quicksort(input_list)
    # Only one element retained per unique value due to strict < and >
    assert result == [7]
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))