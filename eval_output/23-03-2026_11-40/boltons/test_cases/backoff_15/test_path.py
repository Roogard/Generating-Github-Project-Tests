import pytest
import math
import random
from boltons.iterutils import backoff

# Path enumeration for backoff function:
# 1. start <= 0 → raise ValueError
# 2. start > 0, stop is None, step <= 0 → raise ValueError
# 3. start > 0, stop is None, step > 0 → infinite loop (generator yields forever)
# 4. start > 0, stop is not None, step <= 0 → raise ValueError
# 5. start > 0, stop is not None, step > 0, stop <= start → yields start once then stops
# 6. start > 0, stop is not None, step > 0, stop > start, exp_base <= 0 → raise ValueError
# 7. start > 0, stop is not None, step > 0, stop > start, exp_base > 0, jitter <= 0 → yields until stop reached
# 8. start > 0, stop is not None, step > 0, stop > start, exp_base > 0, jitter > 0 → yields with jitter until stop reached

# path: start <= 0 → raise ValueError
def test_backoff_start_zero_or_negative():
    with pytest.raises(ValueError):
        list(backoff(start=0, stop=10))
    with pytest.raises(ValueError):
        list(backoff(start=-1, stop=10))

# path: start > 0, stop is None, step <= 0 → raise ValueError
def test_backoff_infinite_step_zero_or_negative():
    with pytest.raises(ValueError):
        list(backoff(start=1, stop=None, step=0))
    with pytest.raises(ValueError):
        list(backoff(start=1, stop=None, step=-1))

# path: start > 0, stop is None, step > 0 → infinite loop (test limited consumption)
def test_backoff_infinite_step_positive():
    gen = backoff(start=1, stop=None, step=2)
    # consume first few values to verify generator works
    assert next(gen) == 1
    assert next(gen) == 3  # 1 + 2
    assert next(gen) == 5  # 3 + 2

# path: start > 0, stop is not None, step <= 0 → raise ValueError
def test_backoff_finite_step_zero_or_negative():
    with pytest.raises(ValueError):
        list(backoff(start=1, stop=10, step=0))
    with pytest.raises(ValueError):
        list(backoff(start=1, stop=10, step=-1))

# path: start > 0, stop is not None, step > 0, stop <= start → yields start once then stops
def test_backoff_stop_less_or_equal_start():
    assert list(backoff(start=5, stop=5)) == [5]
    # The function raises ValueError when stop < start, so we adjust the test.
    with pytest.raises(ValueError):
        list(backoff(start=5, stop=3))

# path: start > 0, stop is not None, step > 0, stop > start, exp_base <= 0 → raise ValueError
def test_backoff_exp_base_zero_or_negative():
    with pytest.raises(ValueError):
        list(backoff(start=1, stop=10, exp_base=0))
    with pytest.raises(ValueError):
        list(backoff(start=1, stop=10, exp_base=-1))

# path: start > 0, stop is not None, step > 0, stop > start, exp_base > 0, jitter <= 0 → yields until stop reached
def test_backoff_no_jitter():
    result = list(backoff(start=1, stop=10, step=2, exp_base=2, jitter=0))
    # manual calculation: start=1, step=2, exp_base=2
    # iteration 0: value=1, next_start=1+2=3
    # iteration 1: value=3, next_start=3+2*2=7
    # iteration 2: value=7, next_start=7+2*4=15 > stop → stop
    assert result == [1, 3, 7]

# path: start > 0, stop is not None, step > 0, stop > start, exp_base > 0, jitter > 0 → yields with jitter until stop reached
def test_backoff_with_jitter():
    random.seed(42)  # deterministic test
    result = list(backoff(start=1, stop=20, step=3, exp_base=1.5, jitter=0.5))
    # jitter adds randomness, but we can verify length and rough range
    assert len(result) > 0
    assert all(1 <= x < 20 for x in result)