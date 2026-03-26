def flatten(arr):
    for x in arr:
        if isinstance(x, list):
            yield from flatten(x)
        else:
            yield flatten(x)