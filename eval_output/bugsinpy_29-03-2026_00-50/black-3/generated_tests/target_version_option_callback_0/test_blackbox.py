import pytest
from unittest.mock import MagicMock
from typing import Tuple, List
import click

from black import target_version_option_callback, TargetVersion

# Helper to create mock context and parameter (not part of logic under test)
def make_ctx_and_param():
    ctx = MagicMock(spec=click.Context)
    param = MagicMock(spec=click.Option)
    return ctx, param


# --- BVA ---

def test_bva_empty_tuple():
    """BVA: empty tuple (min collection size) should return empty list."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ())
    assert result == []
    assert isinstance(result, list)


def test_bva_single_element():
    """BVA: single element tuple (min+1 size) should return a list with one TargetVersion."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ("py36",))
    assert len(result) == 1
    assert result[0] == TargetVersion.PY36


def test_bva_two_elements():
    """BVA: two-element tuple should return exactly two TargetVersion entries."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ("py36", "py37"))
    assert len(result) == 2
    assert TargetVersion.PY36 in result
    assert TargetVersion.PY37 in result


def test_bva_all_valid_versions():
    """BVA: large input — all valid TargetVersion names — should return all members."""
    ctx, param = make_ctx_and_param()
    all_names = tuple(v.name.lower() for v in TargetVersion)
    result = target_version_option_callback(ctx, param, all_names)
    assert len(result) == len(TargetVersion)
    assert set(result) == set(TargetVersion)


def test_bva_invalid_version_string():
    """BVA: a version string that is not a valid TargetVersion name should raise KeyError."""
    ctx, param = make_ctx_and_param()
    with pytest.raises(KeyError):
        target_version_option_callback(ctx, param, ("py999",))


# --- ECP ---

def test_ecp_valid_lowercase():
    """ECP valid class: lowercase version string is a valid representative input."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ("py38",))
    assert result == [TargetVersion.PY38]


def test_ecp_valid_uppercase():
    """ECP valid class: uppercase version string should also work (uppercased internally)."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ("PY38",))
    assert result == [TargetVersion.PY38]


def test_ecp_valid_mixed_case():
    """ECP valid class: mixed-case version string should be normalized to uppercase."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ("Py38",))
    assert result == [TargetVersion.PY38]


def test_ecp_invalid_empty_string():
    """ECP invalid class: empty string is not a valid TargetVersion name."""
    ctx, param = make_ctx_and_param()
    with pytest.raises(KeyError):
        target_version_option_callback(ctx, param, ("",))


def test_ecp_invalid_numeric_string():
    """ECP invalid class: numeric-only string is not a valid TargetVersion name."""
    ctx, param = make_ctx_and_param()
    with pytest.raises(KeyError):
        target_version_option_callback(ctx, param, ("38",))


def test_ecp_invalid_garbage_string():
    """ECP invalid class: arbitrary garbage string should raise KeyError."""
    ctx, param = make_ctx_and_param()
    with pytest.raises(KeyError):
        target_version_option_callback(ctx, param, ("notaversion",))


def test_ecp_multiple_valid_versions():
    """ECP valid class: multiple distinct valid versions all processed correctly."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ("py36", "py37", "py38"))
    assert set(result) == {TargetVersion.PY36, TargetVersion.PY37, TargetVersion.PY38}
    assert len(result) == 3


def test_ecp_duplicate_valid_versions():
    """ECP valid class: duplicate version strings should both appear in output list."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ("py38", "py38"))
    # A correct implementation maps each input to a TargetVersion; duplicates are kept
    assert len(result) == 2
    assert all(v == TargetVersion.PY38 for v in result)


def test_ecp_mixed_valid_and_invalid():
    """ECP: mixing valid and invalid strings — should raise KeyError on the invalid one."""
    ctx, param = make_ctx_and_param()
    with pytest.raises(KeyError):
        target_version_option_callback(ctx, param, ("py38", "invalid_ver"))


# --- Mutation Detection ---

def test_mutation_upper_not_applied_catches_wrong_variable():
    """Mutation: if val.upper() were missing, 'py38' (lowercase) would fail lookup
    because TargetVersion enum keys are uppercase. This detects omission of .upper()."""
    ctx, param = make_ctx_and_param()
    # 'py38' is lowercase — a correct implementation converts to 'PY38' via .upper()
    result = target_version_option_callback(ctx, param, ("py38",))
    assert result == [TargetVersion.PY38]


def test_mutation_upper_with_uppercase_input():
    """Mutation: if .upper() were replaced with .lower() then 'PY38' would fail.
    Correct: upper-casing uppercase still yields 'PY38'."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ("PY38",))
    assert result == [TargetVersion.PY38]


def test_mutation_list_comprehension_not_set():
    """Mutation: if the comprehension returned a set instead of a list, len would
    still equal input length for distinct items, but type would differ."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ("py36", "py37"))
    # A correct implementation returns a list, not a set or tuple
    assert isinstance(result, list)


def test_mutation_order_preserved():
    """Mutation: if wrong iteration order were used, the result order would differ.
    A correct list comprehension preserves input order."""
    ctx, param = make_ctx_and_param()
    versions = ("py36", "py37", "py38")
    result = target_version_option_callback(ctx, param, versions)
    expected = [TargetVersion[v.upper()] for v in versions]
    assert result == expected


def test_mutation_length_matches_input():
    """Mutation: if the comprehension skipped elements (e.g. off-by-one on iteration),
    output length would differ. Correct: output length == input length."""
    ctx, param = make_ctx_and_param()
    v_tuple = ("py36", "py37", "py38", "py39") if hasattr(TargetVersion, "PY39") else ("py36", "py37", "py38")
    result = target_version_option_callback(ctx, param, v_tuple)
    assert len(result) == len(v_tuple)


def test_mutation_returns_target_version_instances():
    """Mutation: if wrong enum class were subscripted, items would not be TargetVersion.
    Correct: every element in the result is a TargetVersion instance."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ("py36", "py38"))
    assert all(isinstance(v, TargetVersion) for v in result)


def test_mutation_single_char_case_insensitivity():
    """Mutation: if case conversion used .lower() instead of .upper(), valid uppercase
    inputs would fail. Detect by passing uppercase and verifying correct result."""
    ctx, param = make_ctx_and_param()
    result = target_version_option_callback(ctx, param, ("PY36",))
    assert result == [TargetVersion.PY36]


def test_mutation_context_and_param_ignored():
    """Mutation: correct implementation uses only `v`; if ctx or param were accidentally
    used in place of `v`, results would be wrong. Verify with two different contexts."""
    ctx1, param1 = make_ctx_and_param()
    ctx2, param2 = make_ctx_and_param()
    result1 = target_version_option_callback(ctx1, param1, ("py38",))
    result2 = target_version_option_callback(ctx2, param2, ("py38",))
    # Both should produce same result regardless of context/param differences
    assert result1 == result2 == [TargetVersion.PY38]