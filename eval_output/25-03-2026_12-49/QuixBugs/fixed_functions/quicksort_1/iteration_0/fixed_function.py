def quicksort(arr):
    if not isinstance(arr, list):
        raise TypeError
    if len(arr) <= 1:
        return arr[:]
    pivot = arr[0]
    lesser = []
    equal = []
    greater = []
    for x in arr:
        if x < pivot:
            lesser.append(x)
        elif x > pivot:
            greater.append(x)
        else:
            equal.append(x)
    return quicksort(lesser) + equal + quicksort(greater)