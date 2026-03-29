import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from black import Line
from blib2to3.pgen2 import token
from blib2to3.pytree import Leaf, Node
import black
from black import syms, CLOSING_BRACKETS

# Helper to create a mock Leaf


def make_leaf(type_, value="x", bracket_depth=0, parent=None, opening_bracket=None):
    leaf = MagicMock(spec=Leaf)
    leaf.type = type_
    leaf.value = value
    leaf.bracket_depth = bracket_depth
    leaf.parent = parent
    leaf.opening_bracket = opening_bracket
    return leaf


def make_line(leaves=None, is_import=False):
    """Create a mock Line instance with mocked internals."""
    line = MagicMock(spec=Line)
    line.leaves = leaves if leaves is not None else []
    type(line).is_import = PropertyMock(return_value=is_import)
    line.remove_trailing_comma = MagicMock()
    # Bind the real method to our mock instance
    line.maybe_remove_trailing_comma = lambda closing: Line.maybe_remove_trailing_comma(line, closing)
    return line


# --- ECP ---

# ECP: No leaves at all — should return False
def test_ecp_no_leaves():
    closing = make_leaf(token.RBRACE)
    line = make_line(leaves=[])
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# ECP: Last leaf is not a comma — should return False
def test_ecp_last_leaf_not_comma():
    non_comma = make_leaf(token.NAME, "x")
    closing = make_leaf(token.RBRACE)
    line = make_line(leaves=[non_comma])
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# ECP: Closing is not a closing bracket type — should return False
def test_ecp_closing_not_bracket():
    comma = make_leaf(token.COMMA, ",")
    # Use a type not in CLOSING_BRACKETS
    closing = make_leaf(token.NAME, "x")
    assert closing.type not in CLOSING_BRACKETS
    line = make_line(leaves=[comma])
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# ECP: closing is RBRACE — always remove and return True
def test_ecp_rbrace_removes_comma():
    comma = make_leaf(token.COMMA, ",")
    closing = make_leaf(token.RBRACE, "}")
    line = make_line(leaves=[comma])
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# ECP: closing is RSQB with listmaker parent — remove and return True
def test_ecp_rsqb_with_listmaker_parent():
    parent_node = MagicMock()
    parent_node.type = syms.listmaker
    comma = make_leaf(token.COMMA, ",")
    comma.parent = parent_node
    closing = make_leaf(token.RSQB, "]")
    line = make_line(leaves=[comma])
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# ECP: closing is RSQB without listmaker parent — should NOT remove (falls through to paren logic)
def test_ecp_rsqb_no_listmaker_parent():
    parent_node = MagicMock()
    parent_node.type = syms.atom  # not listmaker
    comma = make_leaf(token.COMMA, ",")
    comma.parent = parent_node
    closing = make_leaf(token.RSQB, "]")
    line = make_line(leaves=[comma])
    # No opening bracket found in leaves => for/else returns False
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# ECP: closing is RSQB with no parent — should NOT remove
def test_ecp_rsqb_comma_no_parent():
    comma = make_leaf(token.COMMA, ",")
    comma.parent = None
    closing = make_leaf(token.RSQB, "]")
    line = make_line(leaves=[comma])
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# ECP: is_import=True with RPAR — always remove
def test_ecp_import_removes_comma():
    comma = make_leaf(token.COMMA, ",")
    closing = make_leaf(token.RPAR, ")")
    line = make_line(leaves=[comma], is_import=True)
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# ECP: RPAR, not import, only one comma at depth — protect tuple, return False
def test_ecp_rpar_single_comma_no_remove():
    # Build: opening_paren, elem, comma(trailing), closing_rpar
    # The opening bracket must be found in leaves
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    elem = make_leaf(token.NAME, "x", bracket_depth=1)
    comma = make_leaf(token.COMMA, ",", bracket_depth=1)

    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    comma.parent = None

    line = make_line(leaves=[opening, elem, comma], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# ECP: RPAR, not import, multiple commas at depth — remove trailing comma
def test_ecp_rpar_multiple_commas_remove():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    elem1 = make_leaf(token.NAME, "a", bracket_depth=1)
    mid_comma = make_leaf(token.COMMA, ",", bracket_depth=1)
    mid_comma.parent = None
    elem2 = make_leaf(token.NAME, "b", bracket_depth=1)
    trailing_comma = make_leaf(token.COMMA, ",", bracket_depth=1)
    trailing_comma.parent = None

    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening

    line = make_line(leaves=[opening, elem1, mid_comma, elem2, trailing_comma], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# --- BVA ---

# BVA: exactly 1 leaf (the comma itself) + RBRACE — boundary of minimum leaves
def test_bva_single_leaf_comma_rbrace():
    comma = make_leaf(token.COMMA, ",")
    closing = make_leaf(token.RBRACE, "}")
    line = make_line(leaves=[comma])
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# BVA: opening bracket not found in leaves — for/else triggers return False
def test_bva_opening_not_in_leaves():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    comma = make_leaf(token.COMMA, ",")
    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0
    # opening_bracket points to `opening` but `opening` is NOT in leaves
    closing.opening_bracket = opening

    line = make_line(leaves=[comma], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# BVA: exactly 2 commas at correct depth (boundary of commas > 1)
def test_bva_exactly_two_commas_at_depth():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    a = make_leaf(token.NAME, "a", bracket_depth=1)
    c1 = make_leaf(token.COMMA, ",", bracket_depth=1)
    c1.parent = None
    b = make_leaf(token.NAME, "b", bracket_depth=1)
    c2 = make_leaf(token.COMMA, ",", bracket_depth=1)
    c2.parent = None

    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening

    line = make_line(leaves=[opening, a, c1, b, c2], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    # commas == 2 > 1, should remove
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# BVA: exactly 1 comma at correct depth (boundary: commas == 1, NOT > 1)
def test_bva_exactly_one_comma_at_depth_no_remove():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    a = make_leaf(token.NAME, "a", bracket_depth=1)
    c1 = make_leaf(token.COMMA, ",", bracket_depth=1)
    c1.parent = None

    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening

    line = make_line(leaves=[opening, a, c1], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    # commas == 1, NOT > 1 => do not remove
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# BVA: comma at wrong bracket_depth — should not be counted
def test_bva_comma_at_wrong_depth_not_counted():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    # Two commas but at depth 2, not depth 1 (closing.bracket_depth+1=1)
    a = make_leaf(token.NAME, "a", bracket_depth=2)
    c1 = make_leaf(token.COMMA, ",", bracket_depth=2)
    c1.parent = None
    b = make_leaf(token.NAME, "b", bracket_depth=2)
    c2 = make_leaf(token.COMMA, ",", bracket_depth=2)
    c2.parent = None

    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0  # depth = 0 + 1 = 1, but commas are at 2
    closing.opening_bracket = opening

    line = make_line(leaves=[opening, a, c1, b, c2], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    # commas at depth==1 not found => commas==0, not > 1
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# BVA: leaves has many items but last is not comma — return False immediately
def test_bva_many_leaves_last_not_comma():
    leaves = [make_leaf(token.COMMA, ",")] * 10 + [make_leaf(token.NAME, "x")]
    closing = make_leaf(token.RBRACE, "}")
    line = make_line(leaves=leaves)
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# --- Mutation Detection ---

# MUTATION: `self.leaves[-1].type == token.COMMA` changed to `!=`
# With a comma as last leaf and RBRACE, a correct impl returns True
def test_mutation_last_leaf_must_be_comma_checked():
    comma = make_leaf(token.COMMA, ",")
    closing = make_leaf(token.RBRACE, "}")
    line = make_line(leaves=[comma])
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True  # detects mutation: if COMMA check is inverted, returns False


# MUTATION: `closing.type in CLOSING_BRACKETS` changed to `not in`
# A non-closing bracket should return False; a closing bracket should proceed
def test_mutation_closing_must_be_in_closing_brackets():
    comma = make_leaf(token.COMMA, ",")
    # RPAR is in CLOSING_BRACKETS
    closing_valid = make_leaf(token.RPAR, ")")
    closing_valid.bracket_depth = 0
    opening = make_leaf(token.LPAR, "(")
    closing_valid.opening_bracket = opening
    line1 = make_line(leaves=[comma], is_import=True)
    result1 = line1.maybe_remove_trailing_comma(closing_valid)
    assert result1 is True  # closing is in CLOSING_BRACKETS

    # A non-closing type
    closing_invalid = make_leaf(token.NAME, "x")
    line2 = make_line(leaves=[make_leaf(token.COMMA, ",")])
    result2 = line2.maybe_remove_trailing_comma(closing_invalid)
    assert result2 is False  # not in CLOSING_BRACKETS


# MUTATION: `commas > 1` changed to `commas >= 1` or `commas > 0`
# When commas == 1, should NOT remove (protects single-element tuple)
def test_mutation_commas_greater_than_one_not_geq():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    a = make_leaf(token.NAME, "a", bracket_depth=1)
    only_comma = make_leaf(token.COMMA, ",", bracket_depth=1)
    only_comma.parent = None

    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening

    line = make_line(leaves=[opening, a, only_comma], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    # commas == 1; correct impl: 1 > 1 is False => do NOT remove
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# MUTATION: arglist parent doubles the comma count — detects if that branch is removed
def test_mutation_arglist_parent_increments_commas():
    # With arglist parent on mid-comma, one real comma becomes 2 => triggers remove
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    a = make_leaf(token.NAME, "a", bracket_depth=1)

    arglist_parent = MagicMock()
    arglist_parent.type = syms.arglist

    c1 = make_leaf(token.COMMA, ",", bracket_depth=1)
    c1.parent = arglist_parent  # arglist parent => commas += 2 total

    trailing = make_leaf(token.COMMA, ",", bracket_depth=1)
    trailing.parent = None

    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening

    line = make_line(leaves=[opening, a, c1, trailing], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    # arglist branch: commas becomes 2 after first arglist comma, breaks, commas > 1 => True
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# MUTATION: `self.is_import` check flipped to `not self.is_import`
def test_mutation_is_import_true_removes():
    comma = make_leaf(token.COMMA, ",")
    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = MagicMock()

    line = make_line(leaves=[comma], is_import=True)
    result = line.maybe_remove_trailing_comma(closing)
    # A correct impl: is_import=True => remove and return True
    assert result is True
    line.remove_trailing_comma.assert_called_once()


def test_mutation_is_import_false_does_not_short_circuit():
    # is_import=False should NOT remove via the import branch
    # (will fall through to opening-not-found => False)
    comma = make_leaf(token.COMMA, ",")
    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0
    # opening_bracket not in leaves
    closing.opening_bracket = make_leaf(token.LPAR, "(")

    line = make_line(leaves=[comma], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False


# MUTATION: `closing.type == token.RBRACE` branch — if changed to RSQB
def test_mutation_rbrace_branch_distinct_from_rsqb():
    comma = make_leaf(token.COMMA, ",")
    rbrace_closing = make_leaf(token.RBRACE, "}")
    line = make_line(leaves=[comma])
    result = line.maybe_remove_trailing_comma(rbrace_closing)
    # RBRACE => unconditional remove
    assert result is True
    line.remove_trailing_comma.assert_called_once()

    # RSQB without listmaker parent should NOT unconditionally remove
    comma2 = make_leaf(token.COMMA, ",")
    comma2.parent = None
    rsqb_closing = make_leaf(token.RSQB, "]")
    line2 = make_line(leaves=[comma2])
    result2 = line2.maybe_remove_trailing_comma(rsqb_closing)
    # no listmaker parent => falls through => False (opening not in leaves)
    assert result2 is False


# MUTATION: depth computation `closing.bracket_depth + 1` changed to `closing.bracket_depth`
# Commas are at bracket_depth == closing.bracket_depth + 1
def test_mutation_depth_off_by_one():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    a = make_leaf(token.NAME, "a", bracket_depth=1)
    c1 = make_leaf(token.COMMA, ",", bracket_depth=1)  # at depth 1 = closing.bracket_depth+1
    c1.parent = None
    b = make_leaf(token.NAME, "b", bracket_depth=1)
    c2 = make_leaf(token.COMMA, ",", bracket_depth=1)
    c2.parent = None

    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0  # depth = 0 + 1 = 1
    closing.opening_bracket = opening

    line = make_line(leaves=[opening, a, c1, b, c2], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    # commas at depth 1 == 0+1, so commas=2 > 1 => True
    assert result is True
    # If depth were 0 (off-by-one), commas at depth 1 wouldn't match depth 0 => False
    line.remove_trailing_comma.assert_called_once()


# MUTATION: for/else — if `else` removed, `_opening_index` might be undefined
def test_mutation_for_else_opening_not_found_returns_false():
    # opening_bracket is not any of the leaves
    foreign_opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    comma = make_leaf(token.COMMA, ",")
    other_leaf = make_leaf(token.NAME, "y")

    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = foreign_opening  # not in leaves

    line = make_line(leaves=[other_leaf, comma], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    # Correct impl: opening not found => for/else triggers => return False
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# MUTATION: `_opening_index + 1` changed to `_opening_index` (off-by-one in slice)
# If slice starts at opening itself, and opening.type != COMMA, still no extra commas counted
# Test: ensure the opening leaf itself is not counted as a comma
def test_mutation_opening_index_slice_excludes_opening():
    # Put opening at index 0, then commas — if slice starts at 0 (wrong), opening's bracket_depth matters
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    # Give opening a COMMA type to catch mutation (it shouldn't be counted)
    opening_as_comma = MagicMock(spec=Leaf)
    opening_as_comma.type = token.LPAR  # it is the opening bracket, NOT a comma
    opening_as_comma.bracket_depth = 1

    a = make_leaf(token.NAME, "a", bracket_depth=1)
    only_comma = make_leaf(token.COMMA, ",", bracket_depth=1)
    only_comma.parent = None

    closing = make_leaf(token.RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening_as_comma

    line = make_line(leaves=[opening_as_comma, a, only_comma], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    # Only one comma at correct depth => commas==1 => NOT > 1 => False
    assert result is False
    line.remove_trailing_comma.assert_not_called()