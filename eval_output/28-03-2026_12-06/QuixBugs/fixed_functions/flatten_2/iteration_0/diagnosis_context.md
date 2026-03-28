_(showing 10 of 25 failures)_

## Trigger Test(s)

```python
# test_blackbox.py
from python_programs.flatten import flatten

# --- BVA ---

def test_bva_empty_list():
    # Boundary: empty collection
    result = list(flatten([]))
    assert result == []

def test_bva_single_non_list_element():
    # Boundary: single non-list element
    result = list(flatten([42]))
    assert len(result) == 1
    assert result[0] == 42

def test_bva_single_nested_list():
    # Boundary: single element that is itself a list
    result = list(flatten([[1]]))
    assert result == [1]

def test_bva_two_elements():
    # Boundary: minimal multi-element flat list
    result = list(flatten([1, 2]))
    assert result == [1, 2]

def test_bva_deeply_nested_single_element():
    # Boundary: maximum nesting depth with one value
    result = list(flatten([[[[42]]]]))
    assert result == [42]

def test_bva_large_flat_list():
    # Boundary: large collection
    data = list(range(1000))
    result = list(flatten(data))
    assert result == data

def test_bva_large_nested_list():
    # Boundary: large nested collection
    data = [[i] for i in range(1000)]
    result = list(flatten(data))
    assert result == list(range(1000))

# --- ECP ---

def test_ecp_valid_flat_list_of_ints():
    # ECP: valid class — flat list of integers
    result = list(flatten([1, 2, 3, 4, 5]))
    assert result == [1, 2, 3, 4, 5]

def test_ecp_valid_nested_list():
    # ECP: valid class — one level of nesting
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

def test_ecp_valid_mixed_nested_and_flat():
    # ECP: valid class — mix of nested lists and scalars at same level
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

def test_ecp_valid_deeply_nested():
    # ECP: valid class — deeply nested structure
    result = list(flatten([1, [2, [3, [4]]]]))
    assert result == [1, 2, 3, 4]

def test_ecp_valid_strings_as_leaves():
    # ECP: valid class — non-list, non-int elements (strings are not lists)
    result = list(flatten(["a", "b", "c"]))
    assert result == ["a", "b", "c"]

def test_ecp_valid_none_as_element():
    # ECP: valid class — None is not a list, should be yielded as-is
    result = list(flatten([None, None]))
    assert result == [None, None]

def test_ecp_valid_mixed_types():
    # ECP: valid class — heterogeneous scalars
    result = list(flatten([1, "two", 3.0, None]))
    assert result == [1, "two", 3.0, None]

def test_ecp_valid_nested_mixed_types():
    # ECP: valid class — nested structure with mixed types
    result = list(flatten([1, ["two", [3.0]]]))
    assert result == [1, "two", 3.0]

def test_ecp_all_nested_no_scalars_at_top():
    # ECP: valid class — no scalars at top level, all elements are lists
    result = list(flatten([[1, 2], [3, [4, 5]]]))
    assert result == [1, 2, 3, 4, 5]

# --- Mutation Detection ---

def test_mutation_isinstance_check_yields_non_list_not_recursive():
    # Detects mutation: `else: yield flatten(x)` should be `else: yield x`
    # A correct flatten SHOULD yield the scalar value itself, not a generator object
    result = list(flatten([7]))
    assert result == [7], "A correct flatten should yield scalar 7, not a generator object"

def test_mutation_isinstance_check_string_not_recursed():
    # Detects mutation: isinstance check using wrong type (e.g., treating strings as lists)
    # A correct flatten SHOULD NOT recurse into strings
    result = list(flatten(["hello"]))
    assert len(result) == 1
    assert result[0] == "hello"

def test_mutation_yield_vs_yield_from_non_list():
    # Detects mutation: else branch yields generator instead of value
    result = list(flatten([99]))
    assert result[0] == 99
    assert not hasattr(result[0], '__next__'), "Yielded value should be the scalar, not a generator"

def test_mutation_recursive_call_on_flat_element_is_wrong():
    # Detects mutation: calling flatten on a non-list should not wrap it
    data = [1, 2, 3]
    result = list(flatten(data))
    assert all(isinstance(v, int) for v in result), \
        "All yielded values should be ints, not generators"

def test_mutation_off_by_one_nesting_level():
    # Detects mutation: off-by-one in recursion depth
    # A correct flatten([[1]]) should produce exactly [1], not [[1]] or []
    result = list(flatten([[1]]))
    assert result == [1]
    assert len(result) == 1

def test_mutation_preserves_order():
    # Detects mutation: wrong iteration order or swapped variable
    result = list(flatten([1, [2, [3, [4, [5]]]]]))
    assert result == [1, 2, 3, 4, 5], \
        "A correct flatten SHOULD preserve original element order"

def test_mutation_preserves_duplicates():
    # Detects mutation: deduplication introduced accidentally
    result = list(flatten([1, 1, [1, 1]]))
    assert result == [1, 1, 1, 1], \
        "A correct flatten SHOULD preserve duplicate values"

def test_mutation_empty_nested_list():
    # Detects mutation: empty nested list should contribute zero elements
    result = list(flatten([[], []]))
    assert result == [], \
        "A correct flatten of empty nested lists SHOULD yield nothing"

def test_mutation_mixed_empty_and_nonempty():
    # Detects mutation: empty inner list should not affect other elements
    result = list(flatten([[], [1], [], [2, 3]]))
    assert result == [1, 2, 3]

def test_mutation_count_matches_leaves():
    # Property: total count of yielded elements must equal total non-list leaves
    data = [1, [2, 3], [4, [5, 6]]]
    result = list(flatten(data))
    assert len(result) == 6, \
        "A correct flatten SHOULD yield exactly as many items as there are non-list leaves"

def test_mutation_all_results_are_non_list():
    # Property: no yielded element from a correct flatten should be a list
    data = [[1, 2], [3, [4, [5]]]]
    result = list(flatten(data))
    assert all(not isinstance(x, list) for x in result), \
        "A correct flatten SHOULD never yield a list as an element"

def test_mutation_no_generator_objects_in_output():
    # Detects mutation: else branch yields flatten(x) instead of x
    import types
    data = [1, 2, [3, 4]]
    result = list(flatten(data))
    assert all(not isinstance(x, types.GeneratorType) for x in result), \
        "A correct flatten SHOULD never yield generator objects"
```

## Error Message(s)

### [FAILURE] test_bva_single_non_list_element (type: blackbox)
Assertion: assert result[0] == 42
Expected: 42
Actual:   <generator object flatten at 0x0000015FE1E4C4F0>
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\flatten_2\test_blackbox.py:14: in test_bva_single_non_list_element
    assert result[0] == 42
E   assert <generator object flatten at 0x0000015FE1E4C4F0> == 42
```

### [FAILURE] test_bva_single_nested_list (type: blackbox)
Assertion: assert result == [1]
Expected: [1]
Actual:   [<generator o...015FE1E4D4E0>]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\flatten_2\test_blackbox.py:19: in test_bva_single_nested_list
    assert result == [1]
E   assert [<generator o...015FE1E4D4E0>] == [1]
E     
E     At index 0 diff: <generator object flatten at 0x0000015FE1E4D4E0> != 1
E     Use -v to get more diff
```

### [FAILURE] test_bva_two_elements (type: blackbox)
Assertion: assert result == [1, 2]
Expected: [1, 2]
Actual:   [<generator o...015FE1E4E4D0>]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\flatten_2\test_blackbox.py:24: in test_bva_two_elements
    assert result == [1, 2]
E   assert [<generator o...015FE1E4E4D0>] == [1, 2]
E     
E     At index 0 diff: <generator object flatten at 0x0000015FE1E4E3E0> != 1
E     Use -v to get more diff
```

### [FAILURE] test_bva_deeply_nested_single_element (type: blackbox)
Assertion: assert result == [42]
Expected: [42]
Actual:   [<generator o...015FE1E4F880>]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\flatten_2\test_blackbox.py:29: in test_bva_deeply_nested_single_element
    assert result == [42]
E   assert [<generator o...015FE1E4F880>] == [42]
E     
E     At index 0 diff: <generator object flatten at 0x0000015FE1E4F880> != 42
E     Use -v to get more diff
```

### [FAILURE] test_bva_large_flat_list (type: blackbox)
Assertion: assert result == data
Expected: [0, 1, 2, 3, 4, 5, ...]
Actual:   [<generator o...2E988B0>, ...]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\flatten_2\test_blackbox.py:35: in test_bva_large_flat_list
    assert result == data
E   assert [<generator o...2E988B0>, ...] == [0, 1, 2, 3, 4, 5, ...]
E     
E     At index 0 diff: <generator object flatten at 0x0000015FE2E98400> != 0
E     Use -v to get more diff
```

### [FAILURE] test_bva_large_nested_list (type: blackbox)
Assertion: assert result == list(range(1000))
Expected: [0, 1, 2, 3, 4, 5, ...]
Actual:   [<generator o...2EE4400>, ...]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\flatten_2\test_blackbox.py:41: in test_bva_large_nested_list
    assert result == list(range(1000))
E   assert [<generator o...2EE4400>, ...] == [0, 1, 2, 3, 4, 5, ...]
E     
E     At index 0 diff: <generator object flatten at 0x0000015FE2ED3F10> != 0
E     Use -v to get more diff
```

### [FAILURE] test_ecp_valid_flat_list_of_ints (type: blackbox)
Assertion: assert result == [1, 2, 3, 4, 5]
Expected: [1, 2, 3, 4, 5]
Actual:   [<generator o...015FE2F1FF10>]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\flatten_2\test_blackbox.py:48: in test_ecp_valid_flat_list_of_ints
    assert result == [1, 2, 3, 4, 5]
E   assert [<generator o...015FE2F1FF10>] == [1, 2, 3, 4, 5]
E     
E     At index 0 diff: <generator object flatten at 0x0000015FE2F1FB50> != 1
E     Use -v to get more diff
```

### [FAILURE] test_ecp_valid_nested_list (type: blackbox)
Assertion: assert result == [1, 2, 3, 4]
Expected: [1, 2, 3, 4]
Actual:   [<generator o...015FE2F2D210>]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\flatten_2\test_blackbox.py:53: in test_ecp_valid_nested_list
    assert result == [1, 2, 3, 4]
E   assert [<generator o...015FE2F2D210>] == [1, 2, 3, 4]
E     
E     At index 0 diff: <generator object flatten at 0x0000015FE2F2CF40> != 1
E     Use -v to get more diff
```

### [FAILURE] test_ecp_valid_mixed_nested_and_flat (type: blackbox)
Assertion: assert result == [1, 2, 3, 4]
Expected: [1, 2, 3, 4]
Actual:   [<generator o...015FE2F2E110>]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\flatten_2\test_blackbox.py:58: in test_ecp_valid_mixed_nested_and_flat
    assert result == [1, 2, 3, 4]
E   assert [<generator o...015FE2F2E110>] == [1, 2, 3, 4]
E     
E     At index 0 diff: <generator object flatten at 0x0000015FE2F2E020> != 1
E     Use -v to get more diff
```

### [FAILURE] test_ecp_valid_deeply_nested (type: blackbox)
Assertion: assert result == [1, 2, 3, 4]
Expected: [1, 2, 3, 4]
Actual:   [<generator o...015FE2F2F790>]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\flatten_2\test_blackbox.py:63: in test_ecp_valid_deeply_nested
    assert result == [1, 2, 3, 4]
E   assert [<generator o...015FE2F2F790>] == [1, 2, 3, 4]
E     
E     At index 0 diff: <generator object flatten at 0x0000015FE2F2F1F0> != 1
E     Use -v to get more diff
```
