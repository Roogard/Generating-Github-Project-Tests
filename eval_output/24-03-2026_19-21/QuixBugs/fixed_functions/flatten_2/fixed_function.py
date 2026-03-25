def flatten(arr):
    if not isinstance(arr, list):
        return
    for x in arr:
        if isinstance(x, list):
            for y in flatten(x):
                yield y
        else:
            yield x