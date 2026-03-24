def merge_sort(array: list[int]) -> list[int]:
    """Sort an array in ascending order using merge sort.

    Args:
        array: List of integers to sort.

    Returns:
        A sorted list.

    Examples:
        >>> merge_sort([3, 1, 2])
        [1, 2, 3]
    """
    if len(array) <= 1:
        return array

    mid = len(array) // 2
    left = merge_sort(array[:mid])
    right = merge_sort(array[mid:])

    _merge(left, right, array)
    return array