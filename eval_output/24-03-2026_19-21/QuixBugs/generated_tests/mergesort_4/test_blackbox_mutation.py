from python_programs.mergesort import mergesort

# catches missing return for empty array (base-case error)
def test_empty_list():
    assert mergesort([]) == []

# catches missing return or wrong base-case for single element
def test_single_element_list():
    assert mergesort([42]) == [42]

# catches wrong comparison logic in merge (e.g., flipped > instead of <=)
def test_two_elements_swapped():
    assert mergesort([2, 1]) == [1, 2]

# catches tail-extension 'or' mutated to 'and' when right side has leftovers
def test_tail_extension_right():
    # left is exhausted first; right tail [2,3] must be appended
    assert mergesort([1, 2, 3]) == [1, 2, 3]

# catches tail-extension 'or' mutated to 'and' when left side has leftovers
def test_tail_extension_left():
    # right is exhausted first; left tail [3] must be appended
    assert mergesort([1, 3, 2]) == [1, 2, 3]

# catches general merge correctness with duplicates
def test_duplicates_ints():
    assert mergesort([3, 1, 2, 1]) == [1, 1, 2, 3]

# catches off-by-one comparison mutation: '<=' mutated to '<' (loss of stability)
class Item:
    def __init__(self, val, idx):
        self.val = val
        self.idx = idx
    def __lt__(self, other):
        return self.val < other.val
    def __le__(self, other):
        return self.val <= other.val
    def __eq__(self, other):
        return isinstance(other, Item) and self.val == other.val and self.idx == other.idx
    def __repr__(self):
        return f"Item({self.val},{self.idx})"

def test_stability_on_equal_items():
    items = [Item(1, 'a'), Item(1, 'b')]
    sorted_items = mergesort(items)
    # original order must be preserved for equal-valued items
    assert sorted_items == items

# catches general correctness on reversed list
def test_reverse_list():
    assert mergesort([4, 3, 2, 1]) == [1, 2, 3, 4]