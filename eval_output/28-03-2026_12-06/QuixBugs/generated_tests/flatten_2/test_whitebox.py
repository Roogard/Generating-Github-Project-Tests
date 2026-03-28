from python_programs.flatten import flatten

# Helper to fully realize the generator into a list
def flat(arr):
    return list(flatten(arr))

# --- Statement Coverage ---

def test_stmt_empty_list():
    # Covers the for-loop with zero iterations (loop body never executes)
    result = flat([])
    assert result == []

def test_stmt_flat_list_integers():
    # Covers the else branch: yield flatten(x) for non-list items
    # A correct flatten SHOULD yield the scalar values themselves
    result = flat([1, 2, 3])
    assert len(result) == 3
    # Each yielded item, when itself iterated (since flatten yields generators for scalars),
    # should produce no sub-elements — but a correct flatten SHOULD yield scalars directly.
    # Property: a correct flatten of a flat list should equal that list
    assert result == [1, 2, 3]

def test_stmt_nested_list():
    # Covers the isinstance branch (True): recurse into sub-list
    result = flat([[1, 2], [3]])
    assert result == [1, 2, 3]

def test_stmt_deeply_nested():
    # Covers recursive path through flatten(x) for nested lists
    result = flat([[1, [2, 3]], 4])
    # A correct flatten SHOULD produce all leaf integers in order
    assert result == [1, 2, 3, 4]

# --- Block Coverage ---

def test_block_all_non_list():
    # Block: loop entry, else branch only
    result = flat([10, 20])
    assert result == [10, 20]

def test_block_all_nested():
    # Block: loop entry, isinstance True branch, inner for-y loop
    result = flat([[5, 6], [7, 8]])
    assert result == [5, 6, 7, 8]

def test_block_mixed():
    # Block: both isinstance True and False branches visited
    result = flat([1, [2, 3], 4])
    assert result == [1, 2, 3, 4]

def test_block_nested_empty_sublist():
    # Block: isinstance True, but inner flatten yields nothing (empty sublist)
    result = flat([[], 1])
    assert result == [1]

# --- Condition Coverage ---

def test_cond_isinstance_true():
    # isinstance(x, list): True
    # x is a list, so we recurse
    result = flat([[42]])
    assert result == [42]  # correct flatten should yield 42

def test_cond_isinstance_false_int():
    # isinstance(x, list): False — x is an int
    result = flat([99])
    assert result == [99]  # correct flatten should yield 99

def test_cond_isinstance_false_string():
    # isinstance(x, list): False — x is a string (non-list scalar)
    result = flat(["hello"])
    assert result == ["hello"]  # correct flatten should yield "hello"

def test_cond_isinstance_false_none():
    # isinstance(x, list): False — x is None
    result = flat([None])
    assert result == [None]  # correct flatten should yield None

def test_cond_isinstance_mixed_true_and_false():
    # isinstance(x, list): True for first element, False for second
    # x>0-style: True case and False case both covered in one test
    result = flat([[1, 2], 3])
    assert result == [1, 2, 3]

# --- Path Coverage ---

def test_path_empty_no_iterations():
    # path: enter flatten → for-loop zero iterations → function returns (generator exhausted)
    result = flat([])
    assert result == []

def test_path_single_scalar():
    # path: enter → loop 1 iter → isinstance False → yield scalar → exit
    result = flat([7])
    assert result == [7]

def test_path_single_nested_list():
    # path: enter → loop 1 iter → isinstance True → recurse → inner for-y loop → yield → exit
    result = flat([[1, 2, 3]])
    assert result == [1, 2, 3]

def test_path_multiple_scalars():
    # path: enter → loop multiple iters → isinstance False each time → multiple yields
    result = flat([1, 2, 3, 4, 5])
    assert result == [1, 2, 3, 4, 5]

def test_path_multiple_nested_lists():
    # path: enter → loop multiple iters → isinstance True each time → recurse each time
    result = flat([[1], [2], [3]])
    assert result == [1, 2, 3]

def test_path_mixed_scalars_and_lists():
    # path: enter → loop iters → isinstance True then False alternating
    result = flat([1, [2], 3, [4, 5]])
    assert result == [1, 2, 3, 4, 5]

def test_path_deeply_nested_multiple_levels():
    # path: enter → isinstance True → recurse → isinstance True again → recurse → scalar yield
    result = flat([[[1, 2]], [[3]]]))
    assert result == [1, 2, 3]

def test_path_mixed_depth():
    # path: some branches go 1 level deep, some go 2 levels deep
    result = flat([1, [2, [3, 4]], 5])
    assert result == [1, 2, 3, 4, 5]

def test_path_all_elements_correct_count():
    # Property: correct flatten preserves total count of leaf elements
    inp = [1, [2, [3, [4]]], 5, [6]]
    result = flat(inp)
    assert len(result) == 6
    assert result == [1, 2, 3, 4, 5, 6]

def test_path_no_nested_lists_remain():
    # Property: a correct flatten SHOULD produce no list instances in output
    inp = [[1, [2]], [3, [4, [5]]]]
    result = flat(inp)
    assert all(not isinstance(x, list) for x in result)
    assert result == [1, 2, 3, 4, 5]