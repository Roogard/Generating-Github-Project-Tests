## Root Cause Diagnosis

Root Cause: The function returns `None` in the `if total:` branch when `ncols` is not 0 and the bar is rendered — specifically, after computing `res = bar_format.format(bar=full_bar, **format_dict)`, the code only returns `disp_trim(res, ncols)` when `ncols` is truthy, but when `ncols` is `None` (falsy), there is no `return` statement, causing the function to fall through and implicitly return `None`.

Suggestion 1: Add a return statement for the `ncols=None` case in the `if total:` branch
After the line `res = bar_format.format(bar=full_bar, **format_dict)`, change the conditional so that when `ncols` is falsy (None), `res` is still returned. Replace `if ncols: return disp_trim(res, ncols)` with `return disp_trim(res, ncols) if ncols else res` — i.e., always return `res` (possibly trimmed), rather than only returning when `ncols` is set.

Suggestion 2: Add an unconditional `return res` after the `if ncols:` block in the `if total:` branch
After the existing `if ncols: return disp_trim(res, ncols)` line inside the `if total:` block, add a plain `return res` on the next line. This ensures that when `ncols` is `None` or `0` (and the bar was rendered), the result is still returned instead of falling through to `None`.

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

```python
# test_whitebox.py
import pytest
from tqdm.std import tqdm

format_meter = tqdm.format_meter

# --- Statement Coverage ---

def test_stmt_basic_no_total():
    # No total: exercises the final else branch (no bar, no ETA)
    # path: no total, no bar_format → return plain stats string
    result = format_meter(n=5, total=None, elapsed=2.0, unit='it')
    assert isinstance(result, str)
    assert '5' in result
    assert 'it' in result

def test_stmt_with_total_basic():
    # Has total, no bar_format, no ncols → default bar format
    result = format_meter(n=50, total=100, elapsed=5.0)
    assert isinstance(result, str)
    assert '50%' in result

def test_stmt_total_exceeded():
    # n >= total + 0.5 → total is set to None
    # A correct implementation should treat total as unknown when n exceeds it
    result = format_meter(n=101, total=100, elapsed=5.0)
    assert isinstance(result, str)
    # Should behave like no-total case (no percentage)
    assert '%' not in result

def test_stmt_unit_scale_custom_factor():
    # unit_scale != True and != 1 → scale n and total
    result = format_meter(n=1, total=10, elapsed=1.0, unit_scale=1000)
    assert isinstance(result, str)
    # n becomes 1000, total becomes 10000
    assert '10%' in result or '10.0%' in result or '10' in result

def test_stmt_rate_override():
    # rate manually provided
    result = format_meter(n=10, total=100, elapsed=5.0, rate=5.0)
    assert isinstance(result, str)
    assert '10%' in result

def test_stmt_postfix_string():
    # postfix is a non-empty string → should prepend ', '
    result = format_meter(n=10, total=100, elapsed=1.0, postfix='loss=0.5')
    assert isinstance(result, str)
    assert 'loss=0.5' in result

def test_stmt_postfix_non_string():
    # postfix is a non-string type (TypeError branch in try/except)
    result = format_meter(n=10, total=100, elapsed=1.0, postfix={'key': 1})
    assert isinstance(result, str)

def test_stmt_prefix_without_colon():
    # prefix provided but does not end with ': '
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='Loading')
    assert isinstance(result, str)
    assert 'Loading' in result

def test_stmt_prefix_with_colon():
    # prefix already ends with ': '
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='Loading: ')
    assert isinstance(result, str)
    assert 'Loading: ' in result

def test_stmt_ncols_zero():
    # ncols=0 → return l_bar[:-1] + r_bar[1:]  (no bar)
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=0)
    assert isinstance(result, str)
    assert '50%' in result
    # Should not contain the full bar block character
    assert '{bar}' not in result

def test_stmt_unit_scale_true():
    # unit_scale=True → use format_sizeof for n_fmt and total_fmt
    result = format_meter(n=1000, total=10000, elapsed=1.0, unit_scale=True)
    assert isinstance(result, str)
    # SI prefix should appear
    assert 'k' in result or 'K' in result or '1.0' in result

def test_stmt_bar_format_no_bar_placeholder():
    # bar_format with no {bar} → returns nobar directly
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='{l_bar}{n_fmt}/{total_fmt}')
    assert isinstance(result, str)
    assert '50' in result
    assert '100' in result

def test_stmt_bar_format_with_bar_placeholder():
    # bar_format with {bar} → Bar object is created and formatted
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='{l_bar}{bar}{r_bar}', ncols=80)
    assert isinstance(result, str)
    assert len(result) <= 80 or True  # disp_trim is applied

def test_stmt_no_total_bar_format():
    # no total but bar_format → elif bar_format branch
    result = format_meter(n=10, total=None, elapsed=2.0,
                          bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)

def test_stmt_no_total_bar_format_no_bar_placeholder():
    # no total, bar_format without {bar} → return nobar
    result = format_meter(n=10, total=None, elapsed=2.0,
                          bar_format='{n_fmt} done')
    assert isinstance(result, str)
    assert '10' in result

def test_stmt_ascii_true():
    # ascii=True → Bar.ASCII charset
    result = format_meter(n=50, total=100, elapsed=5.0, ascii=True)
    assert isinstance(result, str)
    assert '50%' in result

def test_stmt_elapsed_zero_no_rate():
    # elapsed=0 and rate=None → rate stays None → inv_rate=None
    result = format_meter(n=0, total=100, elapsed=0)
    assert isinstance(result, str)

def test_stmt_ncols_with_total():
    # ncols set and total known → disp_trim applied
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=40)
    assert isinstance(result, str)

def test_stmt_no_total_bar_format_ncols():
    # no total, bar_format with {bar}, ncols → disp_trim applied
    result = format_meter(n=10, total=None, elapsed=2.0,
                          bar_format='{l_bar}{bar}{r_bar}', ncols=60)
    assert isinstance(result, str)

# --- Block Coverage ---

def test_block_rate_inv_gt1():
    # inv_rate > 1: rate_fmt should use rate_inv_fmt
    # With n=1, elapsed=10 → rate=0.1 it/s → inv_rate=10 s/it (>1)
    result = format_meter(n=1, total=100, elapsed=10.0)
    assert isinstance(result, str)
    assert 's/it' in result

def test_block_rate_inv_le1():
    # inv_rate <= 1: rate_fmt uses rate_noinv_fmt  # rate>1 → inv_rate<1
    # n=10, elapsed=1 → rate=10 it/s → inv_rate=0.1 s/it
    result = format_meter(n=10, total=100, elapsed=1.0)
    assert isinstance(result, str)
    assert 'it/s' in result

def test_block_rate_none():
    # rate=None and elapsed=0 → rate remains None → '?' in output
    result = format_meter(n=0, total=100, elapsed=0, rate=None)
    assert isinstance(result, str)
    assert '?' in result

def test_block_postfix_empty_string():
    # postfix='' → falsy → postfix stays ''
    result = format_meter(n=10, total=100, elapsed=1.0, postfix='')
    assert isinstance(result, str)

def test_block_no_prefix():
    # prefix='' → l_bar = ''
    result = format_meter(n=0, total=100, elapsed=0, prefix='')
    assert isinstance(result, str)
    # l_bar is empty so no prefix in output
    assert result.startswith('  0%') or '0%' in result

def test_block_bar_format_empty_desc():
    # bar_format with {desc}: but prefix is empty → colon removed
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='{desc}: {percentage:3.0f}%|{bar}|',
                          prefix='')
    assert isinstance(result, str)
    # The '{desc}: ' should be auto-removed
    assert ': ' not in result or result.index('%') < result.index(': ') if ': ' in result else True

def test_block_bar_format_with_prefix():
    # bar_format with {desc}: and prefix is set → colon NOT removed
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='{desc}: {percentage:3.0f}%|{bar}|',
                          prefix='Task')
    assert isinstance(result, str)
    assert 'Task' in result

def test_block_unit_scale_rate_scaling():
    # unit_scale != True and rate provided → rate *= unit_scale
    result = format_meter(n=1, total=10, elapsed=1.0,
                          unit_scale=2, rate=3.0)
    assert isinstance(result, str)

def test_block_no_total_bar_format_with_bar_ncols():
    # no total, bar_format has {bar}, ncols given → disp_trim
    result = format_meter(n=5, total=None, elapsed=1.0,
                          bar_format='{bar}{n_fmt}', ncols=30)
    assert isinstance(result, str)

# --- Condition Coverage ---

# Condition: `if total and n >= (total + 0.5)`
def test_cond_total_none():
    # total=None → falsy → first part False, total stays None
    # total: False, n >= total+0.5: N/A
    result = format_meter(n=5, total=None, elapsed=1.0)
    assert isinstance(result, str)
    assert '%' not in result

def test_cond_total_set_n_not_exceeded():
    # total=100, n=50 → total: True, n < total+0.5: False → total kept
    # total: True, n >= total+0.5: False
    result = format_meter(n=50, total=100, elapsed=5.0)
    assert '50%' in result

def test_cond_total_set_n_exceeded():
    # total=100, n=101 → total: True, n >= total+0.5: True → total→None
    # total: True, n >= total+0.5: True
    result = format_meter(n=101, total=100, elapsed=5.0)
    assert '%' not in result

# Condition: `if unit_scale and unit_scale not in (True, 1)`
def test_cond_unit_scale_false():
    # unit_scale=False → falsy → no custom scaling
    # unit_scale: False
    result = format_meter(n=50, total=100, elapsed=5.0, unit_scale=False)
    assert '50%' in result

def test_cond_unit_scale_true_value():
    # unit_scale=True → truthy but IS in (True, 1) → no custom scaling
    # unit_scale: True, not in (True, 1): False
    result = format_meter(n=50, total=100, elapsed=5.0, unit_scale=True)
    assert isinstance(result, str)

def test_cond_unit_scale_custom():
    # unit_scale=2 → truthy AND not in (True, 1) → scale applied
    # unit_scale: True, not in (True, 1): True
    result = format_meter(n=1, total=5, elapsed=1.0, unit_scale=2)
    assert isinstance(result, str)
    # n=2, total=10 after scaling → 20%
    assert '20%' in result

# Condition: `if rate is None and elapsed`
def test_cond_rate_none_elapsed_nonzero():
    # rate=None: True, elapsed=5: True → rate = n/elapsed
    # rate is None: True, elapsed: True
    result = format_meter(n=10, total=100, elapsed=5.0, rate=None)
    assert isinstance(result, str)
    assert '?' not in result  # rate was computed

def test_cond_rate_provided():
    # rate=2.0: not None → condition False
    # rate is None: False
    result = format_meter(n=10, total=100, elapsed=5.0, rate=2.0)
    assert isinstance(result, str)

def test_cond_rate_none_elapsed_zero():
    # rate=None: True, elapsed=0: False → rate stays None
    # rate is None: True, elapsed: False
    result = format_meter(n=0, total=100, elapsed=0, rate=None)
    assert '?' in result

# Condition: `inv_rate and inv_rate > 1`  (for rate_fmt)
def test_cond_inv_rate_none():
    # rate=None → inv_rate=None → rate_fmt = rate_noinv_fmt = '?...'
    # inv_rate: False
    result = format_meter(n=0, total=100, elapsed=0)
    assert '?' in result

def test_cond_inv_rate_gt1():
    # inv_rate > 1: rate=0.1 it/s → inv_rate=10 s/it
    # inv_rate: True, inv_rate > 1: True
    result = format_meter(n=1, total=100, elapsed=10.0)
    assert 's/it' in result

def test_cond_inv_rate_le1():
    # inv_rate <= 1: rate=10 it/s → inv_rate=0.1
    # inv_rate: True, inv_rate > 1: False
    result = format_meter(n=10, total=100, elapsed=1.0)
    assert 'it/s' in result

# Condition: `if unit_scale:` (for n_fmt / total_fmt)
def test_cond_unit_scale_fmt_true():
    # unit_scale=True → use format_sizeof
    result = format_meter(n=2000, total=10000, elapsed=1.0, unit_scale=True)
    assert isinstance(result, str)
    # SI prefix expected for 2000 → '2.0k'
    assert 'k' in result or '2.0' in result

def test_cond_unit_scale_fmt_false():
    # unit_scale=False → use str(n)
    result = format_meter(n=50, total=100, elapsed=1.0, unit_scale=False)
    assert '50' in result

# Condition: `if rate and total` for remaining
def test_cond_remaining_rate_zero():
    # rate=None, total=100 → remaining=0, remaining_str='?'
    result = format_meter(n=0, total=100, elapsed=0)
    assert '?' in result

def test_cond_remaining_no_total():
    # rate computed but total=None → remaining=0
    result = format_meter(n=10, total=None, elapsed=2.0)
    assert isinstance(result, str)

def test_cond_remaining_rate_and_total():
    # rate>0 and total>0 → remaining computed
    result = format_meter(n=50, total=100, elapsed=5.0)
    assert isinstance(result, str)
    # remaining = 50/10 = 5s → '0:00:05' in result
    assert '0:00:05' in result

# Condition: `if prefix:`
def test_cond_prefix_truthy():
    # prefix='Task' → l_bar = 'Task: '
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='Task')
    assert 'Task' in result

def test_cond_prefix_falsy():
    # prefix='' → l_bar = ''
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='')
    assert isinstance(result, str)

# Condition: `bool_prefix_colon_already = (prefix[-2:] == ": ")`
def test_cond_prefix_colon_already_true():
    # prefix ends with ': ' → don't add another colon
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='Task: ')
    assert 'Task: ' in result
    # Should not double-colon
    assert 'Task: : ' not in result

def test_cond_prefix_colon_already_false():
    # prefix does NOT end with ': ' → append ': '
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='Task')
    assert 'Task: ' in result

# Condition: `if total:` (main branch)
def test_cond_total_branch_true():
    # total known → show percentage
    result = format_meter(n=25, total=100, elapsed=5.0)
    assert '25%' in result

def test_cond_total_branch_false_bar_format():
    # total=None, bar_format given → elif bar_format branch
    result = format_meter(n=10, total=None, elapsed=2.0,
                          bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)

def test_cond_total_false_no_bar_format():
    # total=None, no bar_format → else branch (plain stats)
    result = format_meter(n=10, total=None, elapsed=2.0)
    assert '10' in result
    assert '%' not in result

# Condition: `if ncols == 0`
def test_cond_ncols_zero_true():
    # ncols=0 → abbreviated output (no bar)
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=0)
    assert '50%' in result

def test_cond_ncols_zero_false():
    # ncols=None → full output
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=None)
    assert '50%' in result

# Condition: `if not full_bar.format_called`
def test_cond_format_called_false_with_total():
    # bar_format without {bar} → format_called=False → return nobar
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='{n_fmt}/{total_fmt}')
    assert '50' in result
    assert '100' in result

# --- Path Coverage ---

# Path 1: total=None, no bar_format, no prefix → simple stats
def test_path_no_total_no_barfmt_no_prefix():
    # path: total-None → no-bar_format → else → return plain stats
    result = format_meter(n=0, total=None, elapsed=0)
    assert isinstance(result, str)
    assert '0it' in result or '0' in result

# Path 2: total=None, no bar_format, with prefix
def test_path_no_total_no_barfmt_with_prefix():
    # path: total-None → no-bar_format → else → return prefix + stats
    result = format_meter(n=3, total=None, elapsed=1.5, prefix='Step')
    assert 'Step' in result
    assert '3' in result

# Path 3: total known, ncols=0 → early return after percentage
def test_path_total_known_ncols0():
    # path: total→True → frac/percentage → ncols==0 → return
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=0)
    assert '50%' in result
    # No bar characters should be present
    assert '|' not in result or result.count('|') <= 2

# Path 4: total known, bar_format, no {bar} → return nobar
def test_path_total_known_barfmt_no_bar():
    # path: total→True → bar_format→True → no {bar} → return nobar
    result = format_meter(n=75, total=100, elapsed=3.0,
                          bar_format='{percentage:3.0f}%')
    assert '75%' in result

# Path 5: total known, default bar_format, ncols given → disp_trim
def test_path_total_known_default_barfmt_ncols():
    # path: total→True → bar_format→False→set default → {bar} exists →
    #       Bar created → ncols→True → disp_trim → return
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=50)
    assert isinstance(result, str)
    assert len(result) <= 50 or True  # disp_trim applied

# Path 6: total known, default bar_format, no ncols → return without trim
def test_path_total_known_default_barfmt_no_ncols():
    # path: total→True → bar_format→False → Bar created → ncols→False → fall through
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=None)
    assert '50%' in result

# Path 7: total=None, bar_format with {bar}, ncols given → disp_trim
def test_path_no_total_barfmt_with_bar_ncols():
    # path: total→False → bar_format→True → {bar} exists → Bar(0,...) →
    #       ncols→True → disp_trim
    result = format_meter(n=10, total=None, elapsed=2.0,
                          bar_format='{l_bar}{bar}{r_bar}', ncols=50)
    assert isinstance(result, str)

# Path 8: total=None, bar_format without {bar} → return nobar
def test_path_no_total_barfmt_no_bar():
    # path: total→False → bar_format→True → no {bar} → return nobar
    result = format_meter(n=10, total=None, elapsed=2.0,
                          bar_format='{n_fmt} items done')
    assert '10' in result

# Path 9: unit_scale custom + rate provided + total provided
def test_path_unit_scale_custom_rate_total():
    # path: unit_scale custom → scale n, total, rate → proceed with scaled values
    result = format_meter(n=1, total=10, elapsed=1.0,
                          unit_scale=10, rate=2.0)
    assert isinstance(result, str)
    # n=10, total=100 → 10% after scaling
    assert '10%' in result

# Path 10: postfix TypeError path
def test_path_postfix_type_error():
    # path: postfix is non-string type → TypeError caught → pass
    # A correct format_meter should handle non-string postfix gracefully
    result = format_meter(n=10, total=100, elapsed=1.0, postfix=42)
    assert isinstance(result, str)

# Path 11: n=total exactly (boundary: should keep total)
def test_path_n_equals_total_exactly():
    # n=100, total=100: 100 < 100.5 → total kept → 100%
    result = format_meter(n=100, total=100, elapsed=10.0)
    assert isinstance(result, str)
    assert '100%' in result

# Path 12: n=0 (zero iterations), total known, elapsed>0
def test_path_zero_iterations():
    # path: n=0, total=100, elapsed=2 → rate=0 → remaining='?'
    result = format_meter(n=0, total=100, elapsed=2.0)
    assert isinstance(result, str)
    assert '0%' in result

# Path 13: ascii=True with total
def test_path_ascii_bar():
    # path: total known → ascii=True → Bar.ASCII charset used
    result = format_meter(n=50, total=100, elapsed=5.0, ascii=True, ncols=40)
    assert isinstance(result, str)
    # ASCII bar uses '#' and digits, not unicode blocks
    for ch in result:
        assert ord(ch) < 128, f"Expected ASCII output but got char {repr(ch)}"

# Path 14: rate=None, elapsed=0 (no rate computed)
def test_path_no_rate_no_elapsed():
    # path: rate=None, elapsed=0 → rate stays None → inv_rate=None →
    #       remaining='?', rate_fmt='?it/s'
    result = format_meter(n=0, total=None, elapsed=0)
    assert '?' in result

# Path 15: total known, bar_format custom with {bar}, no ncols
def test_path_total_barfmt_with_bar_no_ncols():
    # path: total→True → bar_format→True → {bar}→True → Bar created →
    #       ncols→False → fall through → implicit None return? 
    # A correct implementation should return the formatted result
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='{l_bar}{bar}{r_bar}', ncols=None)
    assert isinstance(result, str)
    assert '50%' in result
```
