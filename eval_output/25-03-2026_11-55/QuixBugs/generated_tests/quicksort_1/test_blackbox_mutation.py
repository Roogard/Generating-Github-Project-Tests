from python_programs.quicksort import quicksort

# catches missing base-case or wrong empty check (e.g., if arr: return [] instead of if not arr)
def test_empty_list():
    assert quicksort([]) == []

# catches missing or incorrect handling of single-element lists (e.g., missing return or wrong base-case)
def test_single_element():
    assert quicksort([42]) == [42]

# catches missing pivot insertion or wrong concatenation order (e.g., return lesser + greater or greater + [pivot] + lesser)
def test_two_elements():
    assert quicksort([2, 1]) == [1, 2]

# catches wrong recursion or concatenation that would fail on already sorted input
def test_sorted_list():
    input_list = [1, 2, 3, 4, 5]
    assert quicksort(input_list) == [1, 2, 3, 4, 5]

# catches wrong partition comparison signs (e.g., using <= or >= instead of < and >)
def test_reverse_sorted_list():
    input_list = [5, 4, 3, 2, 1]
    assert quicksort(input_list) == [1, 2, 3, 4, 5]

# catches incorrect partition logic for mixed positive and negative numbers (e.g., swapping < and >)
def test_mixed_numbers():
    arr = [3, -1, 0, 2, -5, 4]
    assert quicksort(arr) == sorted(arr)