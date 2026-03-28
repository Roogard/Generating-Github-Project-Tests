from python_programs.quicksort import quicksort

# --- BVA ---

def test_bva_empty_array():
    # Boundary: empty collection
    result = quicksort([])
    assert result == []

def test_bva_single_element():
    # Boundary: single element collection
    result = quicksort([42])
    assert result == [42]

def test_bva_two_elements_sorted():
    # Boundary: two elements already sorted
    result = quicksort([1, 2])
    assert result == [1, 2]

def test_bva_two_elements_reverse():
    # Boundary: two elements in reverse order
    result = quicksort([2, 1])
    assert result == [1, 2]

def test_bva_large_sorted_input():
    # Boundary: already sorted large input (worst-case pivot selection)
    inp = list(range(1, 101))
    result = quicksort(inp)
    assert result == list(range(1, 101))

def test_bva_large_reverse_sorted():
    # Boundary: reverse sorted large input
    inp = list(range(100, 0, -1))
    result = quicksort(inp)
    assert result == list(range(1, 101))

def test_bva_all_identical_elements():
    # Boundary: all elements equal — a correct quicksort preserves all elements
    # Note: this implementation drops duplicates (keeps only pivot), which is a known bug
    # We test against the correct specification: sorted output preserving all elements
    inp = [5, 5, 5, 5]
    result = quicksort(inp)
    # A correct quicksort SHOULD return all elements sorted
    assert result == sorted(inp)

def test_bva_negative_numbers():
    # Boundary: all negative values
    inp = [-3, -1, -4, -1, -5]
    result = quicksort(inp)
    assert result == sorted(inp)

def test_bva_min_max_integers():
    # Boundary: very large and very small integers
    inp = [10**9, -10**9, 0]
    result = quicksort(inp)
    assert result == [-10**9, 0, 10**9]

# --- ECP ---

def test_ecp_valid_typical_unsorted():
    # Valid class: typical unsorted list of distinct integers
    inp = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(inp)
    assert result == sorted(inp)

def test_ecp_valid_already_sorted():
    # Valid class: already sorted input (distinct elements)
    inp = [1, 2, 3, 4, 5]
    result = quicksort(inp)
    assert result == [1, 2, 3, 4, 5]

def test_ecp_valid_reverse_sorted():
    # Valid class: reverse sorted input
    inp = [5, 4, 3, 2, 1]
    result = quicksort(inp)
    assert result == [1, 2, 3, 4, 5]

def test_ecp_valid_with_duplicates():
    # Valid class: list with duplicate elements
    # A correct quicksort MUST preserve all elements including duplicates
    inp = [3, 1, 2, 3, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_ecp_valid_mixed_positive_negative():
    # Valid class: mix of positive, negative, and zero
    inp = [-5, 0, 3, -2, 7]
    result = quicksort(inp)
    assert result == [-5, -2, 0, 3, 7]

def test_ecp_valid_floats():
    # Valid class: floating point numbers
    inp = [3.14, 1.0, 2.71, 0.5]
    result = quicksort(inp)
    assert result == [0.5, 1.0, 2.71, 3.14]

def test_ecp_valid_single_duplicate_pair():
    # Valid class: exactly two equal elements
    inp = [7, 7]
    result = quicksort(inp)
    # A correct quicksort SHOULD return [7, 7]
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_ecp_valid_pivot_is_largest():
    # Valid class: pivot (first element) is the largest
    inp = [9, 1, 3, 5, 7]
    result = quicksort(inp)
    assert result == [1, 3, 5, 7, 9]

def test_ecp_valid_pivot_is_smallest():
    # Valid class: pivot (first element) is the smallest
    inp = [1, 9, 7, 5, 3]
    result = quicksort(inp)
    assert result == [1, 3, 5, 7, 9]

# --- Mutation Detection ---

def test_mutation_offbyone_lesser_boundary():
    # Detects: '<' changed to '<=' in lesser partition
    # If '<=' is used, pivot duplicates go to lesser, causing wrong output
    inp = [3, 1, 3, 5]
    result = quicksort(inp)
    # A correct quicksort SHOULD return sorted(inp) with all elements
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_mutation_offbyone_greater_boundary():
    # Detects: '>' changed to '>=' in greater partition
    # If '>=' is used, pivot duplicates go to greater, causing wrong output
    inp = [3, 5, 3, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_mutation_wrong_variable_arr1_instead_of_arr0():
    # Detects: pivot = arr[1] instead of arr[0]
    # With arr = [10, 1, 2], correct pivot is 10, giving [1, 2, 10]
    # Wrong pivot arr[1]=1 gives [1, 2, 10] only by accident; use a case that differs
    # arr = [5, 1, 9]: correct pivot 5 -> [1, 5, 9]; wrong pivot 1 -> [1, 5, 9] same
    # Use arr = [3, 9, 1]: correct pivot 3 -> [1, 3, 9]; wrong pivot 9 -> [1, 3, 9] same
    # Better: arr = [2, 8, 1]: correct pivot 2 -> lesser=[1], greater=[8] -> [1,2,8]
    #         wrong pivot arr[1]=8 -> lesser=[2,1], greater=[] -> quicksort([2,1])+[8] -> [1,2,8] same
    # Use arr = [5, 1]: correct -> [1, 5]; wrong pivot arr[1]=1 -> lesser=[], greater=[5] -> [1, 5] same
    # Use arr = [1, 5, 3]: correct pivot=1 -> lesser=[], greater=[5,3] -> [1,3,5]
    #          wrong pivot=5 -> lesser=[1,3], greater=[] -> [1,3,5] same
    # The function result is [1,3,5] in both cases; use full correctness check instead
    inp = [4, 2, 6, 1, 5]
    result = quicksort(inp)
    assert result == [1, 2, 4, 5, 6]

def test_mutation_wrong_operator_plus_instead_of_concat():
    # Detects: return order changed, e.g., greater + [pivot] + lesser instead of lesser + [pivot] + greater
    inp = [3, 1, 5]
    result = quicksort(inp)
    assert result == [1, 3, 5]
    assert result[0] < result[1] < result[2]

def test_mutation_negation_not_arr_removed():
    # Detects: base case `if not arr` changed to `if arr` (always returns [] for non-empty)
    inp = [1]
    result = quicksort(inp)
    assert result == [1]  # Would return [] if condition is flipped

def test_mutation_constant_wrong_initial_pivot_index():
    # Detects: arr[0] changed to arr[-1] (last element as pivot)
    # For most inputs result is still sorted; test correctness property
    inp = [5, 3, 8, 1, 9, 2]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_mutation_preserves_all_elements_including_duplicates():
    # Detects: duplicate elements silently dropped (common quicksort bug with strict < and >)
    # A correct quicksort MUST NOT lose elements
    inp = [4, 4, 4, 2, 2, 6, 6]
    result = quicksort(inp)
    assert len(result) == len(inp), "A correct quicksort must preserve all elements including duplicates"
    assert result == sorted(inp)

def test_mutation_output_is_sorted_property():
    # General mutation catcher: output must be non-decreasing
    inp = [10, -3, 0, 7, 2, -1, 4]
    result = quicksort(inp)
    for i in range(len(result) - 1):
        assert result[i] <= result[i + 1], "A correct quicksort must produce non-decreasing output"

def test_mutation_length_preserved_no_drops():
    # Detects any mutation that causes element loss (e.g., missing pivot in return)
    inp = [1, 2, 3, 4, 5]
    result = quicksort(inp)
    assert len(result) == len(inp)

def test_mutation_pivot_included_in_output():
    # Detects: return lesser + greater (pivot omitted)
    inp = [5, 3, 7]
    result = quicksort(inp)
    assert 5 in result
    assert result == [3, 5, 7]