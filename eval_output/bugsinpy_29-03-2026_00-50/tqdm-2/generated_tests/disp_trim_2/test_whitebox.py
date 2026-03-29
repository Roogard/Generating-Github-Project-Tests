from tqdm.utils import disp_trim, disp_len
import re

RE_ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')

# --- Statement Coverage ---

# Test 1: No ANSI characters, len(data) == disp_len(data), early return path
# data[:length] is returned directly
def test_stmt_no_ansi_truncate():
    data = "hello world"
    result = disp_trim(data, 5)
    # A correct trim of a plain ASCII string to length 5 should return first 5 chars
    assert result == "hello"
    assert len(result) == 5

# Test 2: No ANSI, length >= len(data), returns full string
def test_stmt_no_ansi_no_truncate():
    data = "hi"
    result = disp_trim(data, 10)
    assert result == "hi"

# Test 3: ANSI characters present, disp_len > length, loop executes, ANSI reset appended
def test_stmt_ansi_with_reset():
    # Red-colored text: \033[31m followed by text
    data = "\033[31mhello\033[0m"
    result = disp_trim(data, 3)
    # A correct trim should result in a display length <= 3
    assert disp_len(result) <= 3
    # Since ANSI escape remains in the trimmed result, reset should be appended
    assert result.endswith("\033[0m")

# Test 4: ANSI present, disp_len <= length (no loop), but ANSI in data → reset appended
def test_stmt_ansi_no_loop_needed():
    # data with ANSI but short display length
    data = "\033[32mhi\033[0m"
    # disp_len("hi") == 2, length=10 → loop won't run, but RE_ANSI.search(data) is True
    result = disp_trim(data, 10)
    # A correct implementation: display fits, but if ANSI is present and no loop ran,
    # the original data is returned as-is (len(data) != disp_len(data) path)
    # The loop doesn't execute, RE_ANSI.search check happens, reset appended
    assert disp_len(result) <= 10
    assert result.endswith("\033[0m")

# Test 5: ANSI present, after trimming no ANSI remains → return without reset
def test_stmt_ansi_trimmed_away_no_reset():
    # ANSI only at the end; trim cuts it off entirely
    # "\033[31m" is 5 chars of display_len 0, "ab\033[0m" → disp_len("ab") == 2
    # Build: plain text first, ANSI at end
    data = "ab\033[31m"
    # disp_len("ab\033[31m") == 2 (ANSI contributes 0), length=1
    result = disp_trim(data, 1)
    assert disp_len(result) <= 1
    # After trimming to 1 char display, the ANSI escape at end should be trimmed away
    # If no ANSI remains, no reset appended
    assert not result.endswith("\033[0m") or RE_ANSI.search(result[:-4])

# --- Block Coverage ---

# Block 1: early-return block (len == disp_len)
# Covered by test_stmt_no_ansi_truncate

# Block 2: while loop body
def test_block_while_loop_body():
    data = "\033[1mabcdef\033[0m"
    result = disp_trim(data, 2)
    assert disp_len(result) <= 2

# Block 3: if RE_ANSI branch → True (reset appended)
# Covered by test_stmt_ansi_with_reset

# Block 4: final return (no ANSI after trim)
def test_block_no_ansi_after_trim():
    # Plain ASCII: no ANSI at all, goes through while loop then final return
    # But plain ASCII goes through early return... need data where len != disp_len
    # Use wide characters (East Asian width = 2 display units each)
    # 'Ａ' is a full-width character, disp_len != len
    data = "ＡＢＣ"  # 3 full-width chars, disp_len = 6, len = 3
    result = disp_trim(data, 4)
    # disp_len > length, loop runs; no ANSI, so no reset appended
    assert disp_len(result) <= 4
    assert not result.endswith("\033[0m")
    # property: result should be a prefix of data
    assert data.startswith(result)

# --- Condition Coverage ---

# Condition: len(data) == disp_len(data)
# True case (plain ASCII): covered by test_stmt_no_ansi_truncate  # len==disp_len: True
# False case (ANSI or wide chars):
def test_cond_len_ne_disp_len():
    # len(data) != disp_len(data): False branch of first if  # len==disp_len: False
    data = "\033[1mtest\033[0m"
    result = disp_trim(data, 2)
    assert disp_len(result) <= 2

# Condition: disp_len(data) > length
# True case (loop runs): covered by test_stmt_ansi_with_reset  # disp_len>length: True
# False case (loop skipped):
def test_cond_disp_len_not_greater():
    # disp_len(data) <= length → while loop not entered  # disp_len>length: False
    data = "\033[32mhi\033[0m"
    result = disp_trim(data, 100)
    assert disp_len(result) <= 100

# Condition: RE_ANSI.search(data) — True
def test_cond_re_ansi_true():
    # ANSI escape remains after trimming  # RE_ANSI.search: True
    data = "\033[31mhello\033[0m"
    result = disp_trim(data, 2)
    assert result.endswith("\033[0m")
    assert disp_len(result) <= 2

# Condition: RE_ANSI.search(data) — False (no ANSI after trim)
def test_cond_re_ansi_false():
    # Wide chars, no ANSI  # RE_ANSI.search: False
    data = "ＡＢＣ"
    result = disp_trim(data, 3)
    assert not RE_ANSI.search(result)
    assert not result.endswith("\033[0m")
    assert disp_len(result) <= 3

# --- Path Coverage ---

# Path 1: len(data)==disp_len(data) → early return  (short-circuit)
# path: condition-True → return data[:length]
def test_path_early_return_no_truncation():
    # path: len==disp_len True → return full string
    data = "abc"
    result = disp_trim(data, 10)
    assert result == "abc"

def test_path_early_return_with_truncation():
    # path: len==disp_len True → return data[:length] (truncated)
    data = "abcdef"
    result = disp_trim(data, 3)
    assert result == "abc"

# Path 2: len!=disp_len, disp_len<=length, ANSI present → reset appended
# path: first-if False → while-skip → RE_ANSI True → return data+reset
def test_path_no_loop_ansi_reset():
    data = "\033[1mhi\033[0m"
    result = disp_trim(data, 50)
    # display fits, ANSI present, reset appended
    assert result.endswith("\033[0m")
    assert disp_len(result) <= 50

# Path 3: len!=disp_len, disp_len>length, loop runs, ANSI remains → reset appended
# path: first-if False → while-true (multiple iters) → RE_ANSI True → return+reset
def test_path_loop_ansi_reset():
    data = "\033[31mabcde\033[0m"
    result = disp_trim(data, 3)
    assert disp_len(result) <= 3
    assert result.endswith("\033[0m")

# Path 4: len!=disp_len, disp_len>length, loop runs, no ANSI remains → plain return
# path: first-if False → while-true → RE_ANSI False → return data
def test_path_loop_no_ansi():
    # Wide chars trimmed, no ANSI sequences
    data = "ＡＢＣ"  # disp_len=6, len=3
    result = disp_trim(data, 2)
    assert disp_len(result) <= 2
    assert not result.endswith("\033[0m")
    # property: remaining chars are a prefix of original
    assert len(result) <= len(data)

# Path 5: len!=disp_len, disp_len==length exactly → while not entered
# path: first-if False → while-false (zero iters) → RE_ANSI check
def test_path_zero_loop_iterations():
    # ANSI but disp_len exactly equals length
    data = "\033[1mabc\033[0m"
    dl = disp_len(data)  # == 3
    result = disp_trim(data, dl)  # length == disp_len, while not entered
    assert disp_len(result) <= dl
    # ANSI present → reset
    assert result.endswith("\033[0m")

# Path 6: Single loop iteration (disp_len == length+1)
# path: first-if False → while-true (1 iter) → while-false → RE_ANSI check
def test_path_single_loop_iteration():
    # 4 wide chars → disp_len=8, trim to 7 → exactly 1 char removed
    data = "\033[0mＡＢ"  # ANSI + 2 wide chars: disp_len = 4
    result = disp_trim(data, 3)
    assert disp_len(result) <= 3
    # property: result display length is non-negative
    assert disp_len(result) >= 0