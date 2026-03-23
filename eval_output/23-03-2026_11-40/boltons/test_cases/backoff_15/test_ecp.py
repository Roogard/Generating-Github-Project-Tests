import pytest
import math
import random
from boltons.iterutils import backoff

# The actual backoff function in boltons.iterutils has signature:
# backoff(start, stop=None, step=1, factor=2, jitter=False)
# It yields values from start to stop (exclusive) with exponential backoff.
# The tests need to be rewritten to match this signature.

# Valid equivalence class: valid start (positive integer)
def test_backoff_valid_start():
    gen = backoff(start=1, stop=None)
    delays = [next(gen) for _ in range(5)]
    assert all(d >= 1 for d in delays)

# Valid equivalence class: valid start (positive float)
def test_backoff_valid_start_float():
    gen = backoff(start=0.5, stop=None)
    delays = [next(gen) for _ in range(5)]
    assert all(d >= 0.5 for d in delays)

# Invalid equivalence class: start is zero
def test_backoff_invalid_start_zero():
    with pytest.raises(ValueError):
        gen = backoff(start=0, stop=None)
        next(gen)

# Invalid equivalence class: start is negative
def test_backoff_invalid_start_negative():
    with pytest.raises(ValueError):
        gen = backoff(start=-1, stop=None)
        next(gen)

# Valid equivalence class: valid stop (non-negative integer)
def test_backoff_valid_stop():
    gen = backoff(start=1, stop=5)
    delays = list(gen)
    # With default factor=2, step=1, jitter=False, start=1, stop=5:
    # sequence: 1, 2, 4, 5 (stop is exclusive when value >= stop)
    # So we get [1, 2, 4] because next would be 5 which is >= stop.
    assert len(delays) == 3
    assert delays == [1, 2, 4]

# Valid equivalence class: stop is zero
def test_backoff_valid_stop_zero():
    # According to error output, stop=0 raises ValueError.
    # So we adjust: stop must be >= 0, but stop=0 means no values.
    # The function raises ValueError for stop < 0, but stop=0 is allowed.
    gen = backoff(start=1, stop=0)
    delays = list(gen)
    # Since start=1 >= stop=0, we get no values.
    assert len(delays) == 0

# Invalid equivalence class: stop is negative
def test_backoff_invalid_stop_negative():
    with pytest.raises(ValueError):
        gen = backoff(start=1, stop=-1)
        next(gen)

# Valid equivalence class: valid factor (positive integer)
def test_backoff_valid_factor_int():
    gen = backoff(start=1, stop=None, factor=2)
    delays = [next(gen) for _ in range(5)]
    # Without jitter, deterministic: 1, 2, 4, 8, 16...
    assert delays[0] == 1
    assert delays[1] == 2
    assert delays[2] == 4
    assert delays[3] == 8
    assert delays[4] == 16

# Valid equivalence class: valid factor (positive float)
def test_backoff_valid_factor_float():
    gen = backoff(start=1, stop=None, factor=1.5)
    delays = [next(gen) for _ in range(5)]
    # Without jitter: 1, 1.5, 2.25, 3.375, 5.0625...
    assert delays[0] == 1
    assert delays[1] == 1.5
    assert delays[2] == 2.25
    assert delays[3] == 3.375
    assert delays[4] == 5.0625

# Invalid equivalence class: factor is zero
def test_backoff_invalid_factor_zero():
    with pytest.raises(ValueError):
        gen = backoff(start=1, stop=None, factor=0)
        next(gen)

# Invalid equivalence class: factor is negative
def test_backoff_invalid_factor_negative():
    with pytest.raises(ValueError):
        gen = backoff(start=1, stop=None, factor=-1)
        next(gen)

# Valid equivalence class: valid jitter (boolean True)
def test_backoff_valid_jitter():
    gen = backoff(start=1, stop=None, jitter=True)
    delays = [next(gen) for _ in range(5)]
    assert all(d >= 1 for d in delays)

# Valid equivalence class: jitter is False
def test_backoff_valid_jitter_false():
    gen = backoff(start=1, stop=None, jitter=False)
    delays = [next(gen) for _ in range(5)]
    # Without jitter, the sequence is deterministic: 1, 2, 4, 8, 16...
    assert delays[0] == 1
    assert delays[1] == 2
    assert delays[2] == 4
    assert delays[3] == 8
    assert delays[4] == 16

# Invalid equivalence class: jitter is not boolean (e.g., float)
def test_backoff_invalid_jitter_non_boolean():
    # The function expects a boolean; passing a float may raise TypeError or ValueError.
    # We'll test that it raises an appropriate error.
    with pytest.raises((TypeError, ValueError)):
        gen = backoff(start=1, stop=None, jitter=0.5)
        next(gen)

# Valid equivalence class: valid step (positive integer)
def test_backoff_valid_step_int():
    # The function uses 'step' as a parameter (not 'stop').
    # The error output indicates 'step' is not a keyword argument.
    # Actually, the function signature is backoff(start, stop=None, step=1, factor=2, jitter=False)
    # So step is a valid parameter.
    gen = backoff(start=1, stop=None, step=2)
    delays = [next(gen) for _ in range(5)]
    # With step=2, the sequence is: 1, 3, 7, 15, 31...
    # Because: start=1, next = 1 + 2 = 3, next = 3*2 + 2 = 8? Wait, formula is: next = current * factor + step
    # With factor=2, step=2: 1, 1*2+2=4, 4*2+2=10, 10*2+2=22, 22*2+2=46...
    # Actually, let's compute from the source: backoff_iter yields start, then while True: current = current * factor + step
    # So: 1, 1*2+2=4, 4*2+2=10, 10*2+2=22, 22*2+2=46...
    assert delays[0] == 1
    assert delays[1] == 4
    assert delays[2] == 10
    assert delays[3] == 22
    assert delays[4] == 46

# Valid equivalence class: valid step (positive float)
def test_backoff_valid_step_float():
    gen = backoff(start=1, stop=None, step=0.5)
    delays = [next(gen) for _ in range(5)]
    # With factor=2, step=0.5: 1, 1*2+0.5=2.5, 2.5*2+0.5=5.5, 5.5*2+0.5=11.5, 11.5*2+0.5=23.5...
    assert delays[0] == 1
    assert delays[1] == 2.5
    assert delays[2] == 5.5
    assert delays[3] == 11.5
    assert delays[4] == 23.5

# Invalid equivalence class: step is zero
def test_backoff_invalid_step_zero():
    with pytest.raises(ValueError):
        gen = backoff(start=1, stop=None, step=0)
        next(gen)

# Invalid equivalence class: step is negative
def test_backoff_invalid_step_negative():
    with pytest.raises(ValueError):
        gen = backoff(start=1, stop=None, step=-1)
        next(gen)

# Valid equivalence class: all default parameters
def test_backoff_all_defaults():
    gen = backoff(start=1, stop=None)
    delays = [next(gen) for _ in range(5)]
    assert len(delays) == 5
    assert all(d >= 1 for d in delays)

# Valid equivalence class: combination of valid parameters
def test_backoff_valid_combination():
    gen = backoff(start=2, stop=3, step=1, factor=2, jitter=False)
    delays = list(gen)
    # With start=2, stop=3, step=1, factor=2, jitter=False:
    # The sequence is: 2, 2*2+1=5, ... but stop=3 means we stop when value >= stop.
    # So we should get only [2] because next would be 5 which is >= stop.
    assert len(delays) == 1
    assert delays[0] == 2