from python_programs.mergesort import mergesort

# catches: "i < len(left)" mutated to "i <= len(left)" (off-by-one in while condition)
def test_merge_all_left_elements_consumed():
    result = mergesort([3, 1])
    assert result == [1, 3]

# catches: "j < len(right)" mutated to "j <= len(right)" (off-by-one in while condition)
def test_merge_all_right_elements_consumed():
    result = mergesort([1, 3])
    assert result == [1, 3]

# catches: "<=" mutated to "<" (strict vs non-strict comparison, equal elements)
def test_merge_equal_elements():
    result = mergesort([2, 2])
    assert result == [2, 2]

# catches: "left[i] <= right[j]" mutated to "left[i] >= right[j]" (reversed comparison)
def test_merge_two_elements_wrong_order():
    result = mergesort([5, 1])
    assert result == [1, 5]

# catches: "result.append(left[i])" and "result.append(right[j])" swapped (wrong variable)
def test_merge_distinct_values_correct_order():
    result = mergesort([4, 2, 7, 1])
    assert result == [1, 2, 4, 7]

# catches: "left[i:] or right[j:]" mutated to "left[i:] and right[j:]" (wrong operator)
def test_extend_remaining_left():
    result = mergesort([1, 2, 5, 3, 4])
    assert result == [1, 2, 3, 4, 5]

# catches: "left[i:] or right[j:]" — only right remainder appended
def test_extend_remaining_right():
    result = mergesort([3, 4, 1, 2])
    assert result == [1, 2, 3, 4]

# catches: "len(arr) == 0" mutated to "len(arr) == 1" (constant error in base case)
def test_single_element_returns_itself():
    result = mergesort([42])
    assert result == [42]

# catches: "len(arr) == 0" mutated to "len(arr) <= 0" or missing base case entirely
def test_empty_array():
    result = mergesort([])
    assert result == []

# catches: "middle = len(arr) // 2" mutated to "middle = len(arr) // 2 + 1" (off-by-one in split)
def test_odd_length_array():
    result = mergesort([3, 1, 2])
    assert result == [1, 2, 3]

# catches: "arr[:middle]" mutated to "arr[middle:]" and vice versa (swapped slices)
def test_split_correctness_five_elements():
    result = mergesort([5, 4, 3, 2, 1])
    assert result == [1, 2, 3, 4, 5]

# catches: "i += 1" mutated to "j += 1" or vice versa (wrong index incremented)
def test_interleaved_merge():
    result = mergesort([2, 4, 1, 3])
    assert result == [1, 2, 3, 4]

# catches: missing "return arr" in base case (function returns None)
def test_base_case_returns_list_not_none():
    result = mergesort([7])
    assert result is not None
    assert result == [7]

# catches: missing "return merge(left, right)" (function falls through returning None)
def test_return_value_is_not_none():
    result = mergesort([3, 1, 2])
    assert result is not None

# catches: "result.extend" mutated to not extending (truncated output)
def test_full_output_length_preserved():
    arr = [6, 3, 8, 1, 9, 2, 7, 4, 5]
    result = mergesort(arr)
    assert len(result) == len(arr)
    assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9]

# catches: stable sort property (left[i] <= right[j] preserving left-first for equals)
def test_stable_sort_equal_elements_multiple():
    result = mergesort([3, 1, 3, 2, 3])
    assert result == [1, 2, 3, 3, 3]

# catches: "arr[middle:]" mutated to "arr[middle+1:]" (off-by-one dropping element)
def test_no_elements_lost():
    arr = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == list(range(1, 11))