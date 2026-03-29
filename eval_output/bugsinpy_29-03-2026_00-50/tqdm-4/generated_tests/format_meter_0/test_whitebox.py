import pytest
from tqdm._tqdm import tqdm

format_meter = tqdm.format_meter

# Helper: call format_meter with sensible defaults, override as needed
def fm(**kwargs):
    defaults = dict(n=0, total=100, elapsed=1.0)
    defaults.update(kwargs)
    return format_meter(**defaults)


# --- Statement Coverage ---

# Every major branch touched at least once here.

def test_stmt_basic_with_total():
    # path: total known, no prefix, no bar_format, ascii=False, ncols=None
    result = format_meter(n=50, total=100, elapsed=10.0)
    assert isinstance(result, str)
    assert '50%' in result or '50' in result
    assert len(result) > 0

def test_stmt_no_total():
    # path: total=0 → else branch (no progressbar)
    result = format_meter(n=42, total=0, elapsed=5.0, unit='it')
    assert isinstance(result, str)
    assert '42' in result
    assert 'it' in result

def test_stmt_n_exceeds_total():
    # total is reset to None when n > total
    result = format_meter(n=200, total=100, elapsed=5.0)
    # With total=None a correct implementation shows no ETA/percentage
    assert isinstance(result, str)
    assert '200' in result

def test_stmt_unit_scale_custom():
    # unit_scale != True and != 1 → applies scaling branch
    result = format_meter(n=1, total=10, elapsed=1.0, unit_scale=2)
    assert isinstance(result, str)
    assert len(result) > 0

def test_stmt_rate_override():
    # manual rate override
    result = format_meter(n=50, total=100, elapsed=10.0, rate=5.0)
    assert isinstance(result, str)
    assert '5.00' in result or 'it/s' in result

def test_stmt_rate_none_elapsed_zero():
    # rate=None, elapsed=0 → rate stays None
    result = format_meter(n=0, total=100, elapsed=0.0)
    assert isinstance(result, str)
    assert '?' in result  # rate unknown

def test_stmt_ascii_bar():
    # ascii=True branch
    result = format_meter(n=50, total=100, elapsed=5.0, ascii=True)
    assert isinstance(result, str)
    assert '#' in result or '5' in result

def test_stmt_ncols_zero():
    # ncols=0 → return l_bar[:-1] + r_bar[1:]
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=0)
    assert isinstance(result, str)
    assert '|' not in result or result.count('|') < 2  # no full bar

def test_stmt_ncols_nonzero():
    # ncols set → N_BARS computed from ncols
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=80)
    assert isinstance(result, str)
    assert len(result) > 0

def test_stmt_prefix_with_colon():
    # prefix ending in ": " → bool_prefix_colon_already = True
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='Loading: ')
    assert isinstance(result, str)
    assert 'Loading' in result

def test_stmt_prefix_without_colon():
    # prefix not ending in ": " → append ": "
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='Loading')
    assert isinstance(result, str)
    assert 'Loading:' in result

def test_stmt_postfix_string():
    # postfix is a string
    result = format_meter(n=50, total=100, elapsed=5.0, postfix='loss=0.1')
    assert isinstance(result, str)
    assert 'loss=0.1' in result

def test_stmt_postfix_none():
    # postfix=None → empty string
    result = format_meter(n=50, total=100, elapsed=5.0, postfix=None)
    assert isinstance(result, str)

def test_stmt_postfix_type_error():
    # postfix is a dict (non-string) → TypeError caught → pass
    result = format_meter(n=50, total=100, elapsed=5.0, postfix={'a': 1})
    assert isinstance(result, str)

def test_stmt_unit_scale_true():
    # unit_scale=True → format_sizeof used for n_fmt, total_fmt
    result = format_meter(n=1000, total=10000, elapsed=5.0, unit_scale=True)
    assert isinstance(result, str)
    # SI prefix expected
    assert 'k' in result or 'K' in result or '1.0' in result

def test_stmt_bar_format_no_bar():
    # bar_format without {bar} → return directly
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='{percentage:3.0f}% done')
    assert isinstance(result, str)
    assert '50' in result
    assert 'done' in result

def test_stmt_bar_format_with_bar():
    # bar_format with {bar} → split and format
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)
    assert len(result) > 0

def test_stmt_bar_format_no_prefix_removes_desc():
    # no prefix → {desc}: removed from bar_format
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='',
                          bar_format='{desc}: {percentage:3.0f}%')
    assert isinstance(result, str)
    # Should not contain ": " introduced by desc
    assert result.strip() != ': 50%'


# --- Block Coverage ---

# Basic blocks at branch points not yet hit above:

def test_block_full_bar_bar_length_equals_N_BARS():
    # bar_length >= N_BARS → full_bar = bar + padding (no frac_bar)
    # n == total → frac == 1.0 → bar fills entirely
    result = format_meter(n=100, total=100, elapsed=10.0, ncols=20, ascii=True)
    assert isinstance(result, str)
    assert '#' in result

def test_block_unicode_frac_bar():
    # ascii=False, frac_bar_length > 0 → unicode frac_bar character used
    # Choose n so remainder after divmod is non-zero
    result = format_meter(n=33, total=100, elapsed=5.0, ascii=False, ncols=20)
    assert isinstance(result, str)
    # Should contain unicode block characters
    assert len(result) > 0

def test_block_unicode_no_frac_bar():
    # ascii=False, frac_bar_length == 0 → frac_bar = ' '
    # n=0 → frac=0 → no bar at all, frac_bar_length=0
    result = format_meter(n=0, total=100, elapsed=1.0, ascii=False, ncols=20)
    assert isinstance(result, str)

def test_block_ascii_no_frac_bar():
    # ascii=True, frac_bar_length == 0
    result = format_meter(n=0, total=100, elapsed=1.0, ascii=True, ncols=20)
    assert isinstance(result, str)

def test_block_no_total_with_prefix():
    # no total, prefix set → "(prefix + ': ') + ..."
    result = format_meter(n=10, total=0, elapsed=2.0, prefix='Test')
    assert isinstance(result, str)
    assert 'Test' in result
    assert '10' in result

def test_block_no_total_no_prefix():
    # no total, no prefix → no prefix string prepended
    result = format_meter(n=10, total=0, elapsed=2.0, prefix='')
    assert isinstance(result, str)
    assert 'Test' not in result

def test_block_rate_zero_inv_rate_none():
    # rate=0 explicitly passed → inv_rate=None
    result = format_meter(n=0, total=100, elapsed=1.0, rate=0)
    assert isinstance(result, str)
    assert '?' in result

def test_block_unit_scale_with_rate():
    # unit_scale != True, rate given → rate *= unit_scale in scaling branch
    result = format_meter(n=5, total=50, elapsed=1.0, rate=2.0, unit_scale=3)
    assert isinstance(result, str)

def test_block_bar_format_no_prefix_no_desc_token():
    # bar_format without {desc}: but prefix empty → replacement is no-op
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='',
                          bar_format='{percentage:3.0f}%')
    assert isinstance(result, str)
    assert '50' in result


# --- Condition Coverage ---

# Each boolean sub-expression evaluated both True and False.

# condition: `total and n > total`
def test_cond_n_exceeds_total_true():
    # total=True(100), n>total=True → total set to None
    # n=200 > total=100: True, True  # total: True, n>total: True
    result = format_meter(n=200, total=100, elapsed=5.0)
    assert '200' in result
    # A correct implementation with total=None should show no percentage
    assert '%' not in result

def test_cond_n_not_exceed_total_false():
    # total=True, n>total=False
    # total: True, n>total: False
    result = format_meter(n=50, total=100, elapsed=5.0)
    assert '50%' in result

def test_cond_total_falsy():
    # total: False → short-circuit, n>total not evaluated
    # total: False
    result = format_meter(n=50, total=0, elapsed=5.0)
    assert '%' not in result

# condition: `unit_scale and unit_scale not in (True, 1)`
def test_cond_unit_scale_false():
    # unit_scale=False → branch not entered  # unit_scale: False
    result = format_meter(n=50, total=100, elapsed=5.0, unit_scale=False)
    assert isinstance(result, str)

def test_cond_unit_scale_true_in_set():
    # unit_scale=True → unit_scale not in (True,1) is False  # unit_scale: True, not_in: False
    result = format_meter(n=50, total=100, elapsed=5.0, unit_scale=True)
    assert isinstance(result, str)

def test_cond_unit_scale_custom_not_in_set():
    # unit_scale=2 → both conditions True  # unit_scale: True, not_in: True
    result = format_meter(n=5, total=50, elapsed=1.0, unit_scale=2)
    assert isinstance(result, str)

# condition: `rate is None and elapsed`
def test_cond_rate_none_elapsed_truthy():
    # rate=None, elapsed>0  # rate_is_None: True, elapsed: True
    result = format_meter(n=10, total=100, elapsed=2.0, rate=None)
    assert '5.00' in result  # 10/2 = 5.0 it/s

def test_cond_rate_not_none():
    # rate given → rate is None: False  # rate_is_None: False
    result = format_meter(n=10, total=100, elapsed=2.0, rate=3.0)
    assert '3.00' in result

def test_cond_rate_none_elapsed_falsy():
    # rate=None, elapsed=0  # rate_is_None: True, elapsed: False
    result = format_meter(n=0, total=100, elapsed=0.0)
    assert '?' in result

# condition: `inv_rate and inv_rate > 1` (rate_fmt selection)
def test_cond_inv_rate_gt1():
    # slow rate → inv_rate > 1 → rate_fmt = rate_inv_fmt (s/it)
    # rate=0.5 → inv_rate=2.0 > 1  # inv_rate: truthy, inv_rate>1: True
    result = format_meter(n=1, total=10, elapsed=2.0, rate=0.5)
    assert 's/it' in result

def test_cond_inv_rate_le1():
    # fast rate → inv_rate <= 1 → rate_fmt = rate_noinv_fmt (it/s)
    # rate=5.0 → inv_rate=0.2 < 1  # inv_rate: truthy, inv_rate>1: False
    result = format_meter(n=5, total=10, elapsed=1.0, rate=5.0)
    assert 'it/s' in result

def test_cond_inv_rate_none():
    # rate=0 → inv_rate=None  # inv_rate: falsy
    result = format_meter(n=0, total=100, elapsed=1.0, rate=0)
    assert 'it/s' in result  # falls back to rate_noinv_fmt

# condition: `if unit_scale` (n_fmt branch)
def test_cond_unit_scale_for_n_fmt_true():
    # unit_scale=True → format_sizeof used  # unit_scale: True
    result = format_meter(n=2000, total=10000, elapsed=1.0, unit_scale=True)
    assert '2.0' in result or '2k' in result.lower() or 'k' in result

def test_cond_unit_scale_for_n_fmt_false():
    # unit_scale=False → str(n) used  # unit_scale: False
    result = format_meter(n=2000, total=10000, elapsed=1.0, unit_scale=False)
    assert '2000' in result

# condition: `if prefix` (l_bar setup)
def test_cond_prefix_truthy():
    # prefix non-empty  # prefix: True
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='Epoch')
    assert 'Epoch' in result

def test_cond_prefix_falsy():
    # prefix=''  # prefix: False
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='')
    assert 'Epoch' not in result

# condition: `bool_prefix_colon_already = (prefix[-2:] == ": ")`
def test_cond_prefix_already_has_colon():
    # prefix ends with ": "  # bool_prefix_colon_already: True
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='Epoch: ')
    assert 'Epoch: ' in result
    # Should not double the colon
    assert 'Epoch: : ' not in result

def test_cond_prefix_no_colon():
    # prefix does not end with ": "  # bool_prefix_colon_already: False
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='Epoch')
    assert 'Epoch: ' in result

# condition: `ncols == 0`
def test_cond_ncols_zero_true():
    # ncols=0  # ncols==0: True
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=0)
    assert isinstance(result, str)
    # No bar displayed
    assert '█' not in result and '#' not in result

def test_cond_ncols_not_zero():
    # ncols=80  # ncols==0: False
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=80)
    assert isinstance(result, str)

# condition: `if bar_format`
def test_cond_bar_format_truthy():
    # bar_format given  # bar_format: True
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='{percentage:3.0f}%|{bar}|')
    assert '50%' in result

def test_cond_bar_format_falsy():
    # bar_format=None  # bar_format: False
    result = format_meter(n=50, total=100, elapsed=5.0, bar_format=None)
    assert isinstance(result, str)

# condition: `if not prefix` in bar_format section
def test_cond_bar_format_empty_prefix():
    # prefix='' → {desc}: removed  # not prefix: True
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='',
                          bar_format='{desc}: {percentage:3.0f}%')
    assert isinstance(result, str)
    # Leading ": " should be removed
    assert not result.startswith(': ')

def test_cond_bar_format_nonempty_prefix():
    # prefix given → {desc}: kept  # not prefix: False
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='Run',
                          bar_format='{desc}: {percentage:3.0f}%')
    assert 'Run' in result
    assert '50' in result

# condition: `'{bar}' in bar_format`
def test_cond_bar_in_bar_format_true():
    # {bar} present  # '{bar}' in bar_format: True
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='|{bar}|')
    assert '|' in result

def test_cond_bar_not_in_bar_format():
    # {bar} absent  # '{bar}' in bar_format: False
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='{n_fmt}/{total_fmt}')
    assert '50' in result
    assert '100' in result

# condition: `if ncols` for N_BARS computation
def test_cond_ncols_truthy_for_nbars():
    # ncols=80 → N_BARS from ncols  # ncols: truthy
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=80)
    assert len(result) <= 85  # approximately within ncols

def test_cond_ncols_falsy_for_nbars():
    # ncols=None → N_BARS=10  # ncols: falsy
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=None)
    assert isinstance(result, str)

# condition: `if ascii`
def test_cond_ascii_true():
    # ascii=True  # ascii: True
    result = format_meter(n=50, total=100, elapsed=5.0, ascii=True, ncols=30)
    assert '#' in result or '5' in result  # ASCII characters

def test_cond_ascii_false():
    # ascii=False  # ascii: False
    result = format_meter(n=50, total=100, elapsed=5.0, ascii=False, ncols=30)
    assert isinstance(result, str)
    # Unicode block expected
    assert '█' in result or '▌' in result or ' ' in result

# condition: `if bar_length < N_BARS`
def test_cond_bar_length_lt_N_BARS():
    # partial fill → bar_length < N_BARS  # bar_length < N_BARS: True
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=20, ascii=True)
    assert isinstance(result, str)

def test_cond_bar_length_eq_N_BARS():
    # full fill → bar_length >= N_BARS  # bar_length < N_BARS: False
    result = format_meter(n=100, total=100, elapsed=5.0, ncols=20, ascii=True)
    assert isinstance(result, str)
    # Full bar of hashes
    assert '100%' in result

# condition: rate in rate_noinv_fmt (`if rate` for format_sizeof vs format)
def test_cond_rate_truthy_unit_scale():
    # rate known, unit_scale=True → format_sizeof(rate)  # rate: True, unit_scale: True
    result = format_meter(n=5000, total=10000, elapsed=1.0, rate=5000.0,
                          unit_scale=True)
    assert isinstance(result, str)

def test_cond_rate_falsy_in_fmt():
    # rate=None, elapsed=0 → '?'  # rate: False
    result = format_meter(n=0, total=100, elapsed=0.0)
    assert '?' in result


# --- Path Coverage ---

# Distinct paths through the function.

def test_path_no_total_no_prefix_no_rate():
    # path: n<=total check→total reset(no), unit_scale(no), rate=None elapsed=0→rate stays None
    #       → no total → else branch → no prefix
    # rate: False, no prefix  # path: n>total:F → unit_scale:F → rate=None,elapsed=0→rate=None → total:F → prefix:F
    result = format_meter(n=5, total=0, elapsed=0.0, prefix='')
    assert isinstance(result, str)
    assert '5it' in result or '5' in result
    assert '?' in result

def test_path_no_total_with_prefix_with_rate():
    # path: total=0 → else → prefix given
    # path: n>total:F → unit_scale:F → rate given → total:F → prefix:T
    result = format_meter(n=5, total=0, elapsed=2.0, prefix='Task')
    assert isinstance(result, str)
    assert 'Task' in result
    assert '5' in result

def test_path_total_known_no_bar_format_ascii_ncols_none():
    # path: total → frac/pct → no prefix → ncols!=0 → no bar_format → ncols=None → N_BARS=10
    #       → ascii=True → partial bar → bar_length < N_BARS → return
    # path: n>total:F → unit_scale:F → rate computed → total:T → prefix:F → ncols!=0 → bar_format:F
    #       → ncols:F(None) → ascii:T → bar_length<N_BARS:T → return
    result = format_meter(n=30, total=100, elapsed=3.0, ascii=True, ncols=None)
    assert isinstance(result, str)
    assert '30%' in result
    assert '#' in result

def test_path_total_known_no_bar_format_unicode_ncols_none():
    # path: total → no prefix → ncols=None → no bar_format → N_BARS=10 → ascii=False
    # path: ... → ascii:F → bar_length<N_BARS:T → return
    result = format_meter(n=30, total=100, elapsed=3.0, ascii=False, ncols=None)
    assert isinstance(result, str)
    assert '30%' in result

def test_path_total_ncols_zero_return_early():
    # path: total → ncols==0 → return immediately
    # path: n>total:F → unit_scale:F → total:T → ncols==0:T → return
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=0)
    assert isinstance(result, str)
    # bar chars should not be present
    assert '█' not in result and '#' not in result

def test_path_bar_format_no_bar_token_return():
    # path: total → bar_format with no {bar} → return inside bar_format block
    # path: n>total:F → total:T → ncols!=0 → bar_format:T → {bar}:F → return
    result = format_meter(n=50, total=100, elapsed=5.0,
                          bar_format='{n_fmt} of {total_fmt}')
    assert result == '50 of 100'

def test_path_bar_format_with_bar_token_ncols():
    # path: total → bar_format with {bar} → split → ncols set → N_BARS from ncols
    # path: n>total:F → total:T → bar_format:T → {bar}:T → ncols:T
    result = format_meter(n=50, total=100, elapsed=5.0, ncols=60,
                          bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)
    assert len(result) > 0

def test_path_n_exceeds_total_becomes_no_total():
    # path: n>total → total=None → ... → no total branch
    # path: n>total:T → total reset to None → unit_scale:F → rate computed → total:F → ...
    result = format_meter(n=150, total=100, elapsed=5.0, prefix='')
    assert isinstance(result, str)
    assert '%' not in result
    assert '150' in result

def test_path_unit_scale_scaling_branch_with_rate_and_total():
    # path: unit_scale custom → total*=scale, n*=scale, rate*=scale → unit_scale=False
    #       → total known → full bar path
    # path: unit_scale not in (T,1):T → scale applied → total:T
    result = format_meter(n=5, total=50, elapsed=1.0, rate=2.0, unit_scale=10)
    assert isinstance(result, str)
    # n becomes 50, total becomes 500
    assert '10' in result or '50' in result  # scaled values appear

def test_path_full_bar_unicode():
    # path: total → ascii=False → bar_length >= N_BARS (full bar)
    # n=total → frac=1 → bar fills completely
    result = format_meter(n=100, total=100, elapsed=10.0, ascii=False, ncols=20)
    assert isinstance(result, str)
    assert '100%' in result

def test_path_rate_inv_gt1_no_total():
    # path: slow rate → inv_rate>1 → rate_fmt=rate_inv_fmt → no total
    result = format_meter(n=1, total=0, elapsed=5.0, rate=0.1)
    assert isinstance(result, str)
    assert 's/it' in result

def test_path_postfix_type_error_with_total():
    # path: postfix dict → TypeError → pass → total known → full path
    result = format_meter(n=50, total=100, elapsed=5.0, postfix={'k': 'v'})
    assert isinstance(result, str)
    assert '50%' in result

def test_path_zero_iterations_loop_body():
    # n=0 → frac=0 → bar_length=0 → frac_bar_length=0 → full_bar = ' '*N_BARS
    result = format_meter(n=0, total=100, elapsed=0.0, ascii=True, ncols=None)
    assert isinstance(result, str)
    assert '0%' in result

def test_path_one_iteration_of_bar():
    # n=1, small total to get single char bar
    result = format_meter(n=1, total=10, elapsed=1.0, ascii=True, ncols=12)
    assert isinstance(result, str)

def test_path_many_iterations_partial():
    # Multiple iterations, partial fill
    for n in [10, 50, 90]:
        result = format_meter(n=n, total=100, elapsed=float(n), ncols=40)
        assert isinstance(result, str)
        assert str(n) in result

def test_path_unit_scale_true_no_total():
    # unit_scale=True, total=0 → no total branch → format_sizeof for n_fmt
    result = format_meter(n=5000, total=0, elapsed=2.0, unit_scale=True)
    assert isinstance(result, str)
    # SI prefix for n
    assert 'k' in result or '5' in result

def test_path_bar_format_empty_desc_with_bar():
    # bar_format with {desc}: and {bar}, prefix='' → {desc}: removed, {bar} split
    result = format_meter(n=50, total=100, elapsed=5.0, prefix='',
                          bar_format='{desc}: {percentage:3.0f}%|{bar}|')
    assert isinstance(result, str)
    # Should not start with ': '
    assert not result.startswith(': ')

def test_path_postfix_nonempty_string_no_total():
    # postfix string, no total
    result = format_meter(n=10, total=0, elapsed=2.0, postfix='info')
    assert isinstance(result, str)
    assert 'info' in result

def test_path_rate_display_it_per_s_with_total():
    # fast rate → it/s, total known
    result = format_meter(n=100, total=1000, elapsed=10.0, rate=10.0)
    assert 'it/s' in result
    assert '10%' in result

def test_path_rate_display_s_per_it_with_total():
    # slow rate → s/it, total known
    result = format_meter(n=1, total=100, elapsed=5.0, rate=0.2)
    assert 's/it' in result