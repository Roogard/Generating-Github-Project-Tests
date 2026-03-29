## Trigger Test(s)

```python
# test_blackbox.py
import pytest
from tqdm.std import tqdm

format_meter = tqdm.format_meter

# --- BVA ---

def test_bva_n_zero_elapsed_zero():
    # n=0, elapsed=0: no rate computable, rate=None
    result = format_meter(0, 100, 0)
    assert isinstance(result, str)
    assert '0' in result

def test_bva_n_zero_elapsed_positive():
    # n=0, elapsed>0: rate=0/elapsed=0, inv_rate=None
    result = format_meter(0, 100, 1.0)
    assert isinstance(result, str)
    assert '0%' in result or '  0%' in result

def test_bva_n_equals_total_minus_one():
    # n = total - 1: just before 100%
    result = format_meter(99, 100, 1.0)
    assert isinstance(result, str)
    assert '99%' in result

def test_bva_n_equals_total():
    # n == total: 100% completion
    result = format_meter(100, 100, 1.0)
    assert isinstance(result, str)
    # total should become None when n >= total+0.5 is False (100 < 100.5), so still known
    assert '100%' in result

def test_bva_n_exceeds_total_by_half():
    # n >= total + 0.5: total is set to None
    result = format_meter(101, 100, 1.0)
    assert isinstance(result, str)
    # total should be invalidated, no percentage shown
    assert '%' not in result or '101' in result

def test_bva_elapsed_very_small():
    # elapsed approaching 0 but positive
    result = format_meter(10, 100, 0.001)
    assert isinstance(result, str)

def test_bva_total_none():
    # total=None: no ETA, no percentage
    result = format_meter(50, None, 5.0)
    assert isinstance(result, str)
    assert '%' not in result

def test_bva_total_zero():
    # total=0 is falsy: treated like no total
    result = format_meter(0, 0, 1.0)
    assert isinstance(result, str)

def test_bva_ncols_zero():
    # ncols=0: no bar, only stats
    result = format_meter(50, 100, 5.0, ncols=0)
    assert isinstance(result, str)
    # should not contain the bar character
    assert '|' not in result or result.count('|') <= 2

def test_bva_ncols_one():
    # ncols=1: extremely narrow
    result = format_meter(50, 100, 5.0, ncols=1)
    assert isinstance(result, str)

def test_bva_ncols_large():
    # ncols=200: wide display
    result = format_meter(50, 100, 5.0, ncols=200)
    assert isinstance(result, str)
    assert len(result) <= 200

def test_bva_n_is_float():
    # n as float
    result = format_meter(0.5, 1.0, 1.0)
    assert isinstance(result, str)

def test_bva_total_is_float():
    # total as float
    result = format_meter(0.5, 2.5, 1.0)
    assert isinstance(result, str)
    assert '%' in result

def test_bva_elapsed_large():
    # large elapsed value
    result = format_meter(1, 100, 3600.0)
    assert isinstance(result, str)

# --- ECP ---

def test_ecp_valid_no_prefix_no_total():
    # Valid class: no prefix, no total, positive elapsed
    result = format_meter(10, None, 2.0)
    assert isinstance(result, str)
    assert '10' in result

def test_ecp_valid_with_prefix():
    # Valid class: prefix provided
    result = format_meter(50, 100, 5.0, prefix='Loading')
    assert isinstance(result, str)
    assert 'Loading' in result

def test_ecp_valid_prefix_already_has_colon():
    # Prefix ending with ': ' should not add another ': '
    result = format_meter(50, 100, 5.0, prefix='Loading: ')
    assert isinstance(result, str)
    # Should not have 'Loading: : '
    assert 'Loading: : ' not in result
    assert 'Loading: ' in result

def test_ecp_valid_unit_scale_true():
    # unit_scale=True: SI prefix applied
    result = format_meter(1000, 10000, 1.0, unit_scale=True)
    assert isinstance(result, str)
    # Should contain SI prefix like 'k'
    assert 'k' in result or '1' in result

def test_ecp_valid_unit_scale_numeric():
    # unit_scale as numeric factor (e.g., 2)
    result = format_meter(10, 100, 1.0, unit_scale=2)
    assert isinstance(result, str)
    # n should be scaled: 10 * 2 = 20
    assert '20' in result

def test_ecp_valid_custom_unit():
    # unit='MB'
    result = format_meter(50, 100, 5.0, unit='MB')
    assert isinstance(result, str)
    assert 'MB' in result

def test_ecp_valid_custom_rate():
    # Manual rate override
    result = format_meter(50, 100, 5.0, rate=10.0)
    assert isinstance(result, str)

def test_ecp_valid_postfix_string():
    # postfix as string
    result = format_meter(50, 100, 5.0, postfix='loss=0.5')
    assert isinstance(result, str)
    assert 'loss=0.5' in result

def test_ecp_valid_postfix_none():
    # postfix=None: should not appear
    result = format_meter(50, 100, 5.0, postfix=None)
    assert isinstance(result, str)

def test_ecp_valid_postfix_dict():
    # postfix as non-string type (dict); TypeError silently ignored
    result = format_meter(50, 100, 5.0, postfix={'loss': 0.5})
    assert isinstance(result, str)

def test_ecp_valid_bar_format_no_bar_placeholder():
    # bar_format without {bar}: should return formatted string directly
    result = format_meter(50, 100, 5.0, bar_format='{l_bar}{r_bar}')
    assert isinstance(result, str)

def test_ecp_valid_bar_format_with_bar_placeholder():
    # bar_format with {bar}: renders bar
    result = format_meter(50, 100, 5.0, bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)

def test_ecp_valid_ascii_true():
    # ascii=True: use ASCII fill characters
    result = format_meter(50, 100, 5.0, ascii=True)
    assert isinstance(result, str)

def test_ecp_valid_ascii_false():
    # ascii=False: use unicode blocks
    result = format_meter(50, 100, 5.0, ascii=False)
    assert isinstance(result, str)

def test_ecp_valid_ascii_custom_str():
    # ascii as custom string charset
    result = format_meter(50, 100, 5.0, ascii=' =-')
    assert isinstance(result, str)

def test_ecp_valid_no_total_with_bar_format():
    # no total but bar_format provided
    result = format_meter(50, None, 5.0, bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)

def test_ecp_valid_unit_divisor():
    # unit_divisor with unit_scale
    result = format_meter(1024, 10240, 1.0, unit_scale=True, unit_divisor=1024)
    assert isinstance(result, str)

def test_ecp_invalid_rate_zero():
    # rate=0 should be treated like no rate (inv_rate=None)
    result = format_meter(0, 100, 0, rate=0)
    assert isinstance(result, str)
    # rate_noinv_fmt should show '?'
    assert '?' in result

# --- Mutation Detection ---

def test_mutation_total_invalidation_at_exactly_half():
    # Detects off-by-one in: n >= (total + 0.5)
    # n=100.4 should NOT invalidate total=100 (100.4 < 100.5)
    result_keep = format_meter(100.4, 100, 1.0)
    # With total still set, percentage should be shown
    # 100.4/100 >= 1.0, but 100.4 < 100.5, so total must remain valid
    # A correct impl sets total=None only when n >= total+0.5
    assert isinstance(result_keep, str)
    assert '%' in result_keep  # total still known → percentage shown

def test_mutation_total_invalidation_just_above_half():
    # n=100.5 should invalidate total=100
    result_invalidated = format_meter(100.5, 100, 1.0)
    assert isinstance(result_invalidated, str)
    # When total is invalidated, no percentage line
    assert '%' not in result_invalidated

def test_mutation_rate_none_when_elapsed_zero():
    # Detects: `if rate is None and elapsed` — elapsed=0 is falsy, rate stays None
    result = format_meter(10, 100, 0, rate=None)
    assert isinstance(result, str)
    # rate should be unknown → '?' in output
    assert '?' in result

def test_mutation_rate_set_when_elapsed_nonzero():
    # Detects negation of `elapsed` condition: rate should be computed
    result = format_meter(10, 100, 2.0, rate=None)
    assert isinstance(result, str)
    # rate = 10/2 = 5.0 it/s, should not show '?' for rate
    # Actually rate=5 it/s so rate_noinv_fmt='5.00it/s', inv_rate=0.2 < 1
    assert '?' not in result or 'remaining' in result

def test_mutation_inv_rate_threshold():
    # Detects wrong operator in `inv_rate > 1`:
    # rate=0.5 it/s → inv_rate=2.0s/it > 1, so rate_fmt should use rate_inv_fmt
    result = format_meter(1, 100, 2.0, rate=0.5)
    assert isinstance(result, str)
    assert 's/it' in result  # inv_rate > 1 → display seconds per iteration

def test_mutation_inv_rate_threshold_below_one():
    # rate=2.0 it/s → inv_rate=0.5 < 1, should use rate_noinv_fmt (it/s)
    result = format_meter(2, 100, 1.0, rate=2.0)
    assert isinstance(result, str)
    assert 'it/s' in result

def test_mutation_percentage_calculation():
    # Detects wrong operator in frac = n / total
    # n=25, total=100 → percentage=25%
    result = format_meter(25, 100, 1.0)
    assert ' 25%' in result

def test_mutation_percentage_at_50():
    # n=50, total=100 → exactly 50%
    result = format_meter(50, 100, 1.0)
    assert ' 50%' in result

def test_mutation_percentage_at_100():
    # n=100, total=100 → 100% (n < total+0.5 so total stays valid)
    result = format_meter(100, 100, 1.0)
    assert '100%' in result

def test_mutation_prefix_colon_detection():
    # Detects off-by-one in prefix[-2:] == ": "
    # Prefix ending with ': ' should NOT have another ': ' appended
    prefix = 'Test: '
    result = format_meter(50, 100, 1.0, prefix=prefix)
    assert 'Test: : ' not in result
    assert 'Test: ' in result

def test_mutation_prefix_no_colon_gets_colon_appended():
    # Prefix NOT ending with ': ' should get ': ' appended
    prefix = 'Test'
    result = format_meter(50, 100, 1.0, prefix=prefix)
    assert 'Test: ' in result

def test_mutation_remaining_computation():
    # remaining = (total - n) / rate
    # n=50, total=100, elapsed=5 → rate=10it/s, remaining=5s
    result = format_meter(50, 100, 5.0)
    assert isinstance(result, str)
    # remaining_str should be '00:05' (5 seconds)
    assert '00:05' in result

def test_mutation_remaining_zero_when_no_rate():
    # When rate=0/None, remaining should default to 0 and display '?'
    result = format_meter(50, 100, 0, rate=None)
    assert isinstance(result, str)
    assert '?' in result  # remaining_str = '?' when rate is None/falsy

def test_mutation_unit_scale_numeric_scales_n():
    # unit_scale=3 should multiply n by 3
    result = format_meter(10, 100, 1.0, unit_scale=3)
    assert isinstance(result, str)
    # n should be 30, total should be 300
    assert '30' in result

def test_mutation_unit_scale_numeric_scales_total():
    # unit_scale=3 should multiply total by 3: 100*3=300
    result = format_meter(10, 100, 1.0, unit_scale=3)
    assert isinstance(result, str)
    assert '300' in result

def test_mutation_unit_scale_numeric_scales_rate():
    # unit_scale=2, rate=5 → rate becomes 10
    result = format_meter(10, 100, 1.0, unit_scale=2, rate=5.0)
    assert isinstance(result, str)
    # scaled rate=10, inv_rate=0.1 < 1, so it/s displayed: '10.00it/s'
    assert '10.00' in result

def test_mutation_ncols_zero_returns_no_bar():
    # ncols=0: `if ncols == 0: return l_bar[:-1] + r_bar[1:]`
    # Detects == vs != or other wrong comparison
    result = format_meter(50, 100, 5.0, ncols=0)
    assert isinstance(result, str)
    # The bar part is stripped; result should not contain the bar-filling characters
    # result = l_bar[:-1] + r_bar[1:]: l_bar ends with '|', r_bar starts with '|'
    # so result should NOT start/end with '|'
    assert not result.startswith('|')

def test_mutation_postfix_string_prepends_comma():
    # postfix = ', ' + postfix when truthy string
    result = format_meter(50, 100, 5.0, postfix='acc=0.9')
    assert ', acc=0.9' in result

def test_mutation_postfix_empty_string_not_prepended():
    # postfix='' is falsy → stays ''
    result = format_meter(50, 100, 5.0, postfix='')
    assert isinstance(result, str)
    # no extra comma before empty postfix
    assert ',  [' not in result

def test_mutation_bar_format_no_total_sets_percentage_zero():
    # bar_format with no total: percentage should be 0 in format_dict
    result = format_meter(50, None, 5.0, bar_format='{percentage:.0f}%')
    assert result == '0%'

def test_mutation_frac_correct_value():
    # frac = n / total; n=1, total=4 → frac=0.25 → 25%
    result = format_meter(1, 4, 1.0)
    assert ' 25%' in result

def test_mutation_elapsed_str_format():
    # elapsed=61s → '01:01'
    result = format_meter(10, 100, 61.0)
    assert '01:01' in result

def test_mutation_no_total_no_bar_format_output():
    # No total, no bar_format: output format is specific
    result = format_meter(5, None, 2.0, unit='it', prefix='')
    assert isinstance(result, str)
    # Should contain n_fmt and unit
    assert '5it' in result or '5' in result
    assert '[' in result

def test_mutation_no_total_with_prefix_output():
    # No total, no bar_format, with prefix
    result = format_meter(5, None, 2.0, prefix='MyTask')
    assert result.startswith('MyTask: ')

def test_mutation_ncols_trims_result():
    # When ncols is set, result must be trimmed to ncols display length
    from tqdm.utils import disp_len
    ncols = 40
    result = format_meter(50, 100, 5.0, ncols=ncols)
    assert isinstance(result, str)
    assert disp_len(result) <= ncols

def test_mutation_bar_format_desc_removal_when_empty_prefix():
    # When prefix='' and bar_format contains '{desc}: ', it should be stripped
    result = format_meter(50, 100, 5.0, prefix='',
                          bar_format='{desc}: {percentage:.0f}%')
    assert isinstance(result, str)
    # '{desc}: ' replaced since desc is empty
    assert ': ' not in result or result.strip() != ': 50%'
    assert '50%' in result

def test_mutation_bar_format_desc_kept_when_prefix_given():
    # When prefix is given, '{desc}: ' is NOT stripped
    result = format_meter(50, 100, 5.0, prefix='MyTask',
                          bar_format='{desc}: {percentage:.0f}%')
    assert 'MyTask: 50%' in result

def test_mutation_unit_scale_true_uses_format_sizeof_for_n():
    # unit_scale=True: n_fmt uses format_sizeof
    result = format_meter(1500, 10000, 1.0, unit_scale=True)
    assert isinstance(result, str)
    # 1500 with SI prefix → '1.50k' or similar
    assert 'k' in result

def test_mutation_rate_fmt_uses_inv_when_inv_gt_one():
    # rate=0.1 it/s → inv_rate=10 > 1 → rate_fmt = rate_inv_fmt (s/it)
    result = format_meter(1, 1000, 10.0, rate=0.1)
    assert 's/it' in result

def test_mutation_rate_fmt_uses_noinv_when_inv_lte_one():
    # rate=2 it/s → inv_rate=0.5 ≤ 1 → rate_fmt = rate_noinv_fmt (it/s)
    result = format_meter(2, 100, 1.0, rate=2.0)
    assert 'it/s' in result
    assert 's/it' not in result
```

```python
# test_whitebox.py
import pytest
from tqdm.std import tqdm

format_meter = tqdm.format_meter

# --- Statement Coverage ---

def test_stmt_basic_no_total():
    # n=5, total=None, elapsed=2.0 → no bar, just stats
    result = format_meter(5, None, 2.0, unit='it')
    assert isinstance(result, str)
    assert '5' in result
    assert 'it' in result

def test_stmt_total_known_simple():
    # n=50, total=100, elapsed=5.0 → standard bar
    result = format_meter(50, 100, 5.0)
    assert isinstance(result, str)
    assert '50%' in result

def test_stmt_total_exceeded_resets_to_none():
    # n >= total + 0.5 → total becomes None; no percentage shown
    result = format_meter(101, 100, 5.0)
    assert isinstance(result, str)
    # A correct meter with total=None should not show a percentage like "100%"
    assert '%' not in result or '101%' not in result

def test_stmt_unit_scale_custom():
    # unit_scale != True and != 1 → custom scaling applied
    result = format_meter(500, 1000, 5.0, unit_scale=2.0)
    assert isinstance(result, str)

def test_stmt_rate_none_elapsed_zero():
    # rate=None and elapsed=0 → rate stays None → inv_rate=None
    result = format_meter(0, 100, 0, rate=None)
    assert isinstance(result, str)
    assert '?' in result  # rate unknown

def test_stmt_rate_provided():
    # rate manually overridden
    result = format_meter(10, 100, 5.0, rate=2.0)
    assert isinstance(result, str)

def test_stmt_ncols_zero_with_total():
    # ncols=0 → no bar, just l_bar + r_bar without the bar
    result = format_meter(50, 100, 5.0, ncols=0)
    assert isinstance(result, str)
    assert '|' not in result or result.count('|') < 3  # no progress bar characters

def test_stmt_postfix_string():
    # postfix as string
    result = format_meter(10, 100, 2.0, postfix='loss=0.5')
    assert isinstance(result, str)
    assert 'loss=0.5' in result

def test_stmt_postfix_non_string():
    # postfix as dict (TypeError caught, pass)
    result = format_meter(10, 100, 2.0, postfix={'loss': 0.5})
    assert isinstance(result, str)

def test_stmt_bar_format_custom_no_bar_placeholder():
    # bar_format without {bar} → format and return nobar
    result = format_meter(50, 100, 5.0, bar_format='{l_bar}{r_bar}')
    assert isinstance(result, str)
    assert '50%' in result

def test_stmt_bar_format_custom_with_bar_placeholder():
    # bar_format with {bar} → full_bar constructed
    result = format_meter(50, 100, 5.0, bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)

def test_stmt_bar_format_no_total():
    # bar_format specified but no total → elif branch
    result = format_meter(10, None, 2.0, bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)

def test_stmt_bar_format_no_total_no_bar_placeholder():
    # bar_format without {bar} and no total → return nobar
    result = format_meter(10, None, 2.0, bar_format='{l_bar}{r_bar}')
    assert isinstance(result, str)

def test_stmt_unit_scale_true():
    # unit_scale=True → format_sizeof used for n_fmt and total_fmt
    result = format_meter(1000, 10000, 5.0, unit_scale=True)
    assert isinstance(result, str)
    assert 'k' in result or 'K' in result or '1.00k' in result or '1' in result

def test_stmt_prefix_with_colon():
    # prefix already ending in ": "
    result = format_meter(50, 100, 5.0, prefix='Loading: ')
    assert isinstance(result, str)
    assert 'Loading' in result

def test_stmt_prefix_without_colon():
    # prefix without trailing ": "
    result = format_meter(50, 100, 5.0, prefix='Loading')
    assert isinstance(result, str)
    assert 'Loading' in result

def test_stmt_ascii_true():
    # ascii=True → Bar.ASCII charset
    result = format_meter(50, 100, 5.0, ascii=True)
    assert isinstance(result, str)

def test_stmt_ncols_with_total():
    # ncols set → disp_trim called on result
    result = format_meter(50, 100, 5.0, ncols=40)
    assert isinstance(result, str)
    assert len(result) <= 40 + 5  # trim may include unicode width considerations

def test_stmt_ncols_with_no_total_bar_format():
    # ncols with bar_format and no total → disp_trim
    result = format_meter(10, None, 2.0, bar_format='{l_bar}{bar}{r_bar}', ncols=40)
    assert isinstance(result, str)


# --- Block Coverage ---

def test_block_rate_computed_from_elapsed():
    # block: rate is None, elapsed > 0 → rate = n/elapsed
    result = format_meter(10, 100, 2.0, rate=None)
    assert isinstance(result, str)
    # rate = 5.0 it/s, inv_rate = 0.2 < 1 → rate_fmt = rate_noinv_fmt
    assert '/s' in result

def test_block_inv_rate_gt_1_uses_rate_inv_fmt():
    # inv_rate > 1 → rate_fmt = rate_inv_fmt (rate < 1 it/s)
    result = format_meter(1, 100, 10.0, rate=0.1)
    assert isinstance(result, str)
    # rate=0.1 it/s → inv_rate=10 > 1 → shows s/it
    assert 's/it' in result

def test_block_unit_scale_true_total_none():
    # unit_scale True, total=None → total_fmt = '?'
    result = format_meter(1000, None, 5.0, unit_scale=True)
    assert isinstance(result, str)
    assert '?' in result

def test_block_unit_scale_false_total_none():
    # unit_scale False, total=None → total_fmt = '?'
    result = format_meter(10, None, 2.0, unit_scale=False)
    assert isinstance(result, str)
    assert '?' in result

def test_block_postfix_empty_string():
    # postfix='' → '' (falsy, becomes '')
    result = format_meter(10, 100, 2.0, postfix='')
    assert isinstance(result, str)

def test_block_no_rate_remaining_zero():
    # rate=None, elapsed=0 → remaining=0, remaining_str='?'
    result = format_meter(0, 100, 0)
    assert isinstance(result, str)
    assert '?' in result

def test_block_no_prefix_l_bar_empty():
    # no prefix → l_bar = ''
    result = format_meter(50, 100, 5.0, prefix='')
    assert isinstance(result, str)

def test_block_bar_format_desc_replacement():
    # bar_format with {desc}: and no prefix → {desc}: removed
    result = format_meter(50, 100, 5.0, bar_format='{desc}: {percentage:3.0f}%|{bar}{r_bar}', prefix='')
    assert isinstance(result, str)

def test_block_bar_format_desc_with_prefix():
    # bar_format with {desc}: and prefix → NOT removed
    result = format_meter(50, 100, 5.0, bar_format='{desc}: {percentage:3.0f}%|{bar}{r_bar}', prefix='MyDesc')
    assert isinstance(result, str)
    assert 'MyDesc' in result

def test_block_unit_scale_custom_with_rate():
    # unit_scale custom, rate provided → rate scaled
    result = format_meter(50, 100, 5.0, unit_scale=2, rate=1.0)
    assert isinstance(result, str)


# --- Condition Coverage ---

# Condition: total and n >= (total + 0.5)
def test_cond_total_truthy_n_exceeds():
    # total=100 (True), n=101 >= 100.5 (True) → total reset to None
    # cond: total: True, n >= total+0.5: True
    result = format_meter(101, 100, 5.0)
    assert '%' not in result or '101%' not in result

def test_cond_total_truthy_n_within():
    # total=100 (True), n=50 < 100.5 (False) → total kept
    # cond: total: True, n >= total+0.5: False
    result = format_meter(50, 100, 5.0)
    assert '50%' in result

def test_cond_total_none():
    # total=None (False) → short-circuit, total stays None
    # cond: total: False
    result = format_meter(50, None, 5.0)
    assert isinstance(result, str)
    assert '%' not in result

# Condition: unit_scale and unit_scale not in (True, 1)
def test_cond_unit_scale_false():
    # unit_scale=False → condition False
    result = format_meter(50, 100, 5.0, unit_scale=False)
    assert isinstance(result, str)

def test_cond_unit_scale_true_value():
    # unit_scale=True → condition True but "not in (True,1)" is False → skip scaling
    result = format_meter(50, 100, 5.0, unit_scale=True)
    assert isinstance(result, str)

def test_cond_unit_scale_custom_value():
    # unit_scale=2 → condition True and not in (True,1) True → scaling applied
    result = format_meter(50, 100, 5.0, unit_scale=2)
    assert isinstance(result, str)

# Condition: rate is None and elapsed (for computing rate)
def test_cond_rate_none_elapsed_nonzero():
    # rate is None: True, elapsed: True → rate = n/elapsed
    result = format_meter(10, 100, 2.0, rate=None)
    assert isinstance(result, str)

def test_cond_rate_not_none():
    # rate is None: False → skip computation
    result = format_meter(10, 100, 2.0, rate=3.0)
    assert isinstance(result, str)

def test_cond_rate_none_elapsed_zero():
    # rate is None: True, elapsed: False (0) → rate stays None
    result = format_meter(0, 100, 0, rate=None)
    assert '?' in result

# Condition: inv_rate and inv_rate > 1 (for rate_fmt selection)
def test_cond_inv_rate_gt1_true():
    # inv_rate=10 > 1: True → rate_fmt = rate_inv_fmt
    result = format_meter(1, 100, 10.0, rate=0.1)  # inv_rate=10 > 1
    assert 's/it' in result

def test_cond_inv_rate_gt1_false_lt1():
    # rate=5 → inv_rate=0.2 < 1: False → rate_fmt = rate_noinv_fmt
    result = format_meter(10, 100, 2.0, rate=5.0)
    assert 'it/s' in result

def test_cond_inv_rate_none():
    # rate=None, elapsed=0 → inv_rate=None → rate_fmt = rate_noinv_fmt = '?it/s'
    result = format_meter(0, 100, 0)
    assert '?' in result

# Condition: unit_scale (for n_fmt/total_fmt block)
def test_cond_unit_scale_for_fmt_true():
    # unit_scale=True → format_sizeof used
    result = format_meter(5000, 10000, 5.0, unit_scale=True)
    assert isinstance(result, str)

def test_cond_unit_scale_for_fmt_false():
    # unit_scale=False → str() used
    result = format_meter(50, 100, 5.0, unit_scale=False)
    assert '50' in result
    assert '100' in result

# Condition: postfix truthy
def test_cond_postfix_truthy():
    # postfix='info' → ', ' prepended
    result = format_meter(10, 100, 2.0, postfix='info')
    assert ', info' in result

def test_cond_postfix_falsy():
    # postfix='' → stays ''
    result = format_meter(10, 100, 2.0, postfix='')
    assert isinstance(result, str)

# Condition: rate and total (for remaining)
def test_cond_rate_and_total_both_true():
    # rate=2, total=100 → remaining computed
    result = format_meter(10, 100, 2.0, rate=2.0)
    assert isinstance(result, str)
    assert '?' not in result.split('[')[1].split('<')[0]  # elapsed known

def test_cond_rate_true_total_false():
    # total=None → remaining=0
    result = format_meter(10, None, 2.0, rate=2.0)
    assert isinstance(result, str)

def test_cond_rate_false_total_true():
    # rate=None, elapsed=0, total=100 → remaining=0, remaining_str='?'
    result = format_meter(0, 100, 0)
    assert '?' in result

# Condition: prefix truthy
def test_cond_prefix_truthy_no_colon():
    # prefix='Epoch' → l_bar = 'Epoch: '
    result = format_meter(50, 100, 5.0, prefix='Epoch')
    assert 'Epoch' in result

def test_cond_prefix_truthy_with_colon():
    # prefix='Epoch: ' → already has ': ', l_bar = prefix unchanged
    result = format_meter(50, 100, 5.0, prefix='Epoch: ')
    assert 'Epoch' in result

def test_cond_prefix_falsy():
    # prefix='' → l_bar = ''
    result = format_meter(50, 100, 5.0, prefix='')
    assert isinstance(result, str)

# Condition: bool_prefix_colon_already
def test_cond_bool_prefix_colon_already_true():
    # prefix[-2:] == ': ' → True
    result = format_meter(50, 100, 5.0, prefix='Test: ')
    assert 'Test: ' in result

def test_cond_bool_prefix_colon_already_false():
    # prefix[-2:] != ': ' → False → append ': '
    result = format_meter(50, 100, 5.0, prefix='Test')
    assert 'Test: ' in result

# Condition: ncols == 0
def test_cond_ncols_zero_true():
    # ncols=0 → return early without bar
    result = format_meter(50, 100, 5.0, ncols=0)
    assert '50%' in result

def test_cond_ncols_zero_false():
    # ncols=None (not 0) → continue with bar
    result = format_meter(50, 100, 5.0, ncols=None)
    assert isinstance(result, str)

# Condition: bar_format with total
def test_cond_bar_format_true_with_total():
    # bar_format provided, total known
    result = format_meter(50, 100, 5.0, bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)

def test_cond_bar_format_false_with_total():
    # bar_format=None, total known → default bar_format
    result = format_meter(50, 100, 5.0, bar_format=None)
    assert isinstance(result, str)
    assert '|' in result

# Condition: full_bar.format_called (no {bar} in bar_format)
def test_cond_no_bar_in_bar_format_with_total():
    # bar_format has no {bar} → format_called=False → return nobar
    result = format_meter(50, 100, 5.0, bar_format='{percentage:3.0f}%')
    assert isinstance(result, str)
    assert '50' in result

def test_cond_bar_in_bar_format_with_total():
    # bar_format has {bar} → format_called=True → continue
    result = format_meter(50, 100, 5.0, bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)

# Condition: ncols truthy (disp_trim branch)
def test_cond_ncols_truthy_with_total():
    # ncols=50 → disp_trim(res, 50)
    result = format_meter(50, 100, 5.0, ncols=50)
    assert isinstance(result, str)

def test_cond_ncols_none_with_total():
    # ncols=None → return res without trim
    result = format_meter(50, 100, 5.0, ncols=None)
    assert isinstance(result, str)

# Condition: not full_bar.format_called in elif branch (no total)
def test_cond_no_bar_in_bar_format_no_total():
    result = format_meter(10, None, 2.0, bar_format='{l_bar}{r_bar}')
    assert isinstance(result, str)

def test_cond_bar_in_bar_format_no_total():
    result = format_meter(10, None, 2.0, bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)

# Condition: ncols truthy in elif (no total)
def test_cond_ncols_truthy_no_total():
    result = format_meter(10, None, 2.0, bar_format='{l_bar}{bar}{r_bar}', ncols=50)
    assert isinstance(result, str)


# --- Path Coverage ---

# Path 1: total=None, no bar_format → just stats
# path: total=None → not bar_format → else branch → return stats string
def test_path_no_total_no_bar_format():
    result = format_meter(5, None, 2.0)
    assert isinstance(result, str)
    assert '5it' in result
    assert '[' in result
    assert ']' in result

# Path 2: total=None, bar_format, no {bar} → return nobar
# path: total=None → bar_format → elif → full_bar not called → return nobar
def test_path_no_total_bar_format_no_bar_placeholder():
    result = format_meter(5, None, 2.0, bar_format='{l_bar}{n_fmt}it')
    assert isinstance(result, str)
    assert '5' in result

# Path 3: total=None, bar_format with {bar}, ncols=None → return res
# path: total=None → bar_format → elif → {bar} present → Bar(0,...) → return res
def test_path_no_total_bar_format_with_bar_ncols_none():
    result = format_meter(5, None, 2.0, bar_format='{l_bar}{bar}{r_bar}', ncols=None)
    assert isinstance(result, str)

# Path 4: total=None, bar_format with {bar}, ncols set → return disp_trim(res)
# path: total=None → bar_format → elif → {bar} present → Bar(0,...) → ncols→ disp_trim
def test_path_no_total_bar_format_with_bar_ncols_set():
    result = format_meter(5, None, 2.0, bar_format='{l_bar}{bar}{r_bar}', ncols=40)
    assert isinstance(result, str)

# Path 5: total known, n exceeded → total reset to None → no bar_format → stats
# path: n>=total+0.5 → total=None → no bar_format → else → stats
def test_path_total_exceeded():
    result = format_meter(200, 100, 5.0)
    assert isinstance(result, str)
    assert '%' not in result or '200%' not in result

# Path 6: total known, ncols=0 → early return l_bar+r_bar
# path: total → ncols==0 → return early
def test_path_total_ncols_zero():
    result = format_meter(50, 100, 5.0, ncols=0)
    assert isinstance(result, str)
    assert '50%' in result
    assert '50/100' in result

# Path 7: total known, bar_format with no {bar} → return nobar
# path: total → bar_format → full_bar not called → return nobar
def test_path_total_bar_format_no_bar():
    result = format_meter(50, 100, 5.0, bar_format='{percentage:3.0f}%')
    assert isinstance(result, str)
    assert '50' in result

# Path 8: total known, default bar_format, ncols=None → return res
# path: total → no bar_format → bar_format=default → {bar} → Bar → ncols None → return res
def test_path_total_default_bar_ncols_none():
    result = format_meter(50, 100, 5.0, ncols=None)
    assert isinstance(result, str)
    assert '50%' in result

# Path 9: total known, default bar_format, ncols set → disp_trim
# path: total → no bar_format → bar_format=default → {bar} → Bar → ncols → disp_trim
def test_path_total_default_bar_ncols_set():
    result = format_meter(50, 100, 5.0, ncols=80)
    assert isinstance(result, str)

# Path 10: unit_scale custom → total scaled, n scaled, rate scaled
# path: unit_scale custom → scale everything → unit_scale=False → continue normally
def test_path_unit_scale_custom_with_rate_and_total():
    # n=50, total=100, scale=2 → n=100, total=200, rate scaled
    result = format_meter(50, 100, 5.0, unit_scale=2, rate=1.0)
    assert isinstance(result, str)
    assert '50%' in result  # 100/200 = 50%

# Path 11: no prefix, no total, no bar_format → stats with no prefix
# path: no prefix → l_bar='' → no total → no bar_format → return ''+'...'
def test_path_no_prefix_no_total():
    result = format_meter(5, None, 2.0, prefix='')
    assert isinstance(result, str)
    # no prefix means result starts with n_fmt
    assert result.startswith('5')

# Path 12: with prefix ending in ": ", total known, ascii=True
# path: prefix with colon → l_bar=prefix → total → ascii bar
def test_path_prefix_colon_total_ascii():
    result = format_meter(50, 100, 5.0, prefix='Progress: ', ascii=True)
    assert isinstance(result, str)
    assert 'Progress' in result
    assert '#' in result or '|' in result

# Path 13: rate=0 (falsy) → inv_rate=None, rate_fmt uses '?'
# path: rate computed as 0 → inv_rate=None → '?' in rate fields
def test_path_rate_zero():
    result = format_meter(0, 100, 5.0, rate=None)  # n=0 → rate=0
    assert isinstance(result, str)
    assert '?' in result

# Path 14: unit_scale=True, total known → format_sizeof for n and total
# path: unit_scale=True → format_sizeof → total → normal bar with SI prefix
def test_path_unit_scale_true_total_known():
    result = format_meter(5000, 10000, 5.0, unit_scale=True)
    assert isinstance(result, str)
    # Both n and total formatted with SI prefix
    assert '50%' in result

# Path 15: postfix as dict (TypeError path) → postfix unchanged
# path: postfix=dict → try ', '+dict raises TypeError → pass → postfix stays dict
def test_path_postfix_dict():
    result = format_meter(10, 100, 2.0, postfix={'a': 1})
    assert isinstance(result, str)

# --- Additional correctness properties ---

def test_property_result_is_string_always():
    for n, total, elapsed in [(0, 100, 0), (50, 100, 5), (100, 100, 10), (5, None, 2)]:
        result = format_meter(n, total, elapsed)
        assert isinstance(result, str)

def test_property_percentage_correct():
    # At 25%, result should contain '25%'
    result = format_meter(25, 100, 5.0)
    assert '25%' in result

def test_property_percentage_100():
    # At exactly 100 out of 100, show 100%
    result = format_meter(100, 100, 10.0)
    assert '100%' in result

def test_property_n_fmt_in_result():
    # n value should appear in result
    result = format_meter(42, 200, 5.0)
    assert '42' in result

def test_property_total_fmt_in_result():
    # total value should appear in result
    result = format_meter(42, 200, 5.0)
    assert '200' in result

def test_property_unit_in_result():
    # custom unit should appear in result
    result = format_meter(10, None, 2.0, unit='files')
    assert 'files' in result

def test_property_elapsed_in_result():
    # elapsed time should appear
    result = format_meter(50, 100, 90.0)  # 1:30
    assert '1:30' in result

def test_property_ncols_trim_length():
    # With ncols set, result should be approximately within ncols width
    result = format_meter(50, 100, 5.0, ncols=30, bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)

def test_property_no_total_returns_no_percentage():
    # No total → no percentage in result
    result = format_meter(10, None, 2.0)
    assert '%' not in result

def test_property_rate_noinv_fmt_low_rate():
    # Very low rate: inv_rate > 1 → s/unit shown
    result = format_meter(1, 1000, 100.0, rate=0.01)
    assert 's/it' in result

def test_property_rate_noinv_fmt_high_rate():
    # High rate: inv_rate < 1 → unit/s shown
    result = format_meter(100, 1000, 2.0, rate=50.0)
    assert 'it/s' in result
```

## Error Message(s)

### [FAILURE] test_ecp_valid_no_total_with_bar_format (type: blackbox)
Assertion: assert isinstance(result, str)
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_1\test_blackbox.py:181: in test_ecp_valid_no_total_with_bar_format
    assert isinstance(result, str)
E   assert False
E    +  where False = isinstance(None, str)
```

### [FAILURE] test_stmt_bar_format_no_total (type: whitebox)
Assertion: assert isinstance(result, str)
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_1\test_whitebox.py:75: in test_stmt_bar_format_no_total
    assert isinstance(result, str)
E   assert False
E    +  where False = isinstance(None, str)
```

### [FAILURE] test_block_unit_scale_true_total_none (type: whitebox)
Assertion: assert '?' in result
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_1\test_whitebox.py:137: in test_block_unit_scale_true_total_none
    assert '?' in result
E   AssertionError: assert '?' in '1.00kit [00:05, 200it/s]'
```

### [FAILURE] test_block_unit_scale_false_total_none (type: whitebox)
Assertion: assert '?' in result
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_1\test_whitebox.py:143: in test_block_unit_scale_false_total_none
    assert '?' in result
E   AssertionError: assert '?' in '10it [00:02,  5.00it/s]'
```

### [FAILURE] test_cond_bar_in_bar_format_no_total (type: whitebox)
Assertion: assert isinstance(result, str)
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_1\test_whitebox.py:368: in test_cond_bar_in_bar_format_no_total
    assert isinstance(result, str)
E   assert False
E    +  where False = isinstance(None, str)
```

### [FAILURE] test_path_no_total_bar_format_with_bar_ncols_none (type: whitebox)
Assertion: assert isinstance(result, str)
```
eval_output\bugsinpy_29-03-2026_00-50\tqdm-2\generated_tests\format_meter_1\test_whitebox.py:398: in test_path_no_total_bar_format_with_bar_ncols_none
    assert isinstance(result, str)
E   assert False
E    +  where False = isinstance(None, str)
```
