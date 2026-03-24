def insertion_sort(array: list[int]) -> list[int]:
    """Sort an array in ascending order using insertion sort.

    Args:
        array: List of integers to sort.

    Returns:
        A sorted list.

    Examples:
        >>> insertion_sort([3, 1, 2])
        [1, 2, 3]
    """
    for i in range(len(array)):
        cursor = array[i]
        pos = i

        while pos > 0 and array[pos - 1] > cursor:
            array[pos] = array[pos - 1]
            pos -= 1
        array[pos] = cursor

    return array