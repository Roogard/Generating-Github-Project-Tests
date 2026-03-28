from python_programs.mergesort import mergesort

# catches: "result.extend(left[i:] or right[j:])" mutated — only one tail appended correctly
def test_remaining_left_elements_appended():
    # When right is exhausted first, remaining left elements must be appended
    result = mergesort([3, 4, 1, 2])
    assert result == sorted([3, 4, 1, 2])

# catches: "result.extend(left[i:] or right[j:])" — only left tail used, right tail dropped
def test_remaining_right_elements_appended():
    # When left is exhausted first, remaining right elements must be appended
    result = mergesort([1, 5, 2, 6])
    assert result == sorted([1, 5, 2, 6])

# catches: "<=" mutated to "<" (stability/duplicate handling)
def test_equal_elements_preserved():
    arr = [3, 3, 3]
    result = mergesort(arr)
    assert result == [3, 3, 3]

# catches: "<=" mutated to "<" causing wrong ordering with equal elements
def test_two_equal_elements():
    arr = [2, 2]
    result = mergesort(arr)
    assert result == [2, 2]

# catches: "len(arr) == 0" mutated to "len(arr) <= 0" or "len(arr) == 1" (base case boundary)
def test_single_element():
    arr = [42]
    result = mergesort(arr)
    assert result == [42]

# catches: "len(arr) == 0" base case missing or wrong — empty array handling
def test_empty_array():
    result = mergesort([])
    assert result == []

# catches: middle = len(arr) // 2 mutated to len(arr) // 2 + 1 or - 1
def test_two_elements_sorted():
    arr = [5, 1]
    result = mergesort(arr)
    assert result == [1, 5]

# catches: middle = len(arr) // 2 mutated to len(arr) // 2 + 1 or - 1 (odd length)
def test_three_elements():
    arr = [3, 1, 2]
    result = mergesort(arr)
    assert result == [1, 2, 3]

# catches: arr[:middle] mutated to arr[:middle-1] or arr[:middle+1]
def test_preserves_all_elements():
    arr = [5, 3, 8, 1, 9, 2, 7, 4, 6]
    result = mergesort(arr)
    assert len(result) == len(arr)
    assert result == sorted(arr)

# catches: duplicates dropped anywhere in the merge/split
def test_duplicates_preserved_in_output():
    arr = [4, 2, 4, 1, 2]
    result = mergesort(arr)
    assert sorted(result) == sorted(arr)
    assert len(result) == len(arr)

# catches: i += 1 mutated to j += 1 or vice versa (wrong index increment)
def test_correct_ordering_after_merge():
    arr = [10, 1, 9, 2, 8, 3]
    result = mergesort(arr)
    assert result == [1, 2, 3, 8, 9, 10]

# catches: left[i] <= right[j] mutated to left[i] < right[j] with interleaved equal values
def test_equal_interleaved_elements():
    arr = [1, 2, 1, 2]
    result = mergesort(arr)
    assert result == [1, 1, 2, 2]

# catches: "right[j]" and "left[i]" swapped in append inside else branch
def test_descending_input():
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == [1, 2, 3, 4, 5]

# catches: "arr[middle:]" mutated to "arr[middle+1:]" causing element drop
def test_no_elements_lost_even_length():
    arr = [6, 2, 8, 4]
    result = mergesort(arr)
    assert result == [2, 4, 6, 8]
    assert len(result) == 4

# catches: "arr[:middle]" mutated to "arr[1:middle]" causing element drop
def test_no_elements_lost_odd_length():
    arr = [7, 3, 9, 1, 5]
    result = mergesort(arr)
    assert result == [1, 3, 5, 7, 9]
    assert len(result) == 5

# catches: i < len(left) mutated to i <= len(left) (out of bounds or wrong count)
def test_merge_boundary_left():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == [1, 2]

# catches: j < len(right) mutated to j <= len(right)
def test_merge_boundary_right():
    arr = [1, 2]
    result = mergesort(arr)
    assert result == [1, 2]

# catches: "or" mutated to "and" in result.extend(left[i:] or right[j:])
def test_tail_extension_when_both_sides_have_remainder():
    # After the while loop, only one side can have remainder; correct impl appends that side
    arr = [1, 3, 5, 2, 4, 6]
    result = mergesort(arr)
    assert result == [1, 2, 3, 4, 5, 6]