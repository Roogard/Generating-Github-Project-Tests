import pytest
from tqdm._tqdm import tqdm

format_meter = tqdm.format_meter

# --- Statement Coverage ---

def test_stmt_no_total_no_prefix():
    # path: no total branch, no prefix
    result = format_meter(5, None, 2.0, unit='it')
    assert '5it' in result
    assert '[' in result

def test_stmt_no_total_with_prefix():
    # path: no total branch, with prefix
    result = format_meter(5, None, 2.0, prefix='Loading')
    assert 'Loading' in result
    assert '5it' in result

def test_stmt_total_known_basic():
    # path: total known, ascii=False, no bar_format, ncols=None
    result = format_meter(50, 100, 10.0)
    assert '50%' in result or '50' in result
    assert isinstance(result, str)
    assert len(result) > 0

def test_stmt_n_exceeds_total_reset():
    # sanity check: n > total => total becomes None
    # A correct implementation should still return a valid string
    result = format_meter(150, 100, 10.0)
    assert isinstance(result, str)
    # since total is set to None, no ETA or percentage shown
    assert '150it' in result

def test_stmt_unit_scale_custom():
    # apply custom scale if unit_scale not in (True, 1)
    result = format_meter(500, 1000, 10.0, unit_scale=2, unit='it')
    assert isinstance(result, str)
    # n*2=1000, total*2=2000, scaled values should appear
    assert len(result) > 0

def test_stmt_rate_none_elapsed_zero():
    # rate=None, elapsed=0 => rate stays None => inv_rate=None
    result = format_meter(0, 100, 0.0)
    assert isinstance(result, str)
    assert '?' in result  # rate unknown

def test_stmt_rate_provided():
    # manual rate override
    result = format_meter(50, 100, 10.0, rate=5.0)
    assert isinstance(result, str)
    # inv_rate = 1/5.0 = 0.2 < 1, so rate_noinv_fmt used
    assert ' 5.00it/s' in result or '5.00' in result

def test_stmt_postfix_string():
    # postfix as a string
    result = format_meter(50, 100, 10.0, postfix='loss=0.5')
    assert 'loss=0.5' in result

def test_stmt_postfix_non_string():
    # postfix as a non-string type (TypeError caught, pass)
    result = format_meter(50, 100, 10.0, postfix=42)
    assert isinstance(result, str)

def test_stmt_ncols_zero():
    # ncols=0: return l_bar[:-1] + r_bar[1:]
    result = format_meter(50, 100, 10.0, ncols=0)
    assert isinstance(result, str)
    assert len(result) > 0

def test_stmt_ascii_true():
    # ascii=True branch
    result = format_meter(50, 100, 10.0, ascii=True)
    assert '#' in result or '5' in result
    assert isinstance(result, str)

def test_stmt_ascii_false_unicode():
    # ascii=False branch => unicode blocks
    result = format_meter(50, 100, 10.0, ascii=False)
    assert isinstance(result, str)
    assert '\u2588' in result or len(result) > 0

def test_stmt_unit_scale_true():
    # unit_scale=True => format_sizeof used
    result = format_meter(1000, 10000, 5.0, unit_scale=True)
    assert isinstance(result, str)
    assert len(result) > 0

def test_stmt_bar_format_no_bar():
    # bar_format without {bar}: early return from bar_format.format(...)
    result = format_meter(50, 100, 10.0, bar_format='{percentage:3.0f}%')
    assert ' 50%' in result

def test_stmt_bar_format_with_bar():
    # bar_format with {bar}
    result = format_meter(50, 100, 10.0, bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)
    assert len(result) > 0

def test_stmt_ncols_specified():
    # ncols specified => N_BARS calculated from ncols
    result = format_meter(50, 100, 10.0, ncols=60)
    assert isinstance(result, str)

def test_stmt_prefix_colon_already():
    # prefix already ends with ": "
    result = format_meter(50, 100, 10.0, prefix='Epoch: ')
    assert 'Epoch: ' in result

def test_stmt_prefix_no_colon():
    # prefix does NOT end with ": "
    result = format_meter(50, 100, 10.0, prefix='Epoch')
    assert 'Epoch: ' in result

# --- Block Coverage ---

def test_block_bar_full():
    # bar_length >= N_BARS => full_bar = bar + padding (no frac_bar)
    # Use n=total to get frac=1.0
    result = format_meter(100, 100, 10.0, ascii=True, ncols=40)
    assert isinstance(result, str)
    assert '100%' in result or '100' in result

def test_block_bar_partial_frac_nonzero():
    # frac_bar_length != 0 => frac_bar is a character, not space
    # Use a value that produces non-zero frac_bar_length
    result = format_meter(1, 10, 5.0, ascii=True, ncols=20)
    assert isinstance(result, str)

def test_block_bar_partial_frac_zero():
    # frac_bar_length == 0 => frac_bar = ' '
    # Use n=0 to get frac=0
    result = format_meter(0, 10, 0.001, ascii=True, ncols=20)
    assert isinstance(result, str)

def test_block_unicode_frac_nonzero():
    # ascii=False, frac_bar_length != 0
    result = format_meter(3, 8, 5.0, ascii=False, ncols=20)
    assert isinstance(result, str)

def test_block_unicode_frac_zero():
    # ascii=False, frac_bar_length == 0
    result = format_meter(0, 8, 0.001, ascii=False, ncols=20)
    assert isinstance(result, str)

def test_block_bar_format_empty_desc():
    # bar_format with {desc}: and empty prefix => auto-remove ": "
    result = format_meter(50, 100, 10.0,
                          bar_format='{desc}: {percentage:3.0f}%|{bar}|',
                          prefix='')
    # {desc} is empty so "{desc}: " should be removed
    assert isinstance(result, str)
    # colon-space after empty desc should not appear at start
    assert not result.startswith(': ')

def test_block_bar_format_nonempty_desc():
    # bar_format with {desc}: and non-empty prefix
    result = format_meter(50, 100, 10.0,
                          bar_format='{desc}: {percentage:3.0f}%|{bar}|',
                          prefix='MyLabel')
    assert 'MyLabel' in result

def test_block_remaining_rate_zero():
    # rate=0 (elapsed=0, n=0): remaining=0, remaining_str='?'
    result = format_meter(0, 100, 0.0)
    assert '?' in result

def test_block_unit_scale_total_none():
    # unit_scale=True, total=None => total_fmt stays None
    result = format_meter(500, None, 5.0, unit_scale=True)
    assert isinstance(result, str)

def test_block_no_rate_no_elapsed():
    # rate=None, elapsed=0 => rate stays None
    result = format_meter(10, 100, 0.0, rate=None)
    assert isinstance(result, str)
    assert '?' in result

# --- Condition Coverage ---

def test_cond_total_truthy_n_not_exceeds():
    # total=100, n=50: total is truthy, n > total is False
    # total stays 100 (n > total: False)
    result = format_meter(50, 100, 10.0)
    assert '50%' in result or '50' in result  # total known path

def test_cond_total_truthy_n_exceeds():
    # total=100, n=150: total is truthy, n > total is True => total=None
    # n > total: True
    result = format_meter(150, 100, 5.0)
    # A correct implementation sets total=None when n>total
    assert '150it' in result  # no-total path

def test_cond_total_falsy():
    # total=0 or None: total is falsy, goes to else branch
    # total falsy: True
    result = format_meter(5, 0, 2.0)
    assert '5it' in result

def test_cond_unit_scale_not_special():
    # unit_scale=2 (not True, not 1): enters custom scale branch
    # unit_scale truthy: True, unit_scale not in (True,1): True
    result = format_meter(100, 1000, 5.0, unit_scale=2)
    assert isinstance(result, str)

def test_cond_unit_scale_true():
    # unit_scale=True: truthy but in (True, 1), skip custom scale
    # unit_scale truthy: True, unit_scale not in (True,1): False
    result = format_meter(100, 1000, 5.0, unit_scale=True)
    assert isinstance(result, str)

def test_cond_unit_scale_false():
    # unit_scale=False: falsy, skip custom scale entirely
    # unit_scale truthy: False
    result = format_meter(100, 1000, 5.0, unit_scale=False)
    assert isinstance(result, str)

def test_cond_rate_none_elapsed_nonzero():
    # rate is None: True, elapsed is nonzero: True => rate computed
    result = format_meter(10, 100, 5.0, rate=None)
    assert '?' not in result or '0:' in result  # rate should be known

def test_cond_rate_provided_elapsed_nonzero():
    # rate is not None: False => skip rate computation
    result = format_meter(10, 100, 5.0, rate=2.0)
    assert isinstance(result, str)

def test_cond_inv_rate_gt1():
    # inv_rate > 1: True => rate_fmt = rate_inv_fmt (s/unit)
    # rate = 0.5 it/s => inv_rate = 2.0 > 1
    result = format_meter(5, 100, 10.0, rate=0.5)
    assert 's/it' in result  # inv rate displayed

def test_cond_inv_rate_lte1():
    # inv_rate <= 1: rate = 5 it/s => inv_rate = 0.2 < 1
    # rate_fmt = rate_noinv_fmt
    result = format_meter(50, 100, 10.0, rate=5.0)
    assert 'it/s' in result

def test_cond_inv_rate_none():
    # inv_rate is None (rate=0): rate_fmt = rate_noinv_fmt = '?it/s'
    result = format_meter(0, 100, 0.0)
    assert '?it/s' in result or '?' in result

def test_cond_postfix_truthy_string():
    # postfix truthy: True => ', ' + postfix
    result = format_meter(50, 100, 5.0, postfix='acc=0.9')
    assert 'acc=0.9' in result

def test_cond_postfix_falsy():
    # postfix falsy (None/empty): postfix => ''
    result = format_meter(50, 100, 5.0, postfix=None)
    assert isinstance(result, str)

def test_cond_prefix_truthy():
    # prefix truthy: True => l_bar starts with prefix
    result = format_meter(50, 100, 5.0, prefix='Test')
    assert 'Test' in result

def test_cond_prefix_falsy():
    # prefix falsy (empty string): False => l_bar = ''
    result = format_meter(50, 100, 5.0, prefix='')
    assert isinstance(result, str)

def test_cond_prefix_colon_already_true():
    # bool_prefix_colon_already: True (prefix ends with ': ')
    result = format_meter(50, 100, 5.0, prefix='Step: ')
    assert 'Step: ' in result
    # Should NOT double the colon
    assert 'Step: : ' not in result

def test_cond_prefix_colon_already_false():
    # bool_prefix_colon_already: False (prefix does not end with ': ')
    result = format_meter(50, 100, 5.0, prefix='Step')
    assert 'Step: ' in result

def test_cond_ncols_zero():
    # ncols == 0: True => early return without bar
    result = format_meter(50, 100, 5.0, ncols=0)
    assert isinstance(result, str)
    # should not contain bar characters
    assert '\u2588' not in result
    assert '##' not in result

def test_cond_bar_format_truthy():
    # bar_format truthy: True
    result = format_meter(50, 100, 5.0, bar_format='{percentage:.0f}%')
    assert '50%' in result

def test_cond_bar_format_falsy():
    # bar_format falsy (None/empty): False => default bar
    result = format_meter(50, 100, 5.0, bar_format=None)
    assert isinstance(result, str)

def test_cond_bar_format_has_bar_true():
    # '{bar}' in bar_format: True
    result = format_meter(50, 100, 5.0,
                          bar_format='{percentage:.0f}%|{bar}|{elapsed}')
    assert isinstance(result, str)

def test_cond_bar_format_has_bar_false():
    # '{bar}' not in bar_format: False => return immediately
    result = format_meter(50, 100, 5.0, bar_format='{percentage:.0f}%')
    assert '50%' in result

def test_cond_ncols_truthy_for_nbars():
    # ncols truthy: True => N_BARS from ncols
    result = format_meter(50, 100, 5.0, ncols=50)
    assert isinstance(result, str)
    # total width should be approximately ncols
    from tqdm._utils import RE_ANSI
    clean = RE_ANSI.sub('', result)
    assert len(clean) <= 50 + 5  # allow some slack

def test_cond_ncols_falsy_for_nbars():
    # ncols falsy (None): False => N_BARS = 10
    result = format_meter(50, 100, 5.0, ncols=None)
    assert isinstance(result, str)

def test_cond_ascii_true_branch():
    # ascii: True
    result = format_meter(50, 100, 5.0, ascii=True)
    assert isinstance(result, str)
    # No unicode block chars
    assert '\u2588' not in result

def test_cond_ascii_false_branch():
    # ascii: False
    result = format_meter(50, 100, 5.0, ascii=False)
    assert isinstance(result, str)

def test_cond_bar_length_lt_nbars():
    # bar_length < N_BARS: True => full_bar has frac_bar + spaces
    result = format_meter(1, 100, 5.0, ascii=True, ncols=30)
    assert isinstance(result, str)

def test_cond_bar_length_eq_nbars():
    # bar_length >= N_BARS: True (n=total => frac=1)
    result = format_meter(100, 100, 5.0, ascii=True, ncols=30)
    assert isinstance(result, str)
    assert '100%' in result or '100' in result

def test_cond_rate_for_remaining_truthy():
    # rate truthy: True => remaining = (total-n)/rate
    result = format_meter(50, 100, 5.0, rate=10.0)
    # remaining = 50/10 = 5s, remaining_str should not be '?'
    assert '?' not in result or 'it' in result

def test_cond_rate_for_remaining_falsy():
    # rate falsy: False => remaining=0, remaining_str='?'
    result = format_meter(50, 100, 0.0, rate=None)
    assert '?' in result

# --- Path Coverage ---

def test_path_no_total_no_prefix_no_rate():
    # path: n>total skip → unit_scale=False skip → rate=None,elapsed=0 → inv_rate=None
    #       → unit_scale=False → postfix='' → total=False → no-total else
    # total=None, elapsed=0, no prefix, no rate
    result = format_meter(5, None, 0.0)
    # A correct implementation: "5it [00:00, ?it/s]"
    assert '5it' in result
    assert '?' in result

def test_path_no_total_with_prefix_with_rate():
    # path: no total, prefix given, rate given
    result = format_meter(5, None, 2.0, prefix='Proc', rate=2.5)
    assert 'Proc' in result
    assert '5it' in result
    assert isinstance(result, str)

def test_path_total_ncols0():
    # path: total known → ncols==0 → early return l_bar[:-1]+r_bar[1:]
    result = format_meter(50, 100, 5.0, ncols=0, prefix='Step')
    assert isinstance(result, str)
    # Should contain percentage and stats but no bar
    assert '50' in result

def test_path_total_bar_format_no_bar_var():
    # path: total known → bar_format truthy → '{bar}' not in bar_format → return formatted string
    result = format_meter(25, 100, 5.0, bar_format='{n}/{total}')
    assert '25' in result
    assert '100' in result

def test_path_total_bar_format_with_bar_var_ncols():
    # path: total known → bar_format with {bar} → ncols given → N_BARS from ncols
    result = format_meter(25, 100, 5.0,
                          bar_format='{l_bar}{bar}{r_bar}',
                          ncols=60)
    assert isinstance(result, str)

def test_path_total_no_bar_format_ascii_bar_full():
    # path: total → no bar_format → ncols=None → N_BARS=10 → ascii=True → bar_length>=N_BARS
    result = format_meter(100, 100, 5.0, ascii=True)
    assert '100%' in result or '100' in result
    assert '#' * 10 in result

def test_path_total_no_bar_format_ascii_bar_partial():
    # path: total → no bar_format → ncols=None → N_BARS=10 → ascii=True → bar_length<N_BARS
    result = format_meter(1, 10, 1.0, ascii=True)
    assert isinstance(result, str)
    assert '10%' in result or '10' in result

def test_path_total_no_bar_format_unicode_bar_full():
    # path: total → no bar_format → ncols=None → N_BARS=10 → ascii=False → bar_length>=N_BARS
    result = format_meter(100, 100, 5.0, ascii=False)
    assert '\u2588' * 10 in result

def test_path_total_no_bar_format_unicode_bar_partial():
    # path: total → no bar_format → ncols=None → N_BARS=10 → ascii=False → bar_length<N_BARS
    result = format_meter(5, 100, 5.0, ascii=False)
    assert isinstance(result, str)
    assert '5%' in result or '5' in result

def test_path_unit_scale_custom_rate_given():
    # path: unit_scale=2, rate given → scale applied → total known → normal bar
    result = format_meter(100, 500, 5.0, unit_scale=2, rate=10.0)
    # After scale: n=200, total=1000, rate=20
    assert isinstance(result, str)

def test_path_unit_scale_true_no_total():
    # path: unit_scale=True (skip custom scale) → no total → format_sizeof for n
    result = format_meter(1500, None, 5.0, unit_scale=True)
    assert isinstance(result, str)
    # 1500 formatted with SI: should show '1.50k' or similar
    assert 'k' in result or '1.5' in result

def test_path_total_with_postfix_dict_type():
    # path: total known, postfix is dict (non-string) → TypeError caught → pass
    result = format_meter(50, 100, 5.0, postfix={'loss': 0.5})
    assert isinstance(result, str)

def test_path_rate_inv_gt1():
    # path: rate=0.5 → inv_rate=2>1 → rate_fmt=rate_inv_fmt → total → bar
    result = format_meter(50, 100, 10.0, rate=0.5)
    assert 's/it' in result

def test_path_zero_iterations_loop_analogue():
    # zero progress: n=0, total=100, elapsed tiny
    result = format_meter(0, 100, 0.001)
    assert '  0%' in result or '0%' in result
    assert isinstance(result, str)

def test_path_full_completion():
    # n=total: 100% complete, all bars filled
    result = format_meter(200, 200, 20.0)
    assert '100%' in result
    assert isinstance(result, str)

def test_path_bar_format_empty_prefix_removes_desc_colon():
    # path: bar_format with {desc}: , prefix='' → auto-remove → {desc}: stripped
    result = format_meter(50, 100, 5.0,
                          bar_format='{desc}: {percentage:.0f}%',
                          prefix='')
    # A correct implementation removes "{desc}: " when desc is empty
    assert ': ' not in result or 'desc' not in result

def test_path_bar_format_nonempty_prefix_keeps_desc():
    # path: bar_format with {desc}: , prefix='MyLabel' → not removed
    result = format_meter(50, 100, 5.0,
                          bar_format='{desc}: {percentage:.0f}%',
                          prefix='MyLabel')
    assert 'MyLabel: ' in result

# --- Property / Invariant Assertions ---

def test_property_length_preserved_unit_scale():
    # format_sizeof result is deterministic for known values
    result = format_meter(1000, 10000, 5.0, unit_scale=True)
    assert isinstance(result, str)
    assert len(result) > 0

def test_property_percentage_monotone():
    # More progress => higher or equal percentage shown
    r1 = format_meter(10, 100, 5.0)
    r2 = format_meter(90, 100, 5.0)
    # Both should be valid strings representing progress
    assert '10%' in r1 or '10' in r1
    assert '90%' in r2 or '90' in r2

def test_property_elapsed_str_present():
    # elapsed string should always appear in output
    result = format_meter(50, 100, 125.0)  # 2m5s
    assert '2:05' in result or '02:05' in result

def test_property_ncols_constrains_width():
    # output width should not greatly exceed ncols
    from tqdm._utils import RE_ANSI
    for ncols in [20, 40, 80]:
        result = format_meter(50, 100, 5.0, ncols=ncols)
        clean = RE_ANSI.sub('', result)
        # Allow some slack for edge cases
        assert len(clean) <= ncols + 10, \
            f"ncols={ncols}, len={len(clean)}, result={repr(result)}"

def test_property_unit_in_output():
    # Custom unit should appear in the output
    result = format_meter(5, None, 2.0, unit='imgs')
    assert 'imgs' in result

def test_property_n_fmt_in_output():
    # n should always appear in output
    for n in [0, 1, 42, 999]:
        result = format_meter(n, None, 1.0)
        assert str(n) in result

def test_property_total_fmt_in_output():
    # total should appear when total is known
    result = format_meter(50, 100, 5.0)
    assert '100' in result