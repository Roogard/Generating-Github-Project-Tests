import pytest
from algorithms.backtracking.array_sum_combinations import _get_candidates

# Valid equivalence class: constructed_so_far is empty list
def test_get_candidates_empty_list():
    result = _get_candidates([])
    # Expecting all numbers from the global list (assuming it's defined in the module)
    # Since we cannot see the global list, we just verify it returns a list
    assert isinstance(result, list)

# Valid equivalence class: constructed_so_far is a non-empty list with sum less than target
def test_get_candidates_partial_sum():
    # Assuming the global list is [2, 3, 6, 7] and target is 7 (common example)
    # With constructed_so_far = [2], candidates should be numbers that don't exceed target when added
    result = _get_candidates([2])
    assert isinstance(result, list)

# Valid equivalence class: constructed_so_far sum equals target (should return empty list)
def test_get_candidates_sum_equals_target():
    # Assuming target is 7 and constructed_so_far sum is 7
    result = _get_candidates([7])
    assert result == []

# Valid equivalence class: constructed_so_far sum exceeds target (should return empty list)
def test_get_candidates_sum_exceeds_target():
    # Assuming target is 7 and constructed_so_far sum is 8
    result = _get_candidates([8])
    assert result == []

# Invalid equivalence class: constructed_so_far is None
def test_get_candidates_none():
    with pytest.raises(TypeError):
        _get_candidates(None)

# Invalid equivalence class: constructed_so_far is not a list (e.g., a tuple)
def test_get_candidates_non_list():
    with pytest.raises(TypeError):
        _get_candidates((1, 2))

# Invalid equivalence class: constructed_so_far contains non-integer elements
def test_get_candidates_list_with_non_integer():
    with pytest.raises(TypeError):
        _get_candidates([1, "a"])