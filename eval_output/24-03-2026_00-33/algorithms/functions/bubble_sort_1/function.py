def bubble_sort(array: list[int]) -> list[int]:
    """Sort an array in ascending order using bubble sort.

    Args:
        array: List of integers to sort.

    Returns:
        A sorted list.

    Examples:
        >>> bubble_sort([3, 1, 2])
        [1, 2, 3]
    """
    n = len(array)
    swapped = True
    passes = 0
    while swapped:
        swapped = False
        for i in range(1, n - passes):
            if array[i - 1] > array[i]:
                array[i - 1], array[i] = array[i], array[i - 1]
                swapped = True
        passes += 1
    return array