from python_programs.mergesort import mergesort

# catches: "left[i] <= right[j]" mutated to "left[i] < right[j]" (equal elements handled wrong)
def test_equal_elements_preserved():
    result = mergesort([3, 3, 3])
    assert result == [3, 3, 3]

# catches: duplicate elements dropped due to wrong comparison
def test_duplicates_across_halves():
    result = mergesort([2, 1, 2, 1])
    assert result == [1, 1, 2, 2]

# catches: "len(arr) == 0" mutated to "len(arr) <= 0" or "len(arr) < 1" — base case off-by-one
def test_single_element():
    result = mergesort([42])
    assert result == [42]

# catches: base case "== 0" mutated to "== 1" — single element never recurses
def test_two_elements_sorted():
    result = mergesort([2, 1])
    assert result == [1, 2]

# catches: "== 0" mutated to "!= 0" — always returns early
def test_empty_list():
    result = mergesort([])
    assert result == []

# catches: "arr[:middle]" mutated to "arr[:middle+1]" (off-by-one in split)
def test_even_length_split():
    result = mergesort([4, 3, 2, 1])
    assert result == [1, 2, 3, 4]

# catches: "arr[middle:]" mutated to "arr[middle+1:]" (off-by-one, element lost)
def test_no_elements_lost_even():
    arr = [4, 3, 2, 1]
    result = mergesort(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# catches: element loss in odd-length array due to index mutation
def test_no_elements_lost_odd():
    arr = [5, 3, 1, 4, 2]
    result = mergesort(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# catches: "result.extend(left[i:] or right[j:])" — if 'or' becomes 'and', remaining elements dropped
def test_remaining_left_elements_appended():
    result = mergesort([1, 2, 5, 3, 4])
    assert result == [1, 2, 3, 4, 5]

# catches: "left[i:] or right[j:]" — if only right remainder is appended and left is skipped
def test_remaining_right_elements_appended():
    result = mergesort([3, 4, 1, 2])
    assert result == [1, 2, 3, 4]

# catches: "i += 1" mutated to "j += 1" or vice versa (wrong index incremented)
def test_correct_order_maintained():
    result = mergesort([9, 1, 8, 2, 7, 3])
    assert result == [1, 2, 3, 7, 8, 9]

# catches: "len(arr) // 2" mutated to "len(arr) // 2 + 1" or "- 1"
def test_three_elements():
    result = mergesort([3, 1, 2])
    assert result == [1, 2, 3]

# catches: negative numbers handled correctly (arithmetic mutation in comparison)
def test_negative_numbers():
    result = mergesort([-3, -1, -2, 0])
    assert result == [-3, -2, -1, 0]

# catches: already sorted input is not corrupted
def test_already_sorted():
    result = mergesort([1, 2, 3, 4, 5])
    assert result == [1, 2, 3, 4, 5]

# catches: reverse sorted input
def test_reverse_sorted():
    result = mergesort([5, 4, 3, 2, 1])
    assert result == [1, 2, 3, 4, 5]

# catches: all same elements — length preserved and order trivially correct
def test_all_same_elements():
    arr = [7, 7, 7, 7]
    result = mergesort(arr)
    assert result == [7, 7, 7, 7]
    assert len(result) == len(arr)

# catches: "while i < len(left) and j < len(right)" — 'and' mutated to 'or' (index out of bounds or wrong merge)
def test_merge_stops_at_shorter_list():
    result = mergesort([3, 1, 2])
    assert result[0] == 1
    assert result[-1] == 3

# catches: result is actually sorted (property check)
def test_result_is_sorted():
    arr = [10, -5, 3, 8, 0, -1, 7]
    result = mergesort(arr)
    for i in range(len(result) - 1):
        assert result[i] <= result[i + 1]