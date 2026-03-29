from tqdm.utils import disp_trim
import re

# Helper: ANSI escape sequences
ANSI_RED = "\033[31m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_GREEN = "\033[32m"

RE_ANSI = re.compile(r'\x1b\[[0-9;]*m')


def visual_len(s):
    """Compute the visible length of a string (strip ANSI)."""
    return len(RE_ANSI.sub('', s))


# --- BVA ---

def test_bva_plain_length_zero():
    # BVA: length=0, no ANSI — a correct disp_trim should return empty string
    result = disp_trim("hello", 0)
    assert result == ""

def test_bva_plain_length_one():
    # BVA: length=1, plain string
    result = disp_trim("hello", 1)
    assert result == "h"

def test_bva_plain_length_equals_string_length():
    # BVA: length == len(data), plain string — should return full string
    result = disp_trim("hello", 5)
    assert result == "hello"

def test_bva_plain_length_exceeds_string():
    # BVA: length > len(data), plain string — should return full string unchanged
    result = disp_trim("hello", 10)
    assert result == "hello"

def test_bva_plain_length_one_less_than_string():
    # BVA: length = len(data) - 1, plain string
    result = disp_trim("hello", 4)
    assert result == "hell"

def test_bva_empty_string_length_zero():
    # BVA: empty string, length=0
    result = disp_trim("", 0)
    assert result == ""

def test_bva_empty_string_positive_length():
    # BVA: empty string, length=5
    result = disp_trim("", 5)
    assert result == ""

def test_bva_single_char_plain_length_one():
    # BVA: single character, length=1
    result = disp_trim("x", 1)
    assert result == "x"

def test_bva_single_char_plain_length_zero():
    # BVA: single character, length=0
    result = disp_trim("x", 0)
    assert result == ""

def test_bva_ansi_trim_to_zero():
    # BVA: ANSI string trimmed to 0 visible chars
    # A correct disp_trim should return a string with 0 visible chars
    data = ANSI_RED + "hello" + ANSI_RESET
    result = disp_trim(data, 0)
    assert visual_len(result) == 0

def test_bva_ansi_trim_to_one():
    # BVA: ANSI string trimmed to 1 visible char
    data = ANSI_RED + "hello" + ANSI_RESET
    result = disp_trim(data, 1)
    assert visual_len(result) == 1

def test_bva_ansi_trim_length_equals_visible():
    # BVA: length equals visible length — full visible content returned
    data = ANSI_RED + "hi" + ANSI_RESET
    result = disp_trim(data, 2)
    assert visual_len(result) == 2

def test_bva_ansi_trim_length_exceeds_visible():
    # BVA: length > visible length — full string returned unchanged
    data = ANSI_RED + "hi" + ANSI_RESET
    result = disp_trim(data, 100)
    # visible length should be preserved
    assert visual_len(result) == 2

def test_bva_large_plain_string():
    # BVA: large plain string
    data = "a" * 1000
    result = disp_trim(data, 500)
    assert result == "a" * 500

def test_bva_large_ansi_string():
    # BVA: large ANSI string
    data = ANSI_RED + ("a" * 1000) + ANSI_RESET
    result = disp_trim(data, 500)
    assert visual_len(result) == 500


# --- ECP ---

def test_ecp_valid_plain_string_shorter_than_length():
    # ECP: plain string, length > len(data) — no trimming needed
    result = disp_trim("abc", 10)
    assert result == "abc"

def test_ecp_valid_plain_string_longer_than_length():
    # ECP: plain string, length < len(data) — trimming needed
    result = disp_trim("abcdef", 3)
    assert result == "abc"

def test_ecp_valid_plain_string_exact_length():
    # ECP: plain string, length == len(data)
    result = disp_trim("abc", 3)
    assert result == "abc"

def test_ecp_ansi_string_no_trim_needed():
    # ECP: ANSI string, visible length <= requested length
    data = ANSI_RED + "ab" + ANSI_RESET
    result = disp_trim(data, 10)
    assert visual_len(result) == 2

def test_ecp_ansi_string_trim_needed():
    # ECP: ANSI string, visible length > requested length
    data = ANSI_RED + "abcde" + ANSI_RESET
    result = disp_trim(data, 3)
    assert visual_len(result) == 3

def test_ecp_ansi_string_trim_appends_reset():
    # ECP: When ANSI codes are present after trimming, reset must be appended
    data = ANSI_RED + "hello"
    result = disp_trim(data, 3)
    # A correct implementation should append reset if ANSI is present
    assert result.endswith(ANSI_RESET)
    assert visual_len(result) == 3

def test_ecp_ansi_only_no_visible_chars():
    # ECP: string is only ANSI escape codes, no visible chars
    data = ANSI_RED + ANSI_RESET
    result = disp_trim(data, 5)
    assert visual_len(result) == 0

def test_ecp_multiple_ansi_codes():
    # ECP: multiple ANSI sequences embedded in string
    data = ANSI_RED + "he" + ANSI_BOLD + "llo" + ANSI_RESET
    result = disp_trim(data, 3)
    assert visual_len(result) == 3

def test_ecp_empty_string_any_length():
    # ECP: empty string class — always returns empty
    result = disp_trim("", 100)
    assert result == ""

def test_ecp_plain_string_length_zero():
    # ECP: any non-empty plain string trimmed to 0
    result = disp_trim("hello world", 0)
    assert result == ""

def test_ecp_ansi_no_visible_trim_to_zero():
    # ECP: ANSI-only string, trim to 0 visible chars
    data = ANSI_RED + "abc" + ANSI_RESET
    result = disp_trim(data, 0)
    assert visual_len(result) == 0

def test_ecp_plain_result_no_ansi_appended():
    # ECP: plain string trimmed — result should NOT have ANSI reset appended
    result = disp_trim("hello", 3)
    assert result == "hell"[:3]
    assert not result.endswith(ANSI_RESET)

def test_ecp_ansi_trim_visible_length_respected():
    # ECP: verify visible length == requested after trim for ANSI strings
    data = ANSI_GREEN + "testing" + ANSI_RESET
    for length in [1, 3, 5, 7]:
        result = disp_trim(data, length)
        assert visual_len(result) == length, f"Failed for length={length}"


# --- Mutation Detection ---

def test_mutation_off_by_one_strict_gt_vs_gte():
    # Mutation: `while disp_len(data) > length` vs `while disp_len(data) >= length`
    # If mutation uses >=, trim would overshoot by 1
    # A correct disp_trim("abc", 3) should return exactly 3 visible chars for plain string
    result = disp_trim("abc", 3)
    assert result == "abc"  # detects >= mutation: would return "ab"

def test_mutation_off_by_one_ansi_strict_gt():
    # Mutation: off-by-one in while condition for ANSI string
    data = ANSI_RED + "abcde" + ANSI_RESET
    result = disp_trim(data, 3)
    # correct: exactly 3 visible chars; mutated (>=): 2 visible chars
    assert visual_len(result) == 3

def test_mutation_slice_length_plain():
    # Mutation: `data[:length]` vs `data[:length+1]` or `data[:length-1]`
    result = disp_trim("hello", 3)
    assert result == "hel"  # detects +1 mutation (would give "hell"), -1 (would give "he")

def test_mutation_slice_boundary_length_equals_len():
    # Mutation: `data[:length]` where length == len(data)
    # Off-by-one: data[:6] on "hello" (len=5) still returns "hello" in Python,
    # but data[:4] would return "hell". Use exact boundary.
    result = disp_trim("hello", 5)
    assert result == "hello"

def test_mutation_ansi_check_condition_negated():
    # Mutation: `if RE_ANSI.search(data)` → `if not RE_ANSI.search(data)`
    # If negated, plain strings would get reset appended; ANSI strings would not
    data = ANSI_RED + "hi"
    result = disp_trim(data, 1)
    # A correct implementation: ANSI present → append reset
    assert result.endswith(ANSI_RESET)

def test_mutation_ansi_reset_not_appended_for_plain():
    # Mutation: always appending reset (wrong operator in condition)
    result = disp_trim("hello", 3)
    # A correct implementation must NOT append reset for plain strings
    assert not result.endswith(ANSI_RESET)

def test_mutation_disp_len_vs_len_in_branch():
    # Mutation: `len(data) == disp_len(data)` → `len(data) != disp_len(data)`
    # If mutated, plain strings would go through the ANSI loop instead of fast-path
    # A correct fast-path: plain string trimmed to exact length
    result = disp_trim("abcde", 3)
    assert result == "abc"

def test_mutation_wrong_variable_data_vs_length():
    # Mutation: `data[:-1]` → `data[-1:]` (wrong slice direction)
    # If wrong, the loop would keep last char only and loop forever (or wrong output)
    data = ANSI_RED + "hello" + ANSI_RESET
    result = disp_trim(data, 2)
    assert visual_len(result) == 2  # would fail/loop-error with wrong slice

def test_mutation_reset_string_constant():
    # Mutation: wrong reset constant e.g. "\033[00m" or "\033[1m" appended
    data = ANSI_RED + "test"
    result = disp_trim(data, 2)
    assert result.endswith("\033[0m")  # specifically the standard ANSI reset

def test_mutation_off_by_one_trim_one_too_many():
    # Mutation: `data[:-1]` causes one too many deletions if condition is wrong
    data = ANSI_RED + "ab" + ANSI_RESET
    result = disp_trim(data, 2)
    # Correct: exactly 2 visible chars; off-by-one: 1 visible char
    assert visual_len(result) == 2

def test_mutation_fast_path_returns_too_much():
    # Mutation: `data[:length]` → `data[:length+1]` in the fast path
    result = disp_trim("hello", 3)
    assert len(result) == 3  # plain string, visible == raw length

def test_mutation_fast_path_returns_too_little():
    # Mutation: `data[:length]` → `data[:length-1]`
    result = disp_trim("hello", 4)
    assert result == "hell"  # detects -1 mutation which would give "hel"

def test_mutation_ansi_appended_when_no_ansi_present_after_trim():
    # If ANSI codes are entirely removed by trimming (e.g. trim before any ANSI),
    # a correct implementation should check remaining data, not original
    # Trim just plain text before the ANSI sequence
    data = "hi" + ANSI_RED + "world" + ANSI_RESET
    result = disp_trim(data, 2)
    # visible chars are "hi", no ANSI in the trimmed portion if trim cut before \033
    # The key invariant: visible length must be exactly 2
    assert visual_len(result) == 2

def test_mutation_length_zero_ansi_no_infinite_loop():
    # Mutation: off-by-one in while condition could cause infinite loop at 0
    # This test ensures termination and correctness
    data = ANSI_RED + "abc" + ANSI_RESET
    result = disp_trim(data, 0)
    assert visual_len(result) == 0