from algorithms.sorting.bubble_sort import bubble_sort

# Block mapping:
# block 1: n = len(array); swapped = True; passes = 0; while swapped:
# block 2: swapped = False; for i in range(1, n - passes):
# block 3: if array[i - 1] > array[i]:
# block 4: array[i - 1], array[i] = array[i], array[i - 1]; swapped = True
# block 5: passes += 1 (end of while loop)
# block 6: return array

# covers: block 1, block 2, block 5, block 6 (no swaps, while loop runs once)
def test_already_sorted():
    assert bubble_sort([1, 2, 3]) == [1, 2, 3]

# covers: block 1, block 2, block 3, block 4, block 5, block 6 (multiple passes with swaps)
def test_reverse_sorted():
    assert bubble_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: block 1, block 2, block 3, block 4, block 5, block 6 (partial swaps)
def test_unsorted():
    assert bubble_sort([3, 1, 4, 1, 5, 9, 2]) == [1, 1, 2, 3, 4, 5, 9]

# covers: block 1, block 2, block 5, block 6 (single element, no swaps)
def test_single_element():
    assert bubble_sort([42]) == [42]

# covers: block 1, block 2, block 5, block 6 (empty list, no swaps)
def test_empty_list():
    assert bubble_sort([]) == []