def quicksort(arr):
    try:
        arr = list(arr)
    except TypeError:
        raise TypeError
    if not arr:
        return []
    pivot = arr[0]
    lesser = quicksort([x for x in arr if x < pivot])
    equal = [x for x in arr if x == pivot]
    greater = quicksort([x for x in arr if x > pivot])
    return lesser + equal + greater