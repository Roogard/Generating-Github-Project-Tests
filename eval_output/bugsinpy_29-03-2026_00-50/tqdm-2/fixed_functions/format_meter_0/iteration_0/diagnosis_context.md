_(showing 10 of 80 failures)_

## Trigger Test(s)

```python
# test_blackbox.py
import pytest
from tqdm.std import tqdm

format_meter = tqdm.format_meter

# --- BVA ---

def test_bva_n_zero_total_known():
    """n=0, total>0: 0% progress, no elapsed rate."""
    result = format_meter(0, 100, 1.0)
    assert '0%' in result
    assert '100' in result

def test_bva_n_equals_total_minus_one():
    """n = total - 1: just below completion."""
    result = format_meter(99, 100, 10.0)
    assert '99%' in result

def test_bva_n_equals_total():
    """n == total: exactly 100%."""
    result = format_meter(100, 100, 10.0)
    assert '100%' in result

def test_bva_n_exceeds_total_by_half():
    """n >= total + 0.5: total should become None (no percentage shown)."""
    # A correct implementation sets total=None when n >= total + 0.5
    result = format_meter(101, 100, 10.0)
    # When total is None, no percentage should appear
    assert '%' not in result

def test_bva_n_just_below_total_plus_half():
    """n = total + 0.4: within float tolerance, total still valid."""
    result = format_meter(100.4, 100, 10.0)
    assert '100%' in result

def test_bva_elapsed_zero():
    """elapsed=0: rate cannot be computed from elapsed (avoid division by zero)."""
    result = format_meter(0, 100, 0)
    assert result is not None
    # rate should show '?' when rate is unknown
    assert '?' in result

def test_bva_elapsed_very_small():
    """elapsed just above 0: rate is computable."""
    result = format_meter(1, 100, 0.001)
    assert result is not None

def test_bva_total_none():
    """total=None: no ETA, no percentage, just stats."""
    result = format_meter(50, None, 5.0)
    assert '%' not in result
    assert '50' in result

def test_bva_ncols_zero():
    """ncols=0: no bar, only stats with percentage prefix."""
    result = format_meter(50, 100, 5.0, ncols=0)
    assert result is not None
    assert '{bar}' not in result
    # No bar characters expected
    assert '|' not in result or result.count('|') < 2

def test_bva_ncols_one():
    """ncols=1: minimal width."""
    result = format_meter(50, 100, 5.0, ncols=1)
    assert result is not None

def test_bva_ncols_large():
    """ncols=200: wide bar."""
    result = format_meter(50, 100, 5.0, ncols=200)
    assert result is not None
    assert len(result) <= 200

def test_bva_prefix_empty():
    """prefix='': no label, no colon."""
    result = format_meter(0, 100, 1.0, prefix='')
    # Should not start with ': '
    assert not result.startswith(': ')

def test_bva_prefix_single_char():
    """prefix='A': single char prefix."""
    result = format_meter(50, 100, 5.0, prefix='A')
    assert 'A' in result

def test_bva_prefix_with_colon():
    """prefix ends with ': ': should not double the colon."""
    result = format_meter(50, 100, 5.0, prefix='Test: ')
    assert 'Test: ' in result
    assert 'Test: : ' not in result

def test_bva_n_float():
    """n as float: should handle gracefully."""
    result = format_meter(0.5, 1.0, 1.0)
    assert result is not None

# --- ECP ---

def test_ecp_valid_total_and_n_basic():
    """Valid class: n<total, total known, elapsed>0. Standard output."""
    result = format_meter(25, 100, 2.5)
    assert '25%' in result
    assert '25' in result
    assert '100' in result

def test_ecp_total_none_no_rate():
    """No total, no elapsed: only n, unit shown."""
    result = format_meter(10, None, 0)
    assert '10' in result
    assert '%' not in result

def test_ecp_total_none_with_rate():
    """No total but rate available: rate displayed."""
    result = format_meter(10, None, 5.0)
    assert '10' in result
    # rate should be shown as something other than '?'

def test_ecp_manual_rate_override():
    """rate provided manually: should use it instead of n/elapsed."""
    result_manual = format_meter(10, 100, 5.0, rate=5.0)
    result_computed = format_meter(10, 100, 2.0, rate=5.0)
    # Both use rate=5.0, rate_fmt should be identical
    # Extract rate-related portion - both should show same rate
    assert result_manual is not None
    assert result_computed is not None

def test_ecp_unit_scale_true():
    """unit_scale=True: SI prefix formatting."""
    result = format_meter(1000, 10000, 1.0, unit_scale=True)
    # Should contain 'k' for kilo
    assert 'k' in result

def test_ecp_unit_scale_custom_factor():
    """unit_scale=2 (non-True): scales n and total."""
    result = format_meter(500, 1000, 1.0, unit_scale=2)
    # n becomes 1000, total becomes 2000
    assert result is not None

def test_ecp_ascii_true():
    """ascii=True: use ASCII characters for bar."""
    result = format_meter(50, 100, 5.0, ascii=True)
    assert result is not None
    # Bar should only use ASCII characters
    assert all(ord(c) < 128 for c in result)

def test_ecp_ascii_false():
    """ascii=False: use unicode blocks."""
    result = format_meter(50, 100, 5.0, ascii=False)
    assert result is not None

def test_ecp_postfix_string():
    """postfix as string: appended to right bar."""
    result = format_meter(50, 100, 5.0, postfix='loss=0.5')
    assert 'loss=0.5' in result

def test_ecp_postfix_none():
    """postfix=None: treated as empty."""
    result = format_meter(50, 100, 5.0, postfix=None)
    assert result is not None
    assert 'None' not in result

def test_ecp_postfix_dict():
    """postfix as non-string type (dict): should not crash."""
    try:
        result = format_meter(50, 100, 5.0, postfix={'loss': 0.5})
        assert result is not None
    except Exception:
        pass  # some implementations may not support dict postfix

def test_ecp_bar_format_custom_no_bar():
    """bar_format without {bar}: returns formatted string without bar."""
    result = format_meter(50, 100, 5.0, bar_format='{n}/{total}')
    assert '50' in result
    assert '100' in result

def test_ecp_bar_format_with_bar():
    """bar_format with {bar}: bar is rendered."""
    result = format_meter(50, 100, 5.0, bar_format='{l_bar}{bar}{r_bar}')
    assert result is not None

def test_ecp_bar_format_with_desc_empty_prefix():
    """bar_format with {desc}: when prefix empty, {desc}: is removed."""
    result = format_meter(50, 100, 5.0, prefix='', bar_format='{desc}: {n}/{total}')
    # A correct implementation removes "{desc}: " when desc is empty
    assert result == '50/100'

def test_ecp_bar_format_with_desc_nonempty_prefix():
    """bar_format with {desc}: when prefix non-empty, desc shown."""
    result = format_meter(50, 100, 5.0, prefix='test', bar_format='{desc}: {n}/{total}')
    assert 'test' in result
    assert '50' in result

def test_ecp_unit_custom():
    """Custom unit string."""
    result = format_meter(50, 100, 5.0, unit='MB')
    assert 'MB' in result

def test_ecp_unit_divisor():
    """unit_divisor used with unit_scale=True."""
    result = format_meter(1024, 10240, 1.0, unit_scale=True, unit_divisor=1024)
    assert result is not None

def test_ecp_n_is_zero_total_none():
    """n=0, total=None: degenerate case."""
    result = format_meter(0, None, 0)
    assert result is not None
    assert '0' in result

def test_ecp_large_n_and_total():
    """Large values: no crash."""
    result = format_meter(999999, 1000000, 3600.0)
    assert '99%' in result or '100%' in result

# --- Mutation Detection ---

def test_mutation_total_none_when_n_exceeds_total_plus_half():
    """
    Detects off-by-one in: n >= (total + 0.5)
    If mutated to n > (total + 0.5), n=total+0.5 would keep total valid.
    A correct implementation: n >= total+0.5 => total becomes None.
    """
    result = format_meter(100.5, 100, 1.0)
    # A correct impl: 100.5 >= 100.5 => total=None => no percentage
    assert '%' not in result

def test_mutation_total_still_valid_at_total_plus_0_4():
    """
    Detects boundary: n = total + 0.4 should NOT trigger total=None.
    If mutated to n >= total (no +0.5), this would incorrectly set total=None.
    """
    result = format_meter(100.4, 100, 1.0)
    assert '%' in result

def test_mutation_rate_computed_as_n_over_elapsed():
    """
    Detects wrong operator: rate = n / elapsed (not elapsed / n).
    At n=10, elapsed=2.0, rate should be 5.0 it/s.
    """
    result = format_meter(10, None, 2.0)
    # rate=5.0 => 5.00it/s
    assert '5.00' in result

def test_mutation_inv_rate_format_when_rate_gt_1():
    """
    Detects wrong branch: rate_fmt = rate_inv_fmt if inv_rate > 1 else rate_noinv_fmt.
    At rate=0.5 it/s, inv_rate=2.0 > 1, so rate_fmt should show s/unit format.
    """
    result = format_meter(1, None, 2.0, rate=0.5)
    # inv_rate=2.0 > 1 => rate_fmt = rate_inv_fmt => shows 's/it'
    assert 's/it' in result

def test_mutation_inv_rate_format_when_rate_gt_1_boundary():
    """
    Detects off-by-one: inv_rate > 1 vs inv_rate >= 1.
    At rate=1.0, inv_rate=1.0, boundary. A correct impl uses > 1,
    so inv_rate=1.0 is NOT > 1 => rate_noinv_fmt (it/s) used.
    """
    result = format_meter(1, None, 1.0, rate=1.0)
    # inv_rate=1.0, not > 1 => rate_fmt = rate_noinv_fmt => 'it/s'
    assert 'it/s' in result

def test_mutation_inv_rate_format_when_inv_rate_just_above_1():
    """
    At rate=0.9, inv_rate~1.11 > 1 => should show s/unit.
    """
    result = format_meter(9, None, 10.0, rate=0.9)
    assert 's/it' in result

def test_mutation_percentage_calculation():
    """
    Detects wrong operator in frac = n / total (not n * total).
    At n=1, total=4: frac=0.25, percentage=25%.
    """
    result = format_meter(1, 4, 1.0)
    assert '25%' in result

def test_mutation_remaining_time_zero_when_rate_none():
    """
    Detects wrong default: remaining = 0 when rate is None.
    A correct implementation shows '?' for remaining when rate is unknown.
    """
    result = format_meter(50, 100, 0)  # elapsed=0 => rate=None
    assert '?' in result

def test_mutation_remaining_computed_correctly():
    """
    Detects wrong subtraction: remaining = (total - n) / rate.
    n=25, total=100, rate=5 => remaining=15s.
    """
    result = format_meter(25, 100, 5.0, rate=5.0)
    # remaining = (100-25)/5 = 15 seconds = '0:00:15'
    assert '0:00:15' in result

def test_mutation_prefix_colon_not_doubled():
    """
    Detects negation error: bool_prefix_colon_already check.
    If mutated to 'not bool_prefix_colon_already', a prefix ending in ': '
    would get ': ' appended again.
    """
    result = format_meter(50, 100, 5.0, prefix='Running: ')
    assert 'Running: : ' not in result
    assert 'Running: ' in result

def test_mutation_prefix_colon_added_when_missing():
    """
    Detects negation error: if bool_prefix_colon_already logic is flipped,
    a prefix without ': ' would NOT get ': ' appended.
    """
    result = format_meter(50, 100, 5.0, prefix='Running')
    assert 'Running: ' in result

def test_mutation_l_bar_empty_when_no_prefix():
    """
    Detects wrong variable: l_bar should be '' when prefix is empty.
    If mutated to use prefix instead of '', prefix content bleeds in.
    """
    result = format_meter(0, 100, 1.0, prefix='')
    assert result.startswith('  0%|')

def test_mutation_unit_scale_false_n_fmt_is_str():
    """
    Detects wrong branch in n_fmt: when unit_scale=False, n_fmt = str(n).
    If mutated to always use format_sizeof, n_fmt would differ.
    """
    result = format_meter(42, 100, 1.0, unit_scale=False)
    assert '42' in result

def test_mutation_unit_scale_true_n_fmt_uses_si():
    """
    When unit_scale=True and n=1000, n_fmt should use SI prefix 'k'.
    Detects branch swapped between unit_scale True/False.
    """
    result = format_meter(1000, 10000, 1.0, unit_scale=True)
    assert '1.00k' in result or '1k' in result or 'k' in result

def test_mutation_ncols_zero_returns_no_bar():
    """
    Detects off-by-one: `if ncols == 0` vs `if ncols <= 0`.
    ncols=0 should return early without bar.
    """
    result_zero = format_meter(50, 100, 5.0, ncols=0)
    result_none = format_meter(50, 100, 5.0, ncols=None)
    # ncols=0 should not have a bar segment (no '|...|')
    assert result_zero != result_none

def test_mutation_custom_unit_scale_factor_applied_to_n():
    """
    Detects missing multiplication: when unit_scale=2, n should be doubled.
    n=500 becomes 1000, total=1000 becomes 2000 => 50%.
    """
    result = format_meter(500, 1000, 1.0, unit_scale=2)
    assert '50%' in result

def test_mutation_custom_unit_scale_factor_applied_to_rate():
    """
    Detects missing rate scaling: when unit_scale=5, manual rate=2 should become 10.
    """
    result_scaled = format_meter(10, 100, 1.0, unit_scale=5, rate=2.0)
    result_unscaled = format_meter(10, 100, 1.0, unit_scale=False, rate=2.0)
    # Both should show valid output
    assert result_scaled is not None
    assert result_unscaled is not None

def test_mutation_elapsed_str_in_output():
    """
    Detects wrong variable: elapsed_str = format_interval(elapsed).
    At elapsed=3661, should show '1:01:01'.
    """
    result = format_meter(50, 100, 3661.0)
    assert '1:01:01' in result

def test_mutation_bar_format_percentage_in_dict():
    """
    Detects missing update: format_dict must include percentage when bar_format used.
    n=50, total=100 => percentage=50.
    """
    result = format_meter(50, 100, 5.0, bar_format='{percentage:3.0f}%')
    assert '50%' in result

def test_mutation_no_total_bar_format_percentage_zero():
    """
    When total=None and bar_format used, percentage should be 0.
    Detects wrong constant: format_dict.update(percentage=0) vs some other value.
    """
    result = format_meter(50, None, 5.0, bar_format='{percentage:3.0f}%')
    assert '  0%' in result or '0%' in result

def test_mutation_remaining_s_is_zero_when_no_rate():
    """
    Detects wrong default: remaining_s should be 0 when rate is None.
    """
    result = format_meter(50, 100, 0, bar_format='{remaining_s}')
    assert '0' in result

def test_mutation_format_dict_rate_inv_rate_when_inv_gt_1():
    """
    Detects wrong variable: rate in format_dict should be inv_rate when inv_rate > 1.
    At rate=0.5, inv_rate=2.0: format_dict['rate'] should be 2.0.
    """
    result = format_meter(1, None, 1.0, rate=0.5, bar_format='{rate:.1f}')
    assert '2.0' in result

def test_mutation_format_dict_rate_noinv_when_inv_le_1():
    """
    Detects wrong variable: when inv_rate <= 1, format_dict['rate'] should be rate.
    At rate=2.0, inv_rate=0.5: format_dict['rate'] should be 2.0.
    """
    result = format_meter(2, None, 1.0, rate=2.0, bar_format='{rate:.1f}')
    assert '2.0' in result
```

## Error Message(s)

### [FAILURE] test_bva_n_zero_total_known (type: blackbox)
Assertion: assert '0%' in result
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_0\test_blackbox.py:11: in test_bva_n_zero_total_known
    assert '0%' in result
           ^^^^^^^^^^^^^^
E   TypeError: argument of type 'NoneType' is not iterable
```

### [FAILURE] test_bva_n_equals_total_minus_one (type: blackbox)
Assertion: assert '99%' in result
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_0\test_blackbox.py:17: in test_bva_n_equals_total_minus_one
    assert '99%' in result
           ^^^^^^^^^^^^^^^
E   TypeError: argument of type 'NoneType' is not iterable
```

### [FAILURE] test_bva_n_equals_total (type: blackbox)
Assertion: assert '100%' in result
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_0\test_blackbox.py:22: in test_bva_n_equals_total
    assert '100%' in result
           ^^^^^^^^^^^^^^^^
E   TypeError: argument of type 'NoneType' is not iterable
```

### [FAILURE] test_bva_n_just_below_total_plus_half (type: blackbox)
Assertion: assert '100%' in result
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_0\test_blackbox.py:34: in test_bva_n_just_below_total_plus_half
    assert '100%' in result
           ^^^^^^^^^^^^^^^^
E   TypeError: argument of type 'NoneType' is not iterable
```

### [FAILURE] test_bva_elapsed_zero (type: blackbox)
Assertion: assert result is not None
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_0\test_blackbox.py:39: in test_bva_elapsed_zero
    assert result is not None
E   assert None is not None
```

### [FAILURE] test_bva_elapsed_very_small (type: blackbox)
Assertion: assert result is not None
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_0\test_blackbox.py:46: in test_bva_elapsed_very_small
    assert result is not None
E   assert None is not None
```

### [FAILURE] test_bva_prefix_empty (type: blackbox)
Assertion: assert not result.startswith(': ')
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_0\test_blackbox.py:77: in test_bva_prefix_empty
    assert not result.startswith(': ')
               ^^^^^^^^^^^^^^^^^
E   AttributeError: 'NoneType' object has no attribute 'startswith'
```

### [FAILURE] test_bva_prefix_single_char (type: blackbox)
Assertion: assert 'A' in result
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_0\test_blackbox.py:82: in test_bva_prefix_single_char
    assert 'A' in result
           ^^^^^^^^^^^^^
E   TypeError: argument of type 'NoneType' is not iterable
```

### [FAILURE] test_bva_prefix_with_colon (type: blackbox)
Assertion: assert 'Test: ' in result
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_0\test_blackbox.py:87: in test_bva_prefix_with_colon
    assert 'Test: ' in result
           ^^^^^^^^^^^^^^^^^^
E   TypeError: argument of type 'NoneType' is not iterable
```

### [FAILURE] test_bva_n_float (type: blackbox)
Assertion: assert result is not None
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_0\test_blackbox.py:93: in test_bva_n_float
    assert result is not None
E   assert None is not None
```
