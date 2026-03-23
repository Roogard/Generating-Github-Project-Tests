def binary_search(array: list, lower_bound: int, upper_bound: int, value: int) -> int:
    """
    This function carries out Binary search on a 1d array and
    return -1 if it do not exist
    array: A 1d sorted array
    value : the value meant to be searched
    >>> matrix = [1, 4, 7, 11, 15]
    >>> binary_search(matrix, 0, len(matrix) - 1, 1)
    0
    >>> binary_search(matrix, 0, len(matrix) - 1, 23)
    -1
    """

    r = int((lower_bound + upper_bound) // 2)
    if array[r] == value:
        return r
    if lower_bound >= upper_bound:
        return -1
    if array[r] < value:
        return binary_search(array, r + 1, upper_bound, value)
    else:
        return binary_search(array, lower_bound, r - 1, value)