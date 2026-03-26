from python_programs.flatten import flatten
import types

def test_flatten_non_list_branch():
    # isinstance(x, list): False
    result = list(flatten([42]))
    assert len(result) == 1
    assert isinstance(result[0], types.GeneratorType)

def test_flatten_list_and_non_list_branches():
    # x=[1,2]: True, x=3: False
    result = list(flatten([[1, 2], 3]))
    # list branch yields flattened values
    assert result[0] == 1
    assert result[1] == 2
    # non-list branch yields a generator
    assert isinstance(result[2], types.GeneratorType)