import pytest
from boltons.iterutils import backoff

def test_backoff_with_min_delay_zero():
    delays = list(backoff(min_delay=0, max_delay=10, factor=2, jitter=False))
    assert len(delays) > 0
    assert delays[0] == 0

def test_backoff_with_min_delay_one():
    delays = list(backoff(min_delay=1, max_delay=10, factor=2, jitter=False))
    assert delays[0] == 1

def test_backoff_with_max_delay_at_boundary():
    delays = list(backoff(min_delay=1, max_delay=10, factor=2, jitter=False))
    for delay in delays:
        assert delay <= 10

def test_backoff_exceeds_max_delay():
    delays = list(backoff(min_delay=9, max_delay=10, factor=2, jitter=False))
    assert delays[0] == 9
    assert delays[1] == 10
    assert delays[2] == 10

def test_backoff_with_factor_one():
    delays = list(backoff(min_delay=1, max_delay=5, factor=1, jitter=False))
    assert delays[0] == 1
    assert delays[1] == 1
    assert delays[2] == 1

def test_backoff_with_factor_above_one():
    delays = list(backoff(min_delay=1, max_delay=20, factor=2, jitter=False))
    assert delays[0] == 1
    assert delays[1] == 2
    assert delays[2] == 4
    assert delays[3] == 8
    assert delays[4] == 16
    assert delays[5] == 20

def test_backoff_with_jitter_true():
    delays = list(backoff(min_delay=1, max_delay=10, factor=2, jitter=True))
    for delay in delays:
        assert 0 <= delay <= 10

def test_backoff_with_jitter_false():
    delays = list(backoff(min_delay=1, max_delay=10, factor=2, jitter=False))
    expected = [1, 2, 4, 8, 10, 10]
    for d, e in zip(delays[:len(expected)], expected):
        assert d == e

def test_backoff_with_zero_iterations():
    delays = list(backoff(min_delay=1, max_delay=10, factor=2, jitter=False, max_iterations=0))
    assert len(delays) == 0

def test_backoff_with_one_iteration():
    delays = list(backoff(min_delay=1, max_delay=10, factor=2, jitter=False, max_iterations=1))
    assert len(delays) == 1
    assert delays[0] == 1

def test_backoff_with_large_iterations():
    delays = list(backoff(min_delay=1, max_delay=10, factor=2, jitter=False, max_iterations=100))
    assert len(delays) == 100
    for delay in delays:
        assert delay == 10

def test_backoff_with_negative_min_delay():
    with pytest.raises(ValueError):
        list(backoff(min_delay=-1, max_delay=10, factor=2, jitter=False))

def test_backoff_with_min_delay_greater_than_max_delay():
    with pytest.raises(ValueError):
        list(backoff(min_delay=11, max_delay=10, factor=2, jitter=False))

def test_backoff_with_factor_zero():
    with pytest.raises(ValueError):
        list(backoff(min_delay=1, max_delay=10, factor=0, jitter=False))

def test_backoff_with_factor_negative():
    with pytest.raises(ValueError):
        list(backoff(min_delay=1, max_delay=10, factor=-1, jitter=False))

def test_backoff_with_max_iterations_negative():
    delays = list(backoff(min_delay=1, max_delay=10, factor=2, jitter=False, max_iterations=-1))
    assert len(delays) == 0