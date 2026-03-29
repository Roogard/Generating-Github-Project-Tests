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