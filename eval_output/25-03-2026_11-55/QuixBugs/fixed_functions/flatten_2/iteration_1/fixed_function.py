def flatten(arr):
    for x in arr:
        if isinstance(x, list):
            yield flatten(x)
        else:
            yield (i for i in (x,))