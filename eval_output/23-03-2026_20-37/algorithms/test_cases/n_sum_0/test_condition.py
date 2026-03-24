from algorithms.array.n_sum import _same_closure_default

# condition: a == b: True
def test_same_closure_default_true():
    assert _same_closure_default(5, 5) == True

# condition: a == b: False
def test_same_closure_default_false():
    assert _same_closure_default(5, 10) == False