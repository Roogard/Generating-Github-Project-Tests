import sys
import types
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from black import bracket_split_build_line, Line, normalize_prefix, should_explode
from blib2to3.pytree import Leaf
from blib2to3.pgen2 import token

# ---------------------------------------------------------------------------
# Helpers to build minimal real-ish objects
# ---------------------------------------------------------------------------

def make_leaf(token_type, value, prefix=""):
    leaf = Leaf(token_type, value)
    leaf.prefix = prefix
    return leaf


def make_original_line(depth=0, is_import=False, inside_brackets=False):
    """Create a real Line object with controlled properties."""
    line = Line(depth=depth)
    line.inside_brackets = inside_brackets
    # Patch is_import as a property via the instance's class dict isn't simple;
    # we use a subclass approach instead.
    if is_import:
        # Monkey-patch the instance to behave as an import line
        type(line).is_import = property(lambda self: True)
    return line


class FakeLine(Line):
    """Subclass of Line that lets us control is_import easily."""
    def __init__(self, depth=0, _is_import=False):
        super().__init__(depth=depth)
        self._is_import = _is_import

    @property
    def is_import(self):
        return self._is_import

    def comments_after(self, leaf):
        # Return no comments by default (real Line needs leaves appended first)
        return []


def make_opening_bracket():
    return make_leaf(token.LPAR, "(")


# ---------------------------------------------------------------------------
# Statement Coverage
# ---------------------------------------------------------------------------

# --- Statement Coverage ---

def test_sc_non_body_returns_line_with_correct_depth():
    """
    Non-body path: result.inside_brackets not set True, depth unchanged.
    Covers: result creation, populate loop, return.
    # path: is_body=False → populate loop → return
    """
    original = FakeLine(depth=2, _is_import=False)
    leaf = make_leaf(token.NAME, "x")
    opening = make_opening_bracket()

    result = bracket_split_build_line([leaf], original, opening, is_body=False)

    # A correct implementation should copy depth from original
    assert result.depth == 2
    # inside_brackets should NOT be set by non-body path
    assert result.inside_brackets == False


def test_sc_body_sets_inside_brackets_and_increments_depth():
    """
    is_body=True, leaves non-empty, not import.
    Covers: is_body branch, inside_brackets=True, depth+=1, normalize_prefix call.
    # path: is_body=True → leaves non-empty → not import → populate → should_explode → return
    """
    original = FakeLine(depth=1, _is_import=False)
    leaf = make_leaf(token.NAME, "x", prefix="   ")
    opening = make_opening_bracket()

    result = bracket_split_build_line([leaf], original, opening, is_body=True)

    assert result.inside_brackets == True
    assert result.depth == original.depth + 1


def test_sc_body_empty_leaves():
    """
    is_body=True, leaves=[] — the inner `if leaves:` block is skipped.
    Covers: is_body branch with empty leaves list.
    # path: is_body=True → leaves empty → skip normalize/import → populate (no-op) → should_explode → return
    """
    original = FakeLine(depth=0, _is_import=True)
    opening = make_opening_bracket()

    result = bracket_split_build_line([], original, opening, is_body=True)

    assert result.inside_brackets == True
    assert result.depth == 1


def test_sc_import_trailing_comma_inserted():
    """
    is_body=True, is_import=True, last leaf is NAME (not COMMA, not STANDALONE_COMMENT).
    Covers: import branch, reverse loop, else-branch (insert comma), break.
    # path: is_body → import → backward loop → else → insert comma → break → populate → return
    """
    original = FakeLine(depth=0, _is_import=True)
    leaf_a = make_leaf(token.NAME, "os")
    leaf_b = make_leaf(token.NAME, "sys")
    leaves = [leaf_a, leaf_b]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=True)

    # A correct implementation must ensure a trailing comma after the last non-comment leaf
    leaf_types = [l.type for l in leaves]
    assert token.COMMA in leaf_types
    # The comma should be the last leaf (or last before any comments)
    assert leaves[-1].type == token.COMMA


def test_sc_import_existing_comma_no_duplicate():
    """
    is_body=True, is_import=True, last leaf is already COMMA.
    Covers: the `elif leaves[i].type == token.COMMA: break` branch.
    # path: is_body → import → backward loop → elif COMMA → break → populate → return
    """
    original = FakeLine(depth=0, _is_import=True)
    leaf_a = make_leaf(token.NAME, "os")
    comma = make_leaf(token.COMMA, ",")
    leaves = [leaf_a, comma]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=True)

    # A correct implementation should NOT add a second comma
    commas = [l for l in leaves if l.type == token.COMMA]
    assert len(commas) == 1


# ---------------------------------------------------------------------------
# Block Coverage
# ---------------------------------------------------------------------------

# --- Block Coverage ---

def test_bc_standalone_comment_skipped_then_comma_inserted():
    """
    is_body=True, is_import=True, last leaf is STANDALONE_COMMENT, second-to-last is NAME.
    Covers: the `if leaves[i].type == STANDALONE_COMMENT: continue` block,
    then the `else: insert` block.
    # path: is_body → import → backward loop → STANDALONE_COMMENT continue → NAME else insert → break
    """
    from black import STANDALONE_COMMENT

    original = FakeLine(depth=0, _is_import=True)
    leaf_name = make_leaf(token.NAME, "pathlib")
    # STANDALONE_COMMENT is a special token value in black
    leaf_comment = Leaf(STANDALONE_COMMENT, "# a comment")
    leaves = [leaf_name, leaf_comment]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=True)

    # A correct implementation should insert comma before the comment
    # so the comma should appear before the standalone comment
    comma_idx = next((i for i, l in enumerate(leaves) if l.type == token.COMMA), None)
    comment_idx = next((i for i, l in enumerate(leaves) if l.type == STANDALONE_COMMENT), None)
    assert comma_idx is not None, "A trailing comma should have been inserted"
    assert comma_idx < comment_idx, "Comma should appear before the standalone comment"


def test_bc_non_body_no_inside_brackets():
    """
    is_body=False: the entire is_body block is skipped.
    Covers: the else-not-taken block explicitly.
    # path: is_body=False → skip all body blocks → populate → return (no should_explode)
    """
    original = FakeLine(depth=3, _is_import=False)
    opening = make_opening_bracket()

    result = bracket_split_build_line([], original, opening, is_body=False)

    assert result.depth == 3
    assert result.inside_brackets == False


def test_bc_populate_loop_multiple_leaves():
    """
    Populate loop executes multiple times.
    Covers: loop body block executed > 1 time.
    # path: populate loop → 3 iterations → return
    """
    original = FakeLine(depth=0, _is_import=False)
    leaves = [make_leaf(token.NAME, n) for n in ["a", "b", "c"]]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=False)

    # A correct implementation should include all leaves
    assert len(result.leaves) == 3


def test_bc_comments_after_appended():
    """
    Covers the inner loop: `for comment_after in original.comments_after(leaf)`.
    We subclass FakeLine to return a comment for one leaf.
    # path: populate → leaf with comment → inner loop executes → return
    """
    comment_leaf = make_leaf(token.COMMENT, "# hi")
    name_leaf = make_leaf(token.NAME, "foo")

    class LineWithComment(FakeLine):
        def comments_after(self, leaf):
            if leaf is name_leaf:
                return [comment_leaf]
            return []

    original = LineWithComment(depth=0, _is_import=False)
    opening = make_opening_bracket()

    result = bracket_split_build_line([name_leaf], original, opening, is_body=False)

    # A correct implementation should append both the leaf and its comment
    assert len(result.leaves) == 2


# ---------------------------------------------------------------------------
# Condition Coverage
# ---------------------------------------------------------------------------

# --- Condition Coverage ---

# Conditions:
# C1: `is_body` (True/False)
# C2: `leaves` (truthy/falsy — non-empty/empty)
# C3: `original.is_import` (True/False)
# C4: `leaves[i].type == STANDALONE_COMMENT` (True/False)
# C5: `leaves[i].type == token.COMMA` (True/False)

def test_cc_is_body_true_leaves_truthy_is_import_true():
    """
    # C1: True, C2: True, C3: True
    # C4: False (NAME leaf), C5: False → insert comma
    """
    original = FakeLine(depth=0, _is_import=True)
    leaves = [make_leaf(token.NAME, "foo")]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=True)

    assert result.inside_brackets == True
    assert token.COMMA in [l.type for l in leaves]


def test_cc_is_body_false():
    """
    # C1: False — is_body is False, entire body block skipped
    """
    original = FakeLine(depth=5, _is_import=True)
    leaves = [make_leaf(token.NAME, "bar")]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=False)

    # C1=False: inside_brackets not set, depth not incremented
    assert result.inside_brackets == False
    assert result.depth == 5


def test_cc_leaves_falsy():
    """
    # C1: True, C2: False (empty leaves)
    """
    original = FakeLine(depth=0, _is_import=True)
    opening = make_opening_bracket()

    result = bracket_split_build_line([], original, opening, is_body=True)

    # With no leaves, no comma manipulation happens
    assert result.inside_brackets == True
    assert len(result.leaves) == 0


def test_cc_is_import_false():
    """
    # C1: True, C2: True, C3: False — no comma logic runs
    """
    original = FakeLine(depth=0, _is_import=False)
    leaves = [make_leaf(token.NAME, "x")]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=True)

    # No comma should be added for non-import lines
    assert token.COMMA not in [l.type for l in leaves]


def test_cc_standalone_comment_true():
    """
    # C4: True — STANDALONE_COMMENT encountered, continue
    Then C4: False for next leaf, C5: False → insert
    """
    from black import STANDALONE_COMMENT

    original = FakeLine(depth=0, _is_import=True)
    name = make_leaf(token.NAME, "abc")
    comment = Leaf(STANDALONE_COMMENT, "# end")
    leaves = [name, comment]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=True)

    # C4=True triggered continue; C4=False, C5=False triggered insert
    comma_positions = [i for i, l in enumerate(leaves) if l.type == token.COMMA]
    assert len(comma_positions) == 1


def test_cc_comma_already_present():
    """
    # C4: False (COMMA leaf), C5: True — break without inserting
    """
    original = FakeLine(depth=0, _is_import=True)
    name = make_leaf(token.NAME, "abc")
    comma = make_leaf(token.COMMA, ",")
    leaves = [name, comma]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=True)

    # C5=True → break → no new comma inserted
    commas = [l for l in leaves if l.type == token.COMMA]
    assert len(commas) == 1


# ---------------------------------------------------------------------------
# Path Coverage
# ---------------------------------------------------------------------------

# --- Path Coverage ---

# Major paths:
# P1: is_body=False, no leaves → pure creation + populate (empty) + return
# P2: is_body=False, with leaves → creation + populate loop + return
# P3: is_body=True, empty leaves → body setup (no leaf processing) + populate + should_explode + return
# P4: is_body=True, non-empty leaves, not import → normalize + populate + should_explode + return
# P5: is_body=True, non-empty leaves, import, last=NAME → normalize + insert comma + populate + should_explode + return
# P6: is_body=True, non-empty leaves, import, last=COMMA → normalize + break (no insert) + populate + return
# P7: is_body=True, non-empty leaves, import, last=STANDALONE_COMMENT, prev=NAME → continue + insert + populate + return
# P8: is_body=True, non-empty leaves, import, last=STANDALONE_COMMENT, prev=COMMA → continue + break + populate + return

def test_p1_is_body_false_empty_leaves():
    """
    # path: is_body=False → skip body block → populate (0 iters) → return
    """
    original = FakeLine(depth=4, _is_import=False)
    opening = make_opening_bracket()

    result = bracket_split_build_line([], original, opening, is_body=False)

    assert result.depth == 4
    assert result.inside_brackets == False
    assert len(result.leaves) == 0


def test_p2_is_body_false_with_leaves():
    """
    # path: is_body=False → skip body block → populate (3 iters) → return
    """
    original = FakeLine(depth=1, _is_import=False)
    leaves = [make_leaf(token.NAME, v) for v in ["x", "y", "z"]]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=False)

    assert result.depth == 1
    assert len(result.leaves) == 3


def test_p3_is_body_true_empty_leaves():
    """
    # path: is_body=True → inside_brackets=True, depth+1 → leaves empty (skip inner) → populate (0) → should_explode → return
    """
    original = FakeLine(depth=2, _is_import=True)
    opening = make_opening_bracket()

    result = bracket_split_build_line([], original, opening, is_body=True)

    assert result.inside_brackets == True
    assert result.depth == 3
    assert len(result.leaves) == 0


def test_p4_is_body_true_not_import():
    """
    # path: is_body=True → inside_brackets=True, depth+1 → leaves non-empty → normalize_prefix → NOT import (skip comma logic) → populate → should_explode → return
    """
    original = FakeLine(depth=0, _is_import=False)
    leaf = make_leaf(token.NAME, "result", prefix="    ")
    opening = make_opening_bracket()

    result = bracket_split_build_line([leaf], original, opening, is_body=True)

    assert result.inside_brackets == True
    assert result.depth == 1
    # Correct impl must not add a comma for non-imports
    assert token.COMMA not in [l.type for l in result.leaves]


def test_p5_is_body_true_import_last_is_name():
    """
    # path: is_body=True → import → backward: NAME → else branch → insert comma → break → populate → return
    """
    original = FakeLine(depth=0, _is_import=True)
    leaves = [make_leaf(token.NAME, "sys"), make_leaf(token.NAME, "os")]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=True)

    # A correct impl should have appended a trailing comma
    assert leaves[-1].type == token.COMMA
    # Correct number of leaves in result (2 names + 1 comma)
    assert len(result.leaves) == 3


def test_p6_is_body_true_import_last_is_comma():
    """
    # path: is_body=True → import → backward: COMMA → elif branch → break (no insert) → populate → return
    """
    original = FakeLine(depth=0, _is_import=True)
    leaves = [make_leaf(token.NAME, "sys"), make_leaf(token.COMMA, ",")]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=True)

    commas = [l for l in result.leaves if l.type == token.COMMA]
    assert len(commas) == 1


def test_p7_is_body_true_import_standalone_then_name():
    """
    # path: is_body=True → import → backward: STANDALONE_COMMENT (continue) → NAME (else insert) → break → populate → return
    """
    from black import STANDALONE_COMMENT

    original = FakeLine(depth=0, _is_import=True)
    name = make_leaf(token.NAME, "json")
    comment = Leaf(STANDALONE_COMMENT, "# comment")
    leaves = [name, comment]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=True)

    # Comma inserted before the comment
    idx_comma = next((i for i, l in enumerate(leaves) if l.type == token.COMMA), None)
    idx_comment = next((i for i, l in enumerate(leaves) if l.type == STANDALONE_COMMENT), None)
    assert idx_comma is not None
    assert idx_comma < idx_comment


def test_p8_is_body_true_import_standalone_then_comma():
    """
    # path: is_body=True → import → backward: STANDALONE_COMMENT (continue) → COMMA (elif break) → populate → return
    """
    from black import STANDALONE_COMMENT

    original = FakeLine(depth=0, _is_import=True)
    name = make_leaf(token.NAME, "json")
    comma = make_leaf(token.COMMA, ",")
    comment = Leaf(STANDALONE_COMMENT, "# comment")
    leaves = [name, comma, comment]
    opening = make_opening_bracket()

    result = bracket_split_build_line(leaves, original, opening, is_body=True)

    # No additional comma should be inserted; still exactly one
    commas = [l for l in leaves if l.type == token.COMMA]
    assert len(commas) == 1


def test_p_depth_propagation_non_body():
    """
    Property: for non-body, result.depth == original.depth always.
    # path: is_body=False → return
    """
    for depth in [0, 1, 5, 10]:
        original = FakeLine(depth=depth, _is_import=False)
        opening = make_opening_bracket()
        result = bracket_split_build_line([], original, opening, is_body=False)
        assert result.depth == depth


def test_p_depth_propagation_body():
    """
    Property: for is_body=True, result.depth == original.depth + 1 always.
    # path: is_body=True → depth+1 → return
    """
    for depth in [0, 2, 7]:
        original = FakeLine(depth=depth, _is_import=False)
        opening = make_opening_bracket()
        result = bracket_split_build_line([], original, opening, is_body=True)
        assert result.depth == depth + 1