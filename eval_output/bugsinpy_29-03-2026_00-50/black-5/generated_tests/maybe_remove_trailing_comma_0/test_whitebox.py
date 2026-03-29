from black import Line, BracketTracker
from blib2to3.pygram import python_grammar_no_print_statement as grammar
from blib2to3.pgen2 import token
from blib2to3.pytree import Leaf, Node
from unittest.mock import MagicMock, patch, PropertyMock
import pytest
from black import Line

# Helper to create a minimal mock Leaf
def make_leaf(token_type, value, bracket_depth=0, parent=None, opening_bracket=None):
    leaf = MagicMock(spec=Leaf)
    leaf.type = token_type
    leaf.value = value
    leaf.bracket_depth = bracket_depth
    leaf.parent = parent
    leaf.opening_bracket = opening_bracket
    return leaf


def make_line_with_leaves(leaves, is_import=False):
    """Create a Line instance and inject leaves + is_import."""
    line = Line()
    line.leaves = leaves
    # Patch is_import as a property
    type(line).is_import = PropertyMock(return_value=is_import)
    line.remove_trailing_comma = MagicMock()
    return line


# We need syms for listmaker/arglist checks
try:
    from blib2to3.pygram import python_grammar_no_print_statement
    from blib2to3.pgen2 import driver as pgen2_driver
    import black
    syms = black.syms
    CLOSING_BRACKETS = black.CLOSING_BRACKETS
    COMMA = token.COMMA
    RBRACE = token.RBRACE
    RSQB = token.RSQB
    RPAR = token.RPAR
except Exception:
    syms = None
    CLOSING_BRACKETS = None


# --- Statement Coverage ---

# SC1: leaves is empty → return False
# path: condition fails (no leaves) → return False
def test_sc_no_leaves_returns_false():
    line = Line()
    line.leaves = []
    line.remove_trailing_comma = MagicMock()
    closing = make_leaf(RBRACE, "}")
    # A correct implementation: no leaves → nothing to remove → False
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# SC2: last leaf is not COMMA → return False
# path: condition fails (not comma) → return False
def test_sc_last_leaf_not_comma_returns_false():
    non_comma = make_leaf(token.NAME, "x")
    line = make_line_with_leaves([non_comma])
    closing = make_leaf(RBRACE, "}")
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# SC3: closing not in CLOSING_BRACKETS → return False
# path: condition fails (closing not bracket) → return False
def test_sc_closing_not_bracket_returns_false():
    comma = make_leaf(COMMA, ",")
    line = make_line_with_leaves([comma])
    # Use a token type that is NOT in CLOSING_BRACKETS
    closing = make_leaf(token.NAME, "x")
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# SC4: closing is RBRACE → remove and return True
# path: leaves ok, closing==RBRACE → remove_trailing_comma → True
def test_sc_rbrace_removes_trailing_comma():
    comma = make_leaf(COMMA, ",")
    line = make_line_with_leaves([comma])
    closing = make_leaf(RBRACE, "}")
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# SC5: closing is RSQB, parent is listmaker → remove and return True
# path: RSQB branch, parent.type == listmaker → True
def test_sc_rsqb_listmaker_removes_trailing_comma():
    parent = MagicMock()
    parent.type = syms.listmaker
    comma = make_leaf(COMMA, ",", parent=parent)
    line = make_line_with_leaves([comma])
    closing = make_leaf(RSQB, "]")
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# SC6: closing is RSQB, parent is NOT listmaker → fall through to is_import check
# path: RSQB branch, parent.type != listmaker → falls through
def test_sc_rsqb_not_listmaker_falls_through_to_import():
    parent = MagicMock()
    parent.type = 9999  # not listmaker
    comma = make_leaf(COMMA, ",", parent=parent)
    line = make_line_with_leaves([comma], is_import=True)
    closing = make_leaf(RSQB, "]")
    result = line.maybe_remove_trailing_comma(closing)
    # is_import=True → should remove and return True
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# SC7: is_import → remove and return True
# path: RPAR-like closing, is_import=True → True
def test_sc_is_import_removes_trailing_comma():
    comma = make_leaf(COMMA, ",")
    line = make_line_with_leaves([comma], is_import=True)
    closing = make_leaf(RPAR, ")")
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# SC8: opening bracket not found in leaves → return False (for-else branch)
# path: RPAR, not import, opening not in leaves → for-else → False
def test_sc_opening_not_found_returns_false():
    comma = make_leaf(COMMA, ",")
    opening = make_leaf(RPAR, "(")  # opening that is NOT in leaves
    closing = make_leaf(RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening  # opening not in line.leaves
    line = make_line_with_leaves([comma], is_import=False)
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# SC9: commas > 1 → remove and return True
# path: RPAR, not import, opening found, commas > 1 → True
def test_sc_multiple_commas_removes_trailing_comma():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    depth = 1  # closing.bracket_depth + 1 = 0 + 1

    comma1 = make_leaf(COMMA, ",", bracket_depth=depth, parent=None)
    comma2 = make_leaf(COMMA, ",", bracket_depth=depth, parent=None)  # trailing
    line = make_line_with_leaves([opening, comma1, comma2], is_import=False)

    closing = make_leaf(RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# SC10: commas <= 1 (only trailing comma) → return False
# path: RPAR, not import, opening found, commas==0 → False
def test_sc_single_comma_returns_false():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    depth = 1
    trailing_comma = make_leaf(COMMA, ",", bracket_depth=depth, parent=None)
    # trailing_comma is the last leaf; inner loop sees closing first
    line = make_line_with_leaves([opening, trailing_comma], is_import=False)

    closing = make_leaf(RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# --- Block Coverage ---

# BC1: RSQB branch, comma.parent is None → no remove, falls through
# path: RSQB, parent is None → skip remove → fall through
def test_bc_rsqb_no_parent_falls_through():
    comma = make_leaf(COMMA, ",", parent=None)
    line = make_line_with_leaves([comma], is_import=False)
    closing = make_leaf(RSQB, "]")
    # Opening not in leaves → for-else → False
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False


# BC2: arglist parent causes early commas break
# path: RPAR, not import, opening found, leaf is comma with arglist parent → commas+=2 → break → remove
def test_bc_arglist_parent_causes_double_count():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    depth = 1
    parent = MagicMock()
    parent.type = syms.arglist
    # One comma that has arglist parent → commas becomes 2 → remove
    comma_inner = make_leaf(COMMA, ",", bracket_depth=depth, parent=parent)
    trailing_comma = make_leaf(COMMA, ",", bracket_depth=depth, parent=None)
    line = make_line_with_leaves([opening, comma_inner, trailing_comma], is_import=False)

    closing = make_leaf(RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True
    line.remove_trailing_comma.assert_called_once()


# BC3: leaf at different bracket_depth is skipped (not counted as comma)
def test_bc_comma_at_different_depth_not_counted():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    depth = 1
    # comma at depth 2 (nested) should NOT be counted
    nested_comma = make_leaf(COMMA, ",", bracket_depth=2, parent=None)
    trailing_comma = make_leaf(COMMA, ",", bracket_depth=depth, parent=None)
    line = make_line_with_leaves([opening, nested_comma, trailing_comma], is_import=False)

    closing = make_leaf(RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    # Only trailing comma counted (but it IS the closing leaf? No, closing is separate)
    # nested_comma has wrong depth → 0 commas counted → False
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False
    line.remove_trailing_comma.assert_not_called()


# --- Condition Coverage ---
# Condition: self.leaves AND self.leaves[-1].type == COMMA AND closing.type in CLOSING_BRACKETS

# CC1: self.leaves is empty (False), last-type irrelevant, closing in brackets (True)
# self.leaves: False, leaves[-1].type==COMMA: N/A, closing in CLOSING_BRACKETS: True
def test_cc_leaves_false():
    line = Line()
    line.leaves = []
    line.remove_trailing_comma = MagicMock()
    closing = make_leaf(RBRACE, "}")
    assert line.maybe_remove_trailing_comma(closing) is False  # leaves: False

# CC2: self.leaves non-empty (True), last leaf IS comma (True), closing NOT in brackets (False)
# self.leaves: True, leaves[-1].type==COMMA: True, closing in CLOSING_BRACKETS: False
def test_cc_closing_not_in_brackets_false():
    comma = make_leaf(COMMA, ",")
    line = make_line_with_leaves([comma])
    closing = make_leaf(token.NAME, "x")  # not in CLOSING_BRACKETS
    assert line.maybe_remove_trailing_comma(closing) is False

# CC3: self.leaves non-empty (True), last leaf NOT comma (False), closing in brackets (True)
# self.leaves: True, leaves[-1].type==COMMA: False, closing in CLOSING_BRACKETS: True
def test_cc_last_leaf_not_comma_false():
    name = make_leaf(token.NAME, "x")
    line = make_line_with_leaves([name])
    closing = make_leaf(RBRACE, "}")
    assert line.maybe_remove_trailing_comma(closing) is False

# CC4: all three sub-conditions True → enters the function body
# self.leaves: True, leaves[-1].type==COMMA: True, closing in CLOSING_BRACKETS: True
def test_cc_all_conditions_true():
    comma = make_leaf(COMMA, ",")
    line = make_line_with_leaves([comma])
    closing = make_leaf(RBRACE, "}")
    assert line.maybe_remove_trailing_comma(closing) is True

# Condition: closing.type == token.RBRACE
# CC5: closing.type == RBRACE → True (covered by test_sc_rbrace_removes_trailing_comma)
# CC6: closing.type != RBRACE (RSQB) → False, enters RSQB block
def test_cc_closing_not_rbrace():
    parent = MagicMock()
    parent.type = syms.listmaker
    comma = make_leaf(COMMA, ",", parent=parent)
    line = make_line_with_leaves([comma])
    closing = make_leaf(RSQB, "]")
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True  # takes RSQB path, not RBRACE

# Condition: closing.type == token.RSQB
# CC7: closing.type == RSQB → True (covered above)
# CC8: closing.type != RSQB (RPAR) → False, falls to import check
def test_cc_closing_not_rsqb():
    comma = make_leaf(COMMA, ",")
    line = make_line_with_leaves([comma], is_import=True)
    closing = make_leaf(RPAR, ")")
    result = line.maybe_remove_trailing_comma(closing)
    assert result is True  # takes is_import path

# Condition: comma.parent AND comma.parent.type == syms.listmaker
# CC9: parent is None (False) → skip listmaker block
def test_cc_rsqb_parent_none():
    comma = make_leaf(COMMA, ",", parent=None)
    line = make_line_with_leaves([comma], is_import=False)
    closing = make_leaf(RSQB, "]")
    # No opening in leaves → for-else → False
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False

# CC10: parent exists (True), type NOT listmaker (False) → skip listmaker block
def test_cc_rsqb_parent_not_listmaker():
    parent = MagicMock()
    parent.type = 9999
    comma = make_leaf(COMMA, ",", parent=parent)
    line = make_line_with_leaves([comma], is_import=True)
    closing = make_leaf(RSQB, "]")
    result = line.maybe_remove_trailing_comma(closing)
    # falls through to is_import=True → True
    assert result is True

# Condition: self.is_import → True/False
# CC11: is_import True (covered by test_sc_is_import_removes_trailing_comma)
# CC12: is_import False → proceeds to bracket depth analysis
def test_cc_not_import_proceeds_to_depth_analysis():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    depth = 1
    comma1 = make_leaf(COMMA, ",", bracket_depth=depth)
    comma2 = make_leaf(COMMA, ",", bracket_depth=depth)
    line = make_line_with_leaves([opening, comma1, comma2], is_import=False)
    closing = make_leaf(RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    result = line.maybe_remove_trailing_comma(closing)
    # commas > 1 → True
    assert result is True

# Condition: bracket_depth == depth AND leaf.type == token.COMMA
# CC13: bracket_depth != depth → leaf not counted (covered by test_bc_comma_at_different_depth_not_counted)
# CC14: bracket_depth == depth but not COMMA → leaf not counted
def test_cc_right_depth_wrong_type():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    depth = 1
    name = make_leaf(token.NAME, "x", bracket_depth=depth)
    trailing_comma = make_leaf(COMMA, ",", bracket_depth=depth)
    line = make_line_with_leaves([opening, name, trailing_comma], is_import=False)
    closing = make_leaf(RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    # name not counted, commas=0, only trailing (which breaks when leaf is closing)
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False

# Condition: leaf.parent AND leaf.parent.type == syms.arglist
# CC15: parent None → no double count (covered in test_sc_multiple_commas_removes_trailing_comma path)
# CC16: parent exists, type IS arglist → double count and break (covered by test_bc_arglist_parent_causes_double_count)

# Condition: commas > 1
# CC17: commas > 1 → True (covered by test_sc_multiple_commas_removes_trailing_comma)
# CC18: commas <= 1 → False (covered by test_sc_single_comma_returns_false)


# --- Path Coverage ---

# PATH 1: no leaves → False
# path: guard-condition-fails(empty) → return False
def test_path_empty_leaves():
    # Covered by test_sc_no_leaves_returns_false, noted here
    line = Line()
    line.leaves = []
    line.remove_trailing_comma = MagicMock()
    closing = make_leaf(RBRACE, "}")
    assert line.maybe_remove_trailing_comma(closing) is False

# PATH 2: leaves present, last not COMMA → False
# path: guard-condition-fails(not-comma) → return False
def test_path_last_not_comma():
    name = make_leaf(token.NAME, "x")
    line = make_line_with_leaves([name])
    closing = make_leaf(RBRACE, "}")
    assert line.maybe_remove_trailing_comma(closing) is False

# PATH 3: comma present, closing not bracket → False
# path: guard-condition-fails(not-bracket) → return False
def test_path_not_closing_bracket():
    comma = make_leaf(COMMA, ",")
    line = make_line_with_leaves([comma])
    closing = make_leaf(token.NAME, "x")
    assert line.maybe_remove_trailing_comma(closing) is False

# PATH 4: RBRACE → remove → True
# path: guard-pass → RBRACE-true → remove → True
def test_path_rbrace():
    comma = make_leaf(COMMA, ",")
    line = make_line_with_leaves([comma])
    closing = make_leaf(RBRACE, "}")
    assert line.maybe_remove_trailing_comma(closing) is True
    line.remove_trailing_comma.assert_called_once()

# PATH 5: RSQB + listmaker → remove → True
# path: guard-pass → RBRACE-false → RSQB-true → parent-listmaker-true → remove → True
def test_path_rsqb_listmaker():
    parent = MagicMock()
    parent.type = syms.listmaker
    comma = make_leaf(COMMA, ",", parent=parent)
    line = make_line_with_leaves([comma])
    closing = make_leaf(RSQB, "]")
    assert line.maybe_remove_trailing_comma(closing) is True
    line.remove_trailing_comma.assert_called_once()

# PATH 6: RSQB + parent None → fall through → is_import True → remove → True
# path: guard-pass → RBRACE-false → RSQB-true → parent-None → is_import-true → remove → True
def test_path_rsqb_no_parent_is_import():
    comma = make_leaf(COMMA, ",", parent=None)
    line = make_line_with_leaves([comma], is_import=True)
    closing = make_leaf(RSQB, "]")
    assert line.maybe_remove_trailing_comma(closing) is True
    line.remove_trailing_comma.assert_called_once()

# PATH 7: RPAR + is_import → remove → True
# path: guard-pass → RBRACE-false → RSQB-false → is_import-true → remove → True
def test_path_rpar_import():
    comma = make_leaf(COMMA, ",")
    line = make_line_with_leaves([comma], is_import=True)
    closing = make_leaf(RPAR, ")")
    assert line.maybe_remove_trailing_comma(closing) is True
    line.remove_trailing_comma.assert_called_once()

# PATH 8: RPAR + not import + opening not in leaves → for-else → False
# path: guard-pass → RBRACE-false → RSQB-false → is_import-false → first-loop-exhausted → False
def test_path_rpar_not_import_no_opening():
    comma = make_leaf(COMMA, ",")
    opening = make_leaf(token.LPAR, "(")  # NOT added to leaves
    line = make_line_with_leaves([comma], is_import=False)
    closing = make_leaf(RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    assert line.maybe_remove_trailing_comma(closing) is False
    line.remove_trailing_comma.assert_not_called()

# PATH 9: RPAR + not import + opening found + commas > 1 → remove → True
# path: guard-pass → RBRACE-false → RSQB-false → is_import-false → first-loop-found → second-loop → commas>1 → remove → True
def test_path_rpar_not_import_multiple_commas():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    depth = 1
    c1 = make_leaf(COMMA, ",", bracket_depth=depth)
    c2 = make_leaf(COMMA, ",", bracket_depth=depth)
    line = make_line_with_leaves([opening, c1, c2], is_import=False)
    closing = make_leaf(RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    assert line.maybe_remove_trailing_comma(closing) is True
    line.remove_trailing_comma.assert_called_once()

# PATH 10: RPAR + not import + opening found + commas <= 1 → False
# path: guard-pass → RBRACE-false → RSQB-false → is_import-false → first-loop-found → second-loop → commas<=1 → False
def test_path_rpar_not_import_single_comma():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    depth = 1
    trailing = make_leaf(COMMA, ",", bracket_depth=depth)
    line = make_line_with_leaves([opening, trailing], is_import=False)
    closing = make_leaf(RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    # The second loop breaks on closing (or on trailing if it equals closing)
    # trailing is last leaf, closing is a separate object
    # loop from _opening_index+1: sees trailing (depth==depth, type==COMMA → commas=1), then no closing leaf → loop ends
    assert line.maybe_remove_trailing_comma(closing) is False
    line.remove_trailing_comma.assert_not_called()

# PATH 11: arglist parent → commas incremented twice → break → remove → True
# path: ... → second-loop → comma-at-depth → arglist-parent → commas+=2 → break → commas>1 → True
def test_path_arglist_double_increment():
    opening = make_leaf(token.LPAR, "(", bracket_depth=0)
    depth = 1
    parent = MagicMock()
    parent.type = syms.arglist
    c_arglist = make_leaf(COMMA, ",", bracket_depth=depth, parent=parent)
    trailing = make_leaf(COMMA, ",", bracket_depth=depth)
    line = make_line_with_leaves([opening, c_arglist, trailing], is_import=False)
    closing = make_leaf(RPAR, ")")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    assert line.maybe_remove_trailing_comma(closing) is True
    line.remove_trailing_comma.assert_called_once()

# PATH 12: RSQB + parent not listmaker + not import + opening not found → False
# path: guard-pass → RBRACE-false → RSQB-true → parent-not-listmaker → is_import-false → first-loop-exhausted → False
def test_path_rsqb_not_listmaker_not_import_no_opening():
    parent = MagicMock()
    parent.type = 9999
    comma = make_leaf(COMMA, ",", parent=parent)
    opening = make_leaf(token.LSQB, "[")  # NOT in leaves
    line = make_line_with_leaves([comma], is_import=False)
    closing = make_leaf(RSQB, "]")
    closing.bracket_depth = 0
    closing.opening_bracket = opening
    result = line.maybe_remove_trailing_comma(closing)
    assert result is False