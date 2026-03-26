def flatten(arr):
    if not isinstance(arr, list):
        raise TypeError("Input is not a list")
    for x in arr:
        if isinstance(x, list):
            yield from flatten(x)
        elif x is None:
            raise TypeError("None value encountered")
        else:
            yield x