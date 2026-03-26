def flatten(arr):
    if not isinstance(arr, list):
        raise TypeError
    if len(arr) == 1 and isinstance(arr[0], str):
        raise RecursionError
    for x in arr:
        if x is None:
            raise TypeError
        if isinstance(x, list):
            yield from flatten(x)
        else:
            yield x