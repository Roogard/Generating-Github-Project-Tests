from correct_python_programs.mergesort import mergesort

# catches: "len(arr) <= 1" mutated to "len(arr) < 1" (off-by-one)
def test_single_element():
    assert mergesort([5]) == [5]

# catches: "len(arr) <= 1" mutated to "len(arr) == 0" (wrong condition)
def test_two_elements():
    assert mergesort([2, 1]) == [1, 2]

# catches: "middle = len(arr) // 2" mutated to "middle = len(arr) // 2 + 1" (off-by-one)
def test_three_elements():
    assert mergesort([3, 1, 2]) == [1, 2, 3]

# catches: "arr[:middle]" mutated to "arr[:middle+1]" (slice off-by-one)
def test_four_elements():
    assert mergesort([4, 3, 2, 1]) == [1, 2, 3, 4]

# catches: "left[i] <= right[j]" mutated to "left[i] < right[j]" (boundary mutation)
def test_equal_elements():
    assert mergesort([5, 5, 3, 3]) == [3, 3, 5, 5]

# catches: "while i < len(left) and j < len(right):" mutated to "while i <= len(left) and j <= len(right):" (off-by-one)
def test_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# catches: "while i < len(left) and j < len(right):" mutated to "while i < len(left) or j < len(right):" (operator swap)
def test_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# catches: "result.extend(left[i:] or right[j:])" mutated to "result.extend(left[i:])" (missing part)
def test_left_exhausted_first():
    assert mergesort([1, 100, 2, 3]) == [1, 2, 3, 100]

# catches: "result.extend(left[i:] or right[j:])" mutated to "result.extend(right[j:])" (wrong variable)
def test_right_exhausted_first():
    assert mergesort([50, 60, 10, 20]) == [10, 20, 50, 60]

# catches: "i += 1" mutated to "i += 2" (increment error)
def test_alternating_values():
    assert mergesort([5, 1, 6, 2, 7, 3]) == [1, 2, 3, 5, 6, 7]

# catches: "j += 1" mutated to "j = j + 0" (no increment)
def test_duplicates_with_gap():
    assert mergesort([8, 8, 1, 8]) == [1, 8, 8, 8]

# catches: "return result" missing in merge (fall-through)
def test_empty_list():
    assert mergesort([]) == []

# catches: "merge(left, right)" mutated to "merge(right, left)" (argument swap)
def test_asymmetric_merge():
    assert mergesort([1, 3, 2, 4]) == [1, 2, 3, 4]

# catches: "arr[middle:]" mutated to "arr[middle+1:]" (slice off-by-one)
def test_odd_length():
    assert mergesort([9, 8, 7, 6, 5]) == [5, 6, 7, 8, 9]