```python
import math
import random
import time
from boltons.iterutils import backoff

# Test 1: initial_delay > 0: True, max_delay is None: True, jitter: False
def test_backoff_initial_positive_no_max_no_jitter():
    """Test basic backoff with positive initial, no max, no jitter"""
    gen = backoff(initial_delay=1.0, max_delay=None, jitter=False)
    delays = [next(gen) for _ in range(5)]
    # initial_delay > 0: True (1.0 > 0)
    # max_delay is None: True
    # jitter: False
    assert delays[0] == 1.0
    assert delays[1] == 2.0  # 1.0 * 2
    assert delays[2] == 4.0  # 2.0 * 2

# Test 2: initial_delay > 0: False, max_delay is None: True, jitter: False
def test_backoff_initial_zero_no_max_no_jitter():
    """Test backoff with zero initial delay, no max, no jitter"""
    gen = backoff(initial_delay=0.0, max_delay=None, jitter=False)
    delays = [next(gen) for _ in range(3)]
    # initial_delay > 0: False (0.0 > 0)
    # max_delay is None: True
    # jitter: False
    assert delays[0] == 0.0
    assert delays[1] == 0.0  # 0.0 * 2
    assert delays[2] == 0.0  # 0.0 * 2

# Test 3: initial_delay > 0: True, max_delay is None: False, jitter: False
def test_backoff_with_max_no_jitter():
    """Test backoff with max delay, no jitter"""
    gen = backoff(initial_delay=1.0, max_delay=3.0, jitter=False)
    delays = [next(gen) for _ in range(5)]
    # initial_delay > 0: True (1.0 > 0)
    # max_delay is None: False (max_delay=3.0)
    # jitter: False
    assert delays[0] == 1.0
    assert delays[1] == 2.0  # 1.0 * 2
    assert delays[2] == 3.0  # min(4.0, 3.0) = 3.0
    assert delays[3] == 3.0  # stays at max
    assert delays[4] == 3.0

# Test 4: initial_delay > 0: True, max_delay is None: True, jitter: True
def test_backoff_with_jitter_no_max():
    """Test backoff with jitter, no max delay"""
    gen = backoff(initial_delay=1.0, max_delay=None, jitter=True)
    delay = next(gen)
    # initial_delay > 0: True (1.0 > 0)
    # max_delay is None: True
    # jitter: True
    assert 0.5 <= delay <= 1.5  # 1.0 ± 50%

# Test 5: initial_delay > 0: True, max_delay is None: False, jitter: True
def test_backoff_with_max_and_jitter():
    """Test backoff with max delay and jitter"""
    gen = backoff(initial_delay=1.0, max_delay=2.0, jitter=True)
    delays = [next(gen) for _ in range(3)]
    # initial_delay > 0: True (1.0 > 0)
    # max_delay is None: False (max_delay=2.0)
    # jitter: True
    assert 0.5 <= delays[0] <= 1.5  # 1.0 ± 50%
    # Second delay should be capped at max_delay=2.0 with jitter
    assert 1.0 <= delays[1] <= 2.0  # min(2.0*2, 2.0)=2.0 ± 50% → 1.0-2.0
    assert 1.0 <= delays[2] <= 2.0  # stays at max with jitter

# Test 6: initial_delay > 0: False, max_delay is None: False, jitter: True
def test_backoff_zero_initial_with_max_and_jitter():
    """Test backoff with zero initial, max delay, and jitter"""
    gen = backoff(initial_delay=0.0, max_delay=1.0, jitter=True)
    delays = [next(gen) for _ in range(3)]
    # initial_delay > 0: False (0.0 > 0)
    # max_delay is None: False (max_delay=1.0)
    # jitter: True
    assert 0.0 <= delays[0] <= 0.0  # 0.0 ± 50% = 0.0
    assert 0.0 <= delays[1] <= 0.0  # 0.0 * 2 = 0.0 ± 50% = 0.0
    assert 0.0 <= delays[2] <= 0.0

# Test 7: initial_delay > 0: False, max_delay is None: True, jitter: True
def test_backoff_zero_initial_jitter_no_max():
    """Test backoff with zero initial, jitter, no max"""
    gen = backoff(initial_delay=0.0, max_delay=None, jitter=True)
    delays = [next(gen) for _ in range(3)]
    # initial_delay > 0: False (0.0 > 0)
    # max_delay is None: True
    # jitter: True
    assert delays[0] == 0.0  # 0.0 ± 50% = 0.0
    assert delays[1] == 0.0  # 0.0 * 2 = 0.0 ± 50% = 0.0
    assert delays[2] == 0.0

# Test 8: initial_delay > 0: False, max_delay is None: False, jitter: False
def test_backoff_zero_initial_with_max_no_jitter():
    """Test backoff with zero initial, max delay, no jitter"""
    gen = backoff(initial_delay=0.0, max_delay=5.0, jitter=False)
    delays = [next(gen) for _ in range(3)]
    # initial_delay > 0: False (0.0 > 0)
    # max_delay is None: False (max_delay=5.0)
    # jitter: False
    assert delays[0] == 0.0
    assert delays[1] == 0.0  # 0.0 * 2
    assert delays[2] == 0.0

# Test 9: initial_delay > 0: True, max_delay is None: False, jitter: False with exact max
def test_backoff_exact_max_hit():
    """Test backoff where calculated delay exactly equals max_delay"""
    gen = backoff(initial_delay=2.0, max_delay=4.0, jitter=False)
    delays = [next(gen) for _ in range(3)]
    # initial_delay > 0: True (2.0 > 0)
    # max_delay is None: False (max_delay=4.0)
    # jitter: False
    assert delays[0] == 2.0
    assert delays[1] == 4.0  # 2.0 * 2 = 4.0 exactly equals max
    assert delays[2] == 4.0  # stays at max

# Test 10: initial_delay > 0: True, max_delay is None: True, jitter: True multiple iterations
def test_backoff_jitter_randomness():
    """Test that jitter produces different values (not guaranteed but likely)"""
    gen1 = backoff(initial_delay=1.0, max_delay=None, jitter=True)
    gen2 = backoff(initial_delay=1.0, max_delay=None, jitter=True)
    delays1 = [next(gen1) for _ in range(10)]
    delays2 = [next(gen2) for _ in range(10)]
    # initial_delay > 0: True (1.0 > 0)
    # max_delay is None: True
    # jitter: True
    # With jitter, sequences should differ (very high probability)
    assert delays1 != delays2

# Test 11: Edge case - negative initial_delay (treated as > 0: False)
def test_backoff_negative_initial():
    """Test backoff with negative initial delay"""
    gen = backoff(initial_delay=-1.0, max_delay=None, jitter=False)
    delays = [next(gen) for _ in range(3)]
    # initial_delay > 0: False (-1.0 > 0)
    # max_delay is None: True
    # jitter: False
    assert delays[0] == -1.0
    assert delays[1] == -2.0  # -1.0 * 2
    assert delays[2] == -4.0  # -2.0 * 2
```