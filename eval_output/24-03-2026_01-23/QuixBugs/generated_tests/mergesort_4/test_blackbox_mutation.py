from python_programs.mergesort import mergesort

# catches missing or incorrect base-case for empty list
def test_empty_list():
    assert mergesort([]) == []

# catches missing or incorrect base-case for single-element list
def test_single_element():
    assert mergesort([42]) == [42]

# catches general merge/sort logic failures (e.g., wrong recursion or merge implementation)
def test_reverse_order_sort():
    assert mergesort([4, 3, 2, 1]) == [1, 2, 3, 4]

# catches leftover-append mutation: `result.extend(left[i:] or right[j:])` mutated to only extend left leftovers
def test_merge_with_right_remainder():
    # right side has extra items after left is exhausted
    assert mergesort([1, 2, 3]) == [1, 2, 3]

# catches comparison mutation: `<=` mutated to `<`, which breaks stability on equal keys
def test_stability_for_equal_keys():
    class Item:
        def __init__(self, key, name):
            self.key = key
            self.name = name
        def __lt__(self, other):
            return self.key < other.key
        def __le__(self, other):
            return self.key <= other.key
        def __repr__(self):
            return f"Item({self.key},{self.name})"
    # create items with equal sort key but distinguishable identity
    left  = Item(2, 'L')
    mid   = Item(1, 'M')
    right = Item(2, 'R')
    arr = [left, mid, right]
    sorted_arr = mergesort(arr)
    # correct mergesort must be stable: items with key=2 keep original order L then R
    assert sorted_arr == [mid, left, right]