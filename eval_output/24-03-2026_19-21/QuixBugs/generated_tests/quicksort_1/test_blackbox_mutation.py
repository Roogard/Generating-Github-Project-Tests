from python_programs.quicksort import quicksort

# catches: missing return or wrong empty check (if arr: vs if not arr:)
def test_quicksort_empty():
    assert quicksort([]) == []

# catches: off-by-one or wrong base-case for single element input
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# catches: wrong slicing arr[1:] mutated to arr[2:] (losing the second element)
def test_quicksort_two_elements():
    assert quicksort([2, 1]) == [1, 2]

# catches: "< pivot" mutated to "<= pivot" or "> pivot" mutated to ">= pivot" (duplicates handling)
def test_quicksort_duplicates():
    # correct implementation drops all but one of the identical elements
    assert quicksort([5, 5, 5]) == [5]

# catches: wrong operator in comparisons or incorrect concatenation order
def test_quicksort_mixed_values():
    input_list = [3, -1, 2, 0, -5, 4]
    expected = [-5, -1, 0, 2, 3, 4]
    assert quicksort(input_list) == expected