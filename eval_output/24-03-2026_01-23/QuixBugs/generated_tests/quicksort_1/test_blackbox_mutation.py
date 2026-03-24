from python_programs.quicksort import quicksort

# catches missing return or incorrect base-case handling for empty list
def test_empty_list():
    assert quicksort([]) == []

# catches incorrect base-case or fall-through for single-element list
def test_single_element():
    assert quicksort([42]) == [42]

# catches wrong concatenation order (e.g., lesser + greater + [pivot])
def test_basic_sort():
    assert quicksort([3, 1, 4, 2]) == [1, 2, 3, 4]

# catches off-by-one wrong comparison: '<' mutated to '<=' would include duplicate pivot in lesser
def test_duplicate_element_less_equal_mutation():
    input_list = [2, 1, 3, 2]
    # correct quicksort drops extra '2' and returns [1,2,3]
    assert quicksort(input_list) == [1, 2, 3]

# catches off-by-one wrong comparison: '>' mutated to '>=' would include duplicate pivot in greater
def test_duplicate_element_greater_equal_mutation():
    input_list = [1, 2, 1, 3]
    # correct quicksort drops extra '1' and returns [1,2,3]
    assert quicksort(input_list) == [1, 2, 3]

# catches failure on already sorted input (e.g., wrong pivot logic)
def test_sorted_input():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# catches issues on reverse-sorted input
def test_reverse_sorted_input():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]