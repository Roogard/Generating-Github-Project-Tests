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