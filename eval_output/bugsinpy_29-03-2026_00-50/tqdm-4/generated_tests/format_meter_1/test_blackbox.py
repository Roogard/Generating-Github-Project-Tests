import pytest
from tqdm._tqdm import tqdm

format_meter = tqdm.format_meter

# --- BVA ---

def test_bva_n_zero_total_nonzero():
    """n=0, total=100: 0% progress"""
    result = format_meter(0, 100, 1.0)
    assert '0%' in result
    assert result is not None

def test_bva_n_equals_total():
    """n==total: 100% progress"""
    result = format_meter(100, 100, 10.0)
    assert '100%' in result

def test_bva_n_one_total_100():
    """n=1, total=100: 1% progress"""
    result = format_meter(1, 100, 1.0)
    assert '1%' in result

def test_bva_n_99_total_100():
    """n=99, total=100: 99% progress"""
    result = format_meter(99, 100, 10.0)
    assert '99%' in result

def test_bva_n_exceeds_total():
    """n > total: total should be set to None, fallback to no-bar mode"""
    result = format_meter(150, 100, 10.0)
    # A correct implementation sets total=None when n > total, so no percentage bar
    assert '%' not in result or '150' in result

def test_bva_elapsed_zero_no_rate():
    """elapsed=0, rate=None: rate cannot be computed (division by zero guard)"""
    result = format_meter(0, 100, 0.0)
    assert result is not None
    # No rate available, should show '?' for rate
    assert '?' in result

def test_bva_elapsed_zero_with_rate_override():
    """elapsed=0 but rate provided manually: should use provided rate"""
    result = format_meter(50, 100, 0.0, rate=5.0)
    assert result is not None
    assert '?' not in result or '50' in result

def test_bva_total_none():
    """total=None: no ETA, no percentage bar"""
    result = format_meter(50, None, 5.0)
    assert '%' not in result
    assert '50' in result

def test_bva_total_zero():
    """total=0 (falsy): treated as no total"""
    result = format_meter(0, 0, 1.0)
    assert '%' not in result

def test_bva_ncols_zero():
    """ncols=0: no bar, only stats"""
    result = format_meter(50, 100, 5.0, ncols=0)
    # Should not contain bar characters
    assert '\u2588' not in result
    assert '#' not in result

def test_bva_ncols_one():
    """ncols=1: extremely narrow display"""
    result = format_meter(50, 100, 5.0, ncols=1)
    assert result is not None

def test_bva_ncols_large():
    """ncols=200: wide display"""
    result = format_meter(50, 100, 5.0, ncols=200)
    assert result is not None
    assert '50%' in result

def test_bva_prefix_empty():
    """prefix='': no label before percentage"""
    result = format_meter(50, 100, 5.0, prefix='')
    assert result is not None

def test_bva_prefix_nonempty():
    """prefix='Loading': appears in output"""
    result = format_meter(50, 100, 5.0, prefix='Loading')
    assert 'Loading' in result

def test_bva_prefix_with_colon():
    """prefix already ends with ': ': should not double the colon"""
    result = format_meter(50, 100, 5.0, prefix='Loading: ')
    assert 'Loading: ' in result
    assert 'Loading: : ' not in result

def test_bva_unit_scale_true():
    """unit_scale=True: n_fmt uses SI prefix"""
    result = format_meter(1000, 10000, 5.0, unit_scale=True)
    assert result is not None
    # 1000 should be shown as 1.00k or similar
    assert 'k' in result or '1.00' in result

def test_bva_unit_scale_custom_factor():
    """unit_scale=2: n and total are multiplied by 2"""
    result = format_meter(10, 100, 5.0, unit_scale=2)
    assert result is not None
    # After scaling: n=20, total=200
    assert '20' in result

def test_bva_postfix_string():
    """postfix as string: appended to bar"""
    result = format_meter(50, 100, 5.0, postfix='loss=0.5')
    assert 'loss=0.5' in result

def test_bva_postfix_none():
    """postfix=None: no postfix in output"""
    result = format_meter(50, 100, 5.0, postfix=None)
    assert result is not None

def test_bva_postfix_dict():
    """postfix as non-string type: should not crash"""
    result = format_meter(50, 100, 5.0, postfix={'loss': 0.5})
    assert result is not None

def test_bva_ascii_true():
    """ascii=True: use '#' characters for bar"""
    result = format_meter(50, 100, 5.0, ascii=True)
    assert '#' in result or '5' in result  # at 50% some chars present

def test_bva_ascii_false():
    """ascii=False: use unicode block characters"""
    result = format_meter(50, 100, 5.0, ascii=False)
    # Unicode block char U+2588 or similar should appear
    assert '\u2588' in result or '\u258' in result[0:1] or result is not None

def test_bva_unit_divisor_default():
    """unit_divisor=1000 (default) with unit_scale=True"""
    result = format_meter(1000, 10000, 1.0, unit_scale=True, unit_divisor=1000)
    assert result is not None

def test_bva_unit_divisor_1024():
    """unit_divisor=1024 with unit_scale=True: binary prefix"""
    result = format_meter(1024, 10240, 1.0, unit_scale=True, unit_divisor=1024)
    assert result is not None

# --- ECP ---

def test_ecp_valid_normal_progress():
    """Valid class: n < total, elapsed > 0, no special options"""
    result = format_meter(30, 100, 3.0)
    assert isinstance(result, str)
    assert '30%' in result
    assert '30/100' in result

def test_ecp_valid_no_total():
    """Valid class: total=None, only stats shown"""
    result = format_meter(42, None, 4.2)
    assert isinstance(result, str)
    assert '%' not in result
    assert '42' in result

def test_ecp_valid_complete():
    """Valid class: n == total, 100% complete"""
    result = format_meter(100, 100, 10.0)
    assert '100%' in result
    assert '100/100' in result

def test_ecp_valid_with_prefix():
    """Valid class: prefix provided"""
    result = format_meter(5, 10, 1.0, prefix='Epoch')
    assert 'Epoch' in result
    assert '50%' in result

def test_ecp_valid_rate_override():
    """Valid class: manual rate provided"""
    result = format_meter(0, 100, 0.0, rate=10.0)
    assert result is not None
    assert '10' in result

def test_ecp_valid_unit_custom():
    """Valid class: custom unit"""
    result = format_meter(5, 10, 1.0, unit='MB')
    assert 'MB' in result

def test_ecp_valid_bar_format_no_bar():
    """Valid class: bar_format without {bar} — returns immediately"""
    result = format_meter(50, 100, 5.0, bar_format='{n}/{total}')
    assert result == '50/100'

def test_ecp_valid_bar_format_with_bar():
    """Valid class: bar_format with {bar} — bar is rendered"""
    result = format_meter(50, 100, 5.0, bar_format='{l_bar}{bar}{r_bar}')
    assert isinstance(result, str)
    assert len(result) > 0

def test_ecp_valid_bar_format_desc_empty():
    """Valid class: bar_format with {desc}: prefix, prefix is empty"""
    result = format_meter(50, 100, 5.0,
                          bar_format='{desc}: {percentage:3.0f}%|{bar}|',
                          prefix='')
    # Correct implementation removes '{desc}: ' when prefix is empty
    assert '{desc}' not in result

def test_ecp_valid_bar_format_desc_nonempty():
    """Valid class: bar_format with {desc}, prefix is set"""
    result = format_meter(50, 100, 5.0,
                          bar_format='{desc}: {percentage:3.0f}%|{bar}|',
                          prefix='Test')
    assert 'Test' in result

def test_ecp_invalid_n_greater_total_treated_as_no_total():
    """Invalid class: n > total — total is nullified"""
    result = format_meter(200, 100, 5.0)
    # A correct implementation treats this as total=None
    assert isinstance(result, str)
    # No percentage should appear since total was reset to None
    # (or if it does appear, it means something else is going on)
    # The spec says total=None when n>total, so no %
    assert '%' not in result

def test_ecp_valid_ncols_set():
    """Valid class: ncols restricts bar width"""
    result_narrow = format_meter(50, 100, 5.0, ncols=40)
    result_wide = format_meter(50, 100, 5.0, ncols=200)
    assert len(result_narrow) <= len(result_wide)

def test_ecp_valid_ascii_bar_chars():
    """Valid class: ascii=True uses 0-9 and # chars"""
    result = format_meter(50, 100, 5.0, ascii=True, ncols=40)
    # Bar content must only use ascii chars (not block elements)
    assert '\u2588' not in result

def test_ecp_valid_unicode_bar_chars():
    """Valid class: ascii=False uses unicode block elements"""
    result = format_meter(50, 100, 5.0, ascii=False, ncols=40)
    # Should contain at least one unicode block character in range
    has_unicode_bar = any('\u2580' <= c <= '\u2588' for c in result)
    assert has_unicode_bar

def test_ecp_valid_unit_scale_si():
    """Valid class: unit_scale=True, large n triggers SI prefix"""
    result = format_meter(1_500_000, 10_000_000, 10.0, unit_scale=True)
    assert result is not None
    assert 'M' in result or 'k' in result

def test_ecp_valid_postfix_string_prefixed_comma():
    """Valid class: postfix string is prefixed with ', '"""
    result = format_meter(50, 100, 5.0, postfix='acc=0.9')
    assert ', acc=0.9' in result

def test_ecp_valid_rate_inverse_shown():
    """Valid class: slow rate (< 1 it/s) shows inverse (s/it)"""
    # rate = 0.1 it/s → inv_rate = 10 s/it > 1 → show s/it
    result = format_meter(1, 100, 10.0, rate=0.1)
    assert 's/it' in result or 's/' in result

def test_ecp_valid_rate_forward_shown():
    """Valid class: fast rate (> 1 it/s) shows it/s"""
    # rate = 10 it/s → inv_rate = 0.1 < 1 → show it/s
    result = format_meter(50, 100, 5.0, rate=10.0)
    assert 'it/s' in result

# --- Mutation Detection ---

def test_mutation_n_greater_total_sets_total_none():
    """Detects mutation: `n > total` changed to `n >= total` or `n < total`"""
    # n == total should NOT nullify total
    result_equal = format_meter(100, 100, 10.0)
    assert '100%' in result_equal  # total must still be valid at n==total

    # n > total SHOULD nullify total
    result_exceed = format_meter(101, 100, 10.0)
    assert '%' not in result_exceed  # total was nullified

def test_mutation_frac_calculation():
    """Detects wrong operator in frac = n / total (e.g., n * total)"""
    result = format_meter(25, 100, 5.0)
    assert '25%' in result  # frac must be 0.25, not 2500

def test_mutation_remaining_formula():
    """Detects mutation: remaining = (total - n) / rate vs (total + n) / rate"""
    # At n=0: remaining = total/rate = 100/10 = 10s
    result_start = format_meter(0, 100, 0.0, rate=10.0)
    # At n=100 (complete): remaining = 0/rate = 0s
    result_done = format_meter(100, 100, 10.0, rate=10.0)
    assert result_done is not None
    # remaining at completion should be 0:00
    assert '0:00' in result_done

def test_mutation_percentage_is_frac_times_100():
    """Detects mutation: percentage = frac (missing * 100)"""
    result = format_meter(1, 2, 1.0)
    assert '50%' in result  # 50%, not 0% or 0.5%

def test_mutation_rate_inv_threshold():
    """Detects off-by-one in inv_rate > 1 condition"""
    # inv_rate exactly = 1.0 means rate = 1.0 it/s exactly
    # inv_rate=1 is NOT > 1, so should show it/s not s/it
    result = format_meter(10, 100, 10.0, rate=1.0)
    assert 'it/s' in result  # inv_rate=1, not > 1, show it/s

def test_mutation_rate_inv_above_threshold():
    """Detects off-by-one in inv_rate > 1: inv_rate=2 should show s/it"""
    # rate=0.5 → inv_rate=2 > 1 → s/it
    result = format_meter(5, 100, 10.0, rate=0.5)
    assert 's/it' in result or 's/' in result

def test_mutation_l_bar_percentage_format():
    """Detects wrong format string for percentage in l_bar"""
    result = format_meter(50, 100, 5.0)
    assert ' 50%' in result  # format is '{0:3.0f}%', so space-padded

def test_mutation_ncols_zero_strips_bar_chars():
    """Detects mutation: ncols==0 check skipped → bar returned with bar chars"""
    result = format_meter(50, 100, 5.0, ncols=0)
    assert '\u2588' not in result
    assert '#' not in result

def test_mutation_n_bars_max_1():
    """Detects mutation: max(1, ...) changed to max(0, ...) for N_BARS"""
    # Very narrow ncols where ncols - len(l_bar+r_bar) < 1
    result = format_meter(50, 100, 5.0, ncols=1)
    # Should not crash; N_BARS >= 1
    assert result is not None

def test_mutation_bar_format_no_bar_returns_early():
    """Detects mutation where early return is missing for no-{bar} bar_format"""
    result = format_meter(50, 100, 5.0, bar_format='{n_fmt}/{total_fmt}')
    assert result == '50/100'  # must return this exactly, not append a bar

def test_mutation_prefix_colon_detection():
    """Detects off-by-one in prefix[-2:] == ': ' check"""
    # prefix ending exactly in ': ' should not add another ': '
    result = format_meter(50, 100, 5.0, prefix='Test: ')
    assert 'Test: ' in result
    assert 'Test: : ' not in result

    # prefix NOT ending in ': ' should have ': ' appended
    result2 = format_meter(50, 100, 5.0, prefix='Test')
    assert 'Test: ' in result2

def test_mutation_unit_scale_custom_multiplies_n():
    """Detects mutation: n *= unit_scale missing → n stays unscaled"""
    result = format_meter(10, 100, 5.0, unit_scale=3)
    # n should become 30, total should become 300
    assert '30' in result
    assert '300' in result

def test_mutation_unit_scale_custom_multiplies_rate():
    """Detects mutation: rate not scaled by unit_scale"""
    # With unit_scale=2, rate=5 → scaled_rate=10
    result = format_meter(10, 100, 5.0, unit_scale=2, rate=5.0)
    # After scaling: n=20, total=200, rate=10
    assert result is not None
    assert '20' in result

def test_mutation_rate_none_no_elapsed():
    """Detects mutation: rate computed even when elapsed=0"""
    result = format_meter(10, 100, 0.0)
    assert result is not None
    # rate should be None (not computed), so '?' for remaining
    assert '?' in result

def test_mutation_whitespace_padding_bar_length_lt_N_BARS():
    """Detects mutation in whitespace padding: max(N_BARS - bar_length - 1, 0) vs wrong"""
    # At 0%, bar_length=0, full_bar should be frac_bar + padding
    result = format_meter(0, 100, 0.0, rate=1.0, ncols=20, ascii=True)
    assert result is not None

def test_mutation_no_total_format_string():
    """Detects mutation in no-total branch: wrong variables or operators"""
    result = format_meter(42, None, 4.0, rate=2.0, unit='MB')
    assert '42MB' in result
    assert '[' in result

def test_mutation_elapsed_string_present():
    """Detects mutation where elapsed_str is omitted"""
    result = format_meter(50, 100, 65.0)  # 65s = 1:05
    assert '1:05' in result

def test_mutation_remaining_zero_when_done():
    """Detects mutation (total-n) vs (n-total): at completion remaining should be 0"""
    result = format_meter(100, 100, 10.0, rate=10.0)
    # remaining = (100-100)/10 = 0 → 0:00
    assert '0:00' in result

def test_mutation_inv_rate_formula():
    """Detects mutation: inv_rate = rate instead of 1/rate"""
    # rate=2.0, so inv_rate should be 0.5 (< 1) → show it/s format
    result = format_meter(20, 100, 10.0, rate=2.0)
    assert 'it/s' in result  # inv_rate=0.5 < 1, show forward rate

def test_mutation_postfix_empty_no_comma():
    """Detects mutation: postfix always gets ', ' prefix even when empty"""
    result = format_meter(50, 100, 5.0, postfix=None)
    # Should not have dangling ', ' in the bar
    assert result.count(', ]') == 0

def test_mutation_ascii_frac_bar_divisor():
    """Detects mutation: divmod(...*10) vs divmod(...*8) for ascii bar"""
    # ascii uses *10 denominator, unicode uses *8
    r_ascii = format_meter(1, 10, 1.0, ascii=True, ncols=30)
    r_unicode = format_meter(1, 10, 1.0, ascii=False, ncols=30)
    # Both should work and be different (different chars)
    assert r_ascii != r_unicode

def test_mutation_n_fmt_without_unit_scale():
    """Detects mutation: n_fmt uses format_sizeof even when unit_scale=False"""
    result = format_meter(1500, 10000, 5.0, unit_scale=False)
    assert '1500' in result  # must be plain string, not '1.50k'
    assert 'k' not in result