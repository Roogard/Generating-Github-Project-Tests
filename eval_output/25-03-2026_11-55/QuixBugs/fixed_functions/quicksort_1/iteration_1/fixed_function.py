def quicksort(arr):
    if not arr:
        return []
    pivot = arr[0]
    lesser = [x for x in arr if x < pivot]
    greater = [x for x in arr if x > pivot]
    return quicksort(lesser) + [pivot] + quicksort(greater)