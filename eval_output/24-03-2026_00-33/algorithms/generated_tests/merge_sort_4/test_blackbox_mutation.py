from algorithms.sorting.merge_sort import merge_sort

# catches: "<= 1" mutated to "< 1" (off-by-one on base case)
def test_merge_sort_single_element():
    assert merge_sort([5]) == [5]

# catches: "<= 1" mutated to "<= 0" (wrong constant)
def test_merge_sort_two_elements():
    assert merge_sort([2, 1]) == [1, 2]

# catches: "mid = len(array) // 2" mutated to "mid = len(array) // 2 + 1" (off-by-one split)
def test_merge_sort_odd_length():
    assert merge_sort([3, 1, 2]) == [1, 2, 3]

# catches: "array[:mid]" mutated to "array[:mid+1]" or "array[mid:]" mutated to "array[mid+1:]" (slice error)
def test_merge_sort_even_length():
    assert merge_sort([4, 3, 2, 1]) == [1, 2, 3, 4]

# catches: missing return in base case or wrong variable returned
def test_merge_sort_empty_list():
    assert merge_sort([]) == []

# catches: "_merge(left, right, array)" mutated to "_merge(right, left, array)" (argument swap)
def test_merge_sort_already_sorted():
    assert merge_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# catches: "_merge" not merging correctly (e.g., comparison flipped, index off-by-one)
def test_merge_sort_reverse_sorted():
    assert merge_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# catches: off-by-one in merge loop or wrong comparison operator (e.g., < instead of <=)
def test_merge_sort_with_duplicates():
    assert merge_sort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]

# catches: mutation in recursion depth (e.g., infinite recursion due to wrong split)
def test_merge_sort_large_random():
    import random
    arr = [random.randint(-100, 100) for _ in range(100)]
    assert merge_sort(arr.copy()) == sorted(arr)