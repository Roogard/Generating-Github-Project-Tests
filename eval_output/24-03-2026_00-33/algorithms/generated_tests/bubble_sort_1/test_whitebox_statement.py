from algorithms.sorting.bubble_sort import bubble_sort

# covers: n = len(array), swapped = True, passes = 0, while swapped (True), swapped = False, for i in range(1, n - passes) (loop body executes), if array[i - 1] > array[i] (True), swap, swapped = True, passes += 1, while swapped (True again), swapped = False, for i in range(1, n - passes) (loop body may not execute), passes += 1, while swapped (False), return array
def test_bubble_sort_multiple_passes():
    assert bubble_sort([3, 1, 2]) == [1, 2, 3]

# covers: n = len(array), swapped = True, passes = 0, while swapped (True), swapped = False, for i in range(1, n - passes) (loop body executes), if array[i - 1] > array[i] (False), passes += 1, while swapped (False), return array
def test_bubble_sort_already_sorted():
    assert bubble_sort([1, 2, 3]) == [1, 2, 3]

# covers: n = len(array) (len 1), swapped = True, passes = 0, while swapped (True), swapped = False, for i in range(1, n - passes) (range(1, 1) empty, loop body never executes), passes += 1, while swapped (False), return array
def test_bubble_sort_single_element():
    assert bubble_sort([5]) == [5]

# covers: n = len(array) (len 0), swapped = True, passes = 0, while swapped (True), swapped = False, for i in range(1, n - passes) (range(1, 0) empty, loop body never executes), passes += 1, while swapped (False), return array
def test_bubble_sort_empty():
    assert bubble_sort([]) == []