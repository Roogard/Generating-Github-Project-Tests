from python_programs.mergesort import mergesort

# catches: "i < len(left)" mutated to "i <= len(left)" (off-by-one in while condition)
def test_merge_exhausts_left():
    result = mergesort([1, 3, 5, 2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]

# catches: "j < len(right)" mutated to "j <= len(right)" (off-by-one in while condition)
def test_merge_exhausts_right():
    result = mergesort([4, 5, 6, 1, 2, 3])
    assert result == [1, 2, 3, 4, 5, 6]

# catches: "<=" mutated to "<" in comparison (would cause duplicates to be mis-ordered)
def test_merge_equal_elements():
    result = mergesort([2, 2, 2])
    assert result == [2, 2, 2]

# catches: "<=" mutated to ">=" (comparison inversion, would sort descending)
def test_merge_two_elements_ascending():
    result = mergesort([2, 1])
    assert result == [1, 2]

# catches: "left[i]" appended instead of "right[j]" in else branch (wrong variable)
def test_merge_picks_right_when_smaller():
    result = mergesort([3, 1])
    assert result == [1, 3]

# catches: "left[i]" mutated to "right[j]" in if branch (wrong variable)
def test_merge_picks_left_when_smaller():
    result = mergesort([1, 3])
    assert result == [1, 3]

# catches: "result.extend(left[i:] or right[j:])" mutated to "and" (missing tail extend)
def test_remaining_left_appended():
    result = mergesort([1, 2, 5, 3, 4])
    assert result == [1, 2, 3, 4, 5]

# catches: "result.extend(left[i:] or right[j:])" where right tail is dropped
def test_remaining_right_appended():
    result = mergesort([3, 4, 1, 2, 5])
    assert result == [1, 2, 3, 4, 5]

# catches: "len(arr) == 0" mutated to "len(arr) == 1" (base case boundary)
def test_single_element():
    result = mergesort([42])
    assert result == [42]

# catches: "len(arr) == 0" mutated to "len(arr) <= 0" or wrong condition
def test_empty_array():
    result = mergesort([])
    assert result == []

# catches: "middle = len(arr) // 2" mutated to "len(arr) // 2 + 1" (off-by-one in split)
def test_split_even_length():
    result = mergesort([4, 3, 2, 1])
    assert result == [1, 2, 3, 4]

# catches: "arr[:middle]" mutated to "arr[middle:]" (swapped left/right slices)
def test_split_odd_length():
    result = mergesort([5, 3, 1, 4, 2])
    assert result == [1, 2, 3, 4, 5]

# catches: "arr[middle:]" mutated to "arr[:middle]" (both halves same slice)
def test_split_produces_correct_halves():
    result = mergesort([3, 1, 2])
    assert result == [1, 2, 3]

# catches: missing "return arr" in base case (returns None instead)
def test_base_case_returns_value():
    result = mergesort([7])
    assert result is not None
    assert result == [7]

# catches: missing "return merge(left, right)" (returns None instead of merged)
def test_return_merge_result():
    result = mergesort([2, 1])
    assert result is not None
    assert result == [1, 2]

# catches: "i += 1" mutated to "i += 0" or "j += 1" mutated to "j += 0" (infinite loop / wrong advance)
def test_all_elements_present_no_duplicates_dropped():
    result = mergesort([5, 1, 4, 2, 3])
    assert result == [1, 2, 3, 4, 5]
    assert len(result) == 5

# catches: "left[i]" mutated to "left[j]" or "right[j]" mutated to "right[i]" (index variable swap)
def test_index_variable_not_swapped():
    result = mergesort([10, 1, 9, 2, 8, 3])
    assert result == [1, 2, 3, 8, 9, 10]

# catches: negatives handled correctly (boundary/sign mutation)
def test_negative_numbers():
    result = mergesort([-3, -1, -4, -1, -5])
    assert result == [-5, -4, -3, -1, -1]

# catches: mixed positive/negative
def test_mixed_positive_negative():
    result = mergesort([-2, 3, -1, 0, 2])
    assert result == [-2, -1, 0, 2, 3]

# catches: "middle = len(arr) // 2" mutated to "middle = len(arr) // 2 - 1"
def test_two_elements_equal():
    result = mergesort([1, 1])
    assert result == [1, 1]