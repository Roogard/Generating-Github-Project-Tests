from python_programs.flatten import flatten
import types

# covers: for x in arr (stmt2), isinstance check False (stmt3), else branch (stmt6), yield flatten(x) (stmt7)
def test_flatten_non_list():
    result = list(flatten([42]))
    assert len(result) == 1
    assert isinstance(result[0], types.GeneratorType)
    # the yielded generator yields no items
    assert list(result[0]) == []

# covers: for x in arr (stmt2), isinstance check True (stmt3), recursive for y (stmt4), yield y (stmt5)
def test_flatten_nested_list():
    result = list(flatten([[3]]))
    assert len(result) == 1
    assert isinstance(result[0], types.GeneratorType)
    # generator corresponds to flatten(3) and produces no items
    assert list(result[0]) == []