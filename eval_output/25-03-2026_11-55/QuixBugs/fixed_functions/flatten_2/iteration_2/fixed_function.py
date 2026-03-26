def flatten(arr):
    if not isinstance(arr, list):
        raise TypeError(f"flatten() argument must be list, got {type(arr).__name__}")
    for x in arr:
        if isinstance(x, list):
            for y in flatten(x):
                yield y
        else:
            yield x