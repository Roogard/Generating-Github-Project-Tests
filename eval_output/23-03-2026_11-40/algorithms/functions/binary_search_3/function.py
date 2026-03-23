def binary_search(array: list[int], query: int) -> int:
    """Search for *query* in a sorted *array* using iterative binary search.

    Args:
        array: Sorted list of integers in ascending order.
        query: Value to search for.

    Returns:
        Index of *query* in *array*, or -1 if not found.

    Examples:
        >>> binary_search([1, 2, 3, 4, 5], 3)
        2
        >>> binary_search([1, 2, 3, 4, 5], 6)
        -1
    """
    low, high = 0, len(array) - 1
    while low <= high:
        mid = low + (high - low) // 2
        val = array[mid]
        if val == query:
            return mid
        if val < query:
            low = mid + 1
        else:
            high = mid - 1
    return -1