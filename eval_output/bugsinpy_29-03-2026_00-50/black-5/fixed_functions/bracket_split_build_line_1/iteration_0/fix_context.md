## Root Cause Diagnosis

Root Cause: The `result.append(comment_after, preformatted=True)` call in the populate loop is not adding the comment leaf to `result.leaves` — instead, the `Line.append` method with `preformatted=True` appears to store comments in a separate `comments` dict rather than in `leaves`. The real bug is that `comment_after` leaves returned by `original.comments_after(leaf)` are being appended as comments (stored in `Line.comments`) rather than as regular leaves in `Line.leaves`, because `Line.append` recognizes comment tokens and routes them differently regardless of `preformatted`.

Looking at the error: the comment leaf `Leaf(COMMENT, '# hi')` ends up in `Line.comments` dict but not in `Line.leaves`. This means `original.comments_after(leaf)` returns actual `COMMENT`-type leaves, and `Line.append` treats them as comments rather than regular leaves.

Suggestion 1: Use a different append mechanism for comments
Instead of calling `result.append(comment_after, preformatted=True)`, directly append the comment leaf to `result.leaves` list (bypassing `Line.append`'s comment-routing logic), so that comment leaves from `original.comments_after()` are stored in `result.leaves` rather than `result.comments`.

Suggestion 2: Use `result.append` with the comment leaf added to result's internal comments dict manually
Change the inner loop to add `comment_after` directly via `result.leaves.append(comment_after)` instead of `result.append(comment_after, preformatted=True)`, so the comment leaf is placed in `result.leaves` in sequence with the other leaves rather than being routed to the `comments` dictionary by `Line.append`'s internal comment-detection logic.

## Trigger Test(s)

```python
# test_blackbox.py
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from blib2to3.pytree import Leaf
from blib2to3.pgen2 import token

# We need to import from black but also mock heavy dependencies where needed
import black
from black import bracket_split_build_line, Line, STANDALONE_COMMENT, normalize_prefix, should_explode


# --- Helpers ---

def make_leaf(tok_type=token.NAME, value="x", prefix=""):
    """Create a real Leaf node."""
    leaf = Leaf(tok_type, value, prefix=prefix)
    return leaf


def make_original_line(depth=0, is_import=False, inside_brackets=False):
    """Create a minimal Line object with controlled attributes."""
    line = MagicMock(spec=Line)
    line.depth = depth
    line.is_import = is_import
    line.inside_brackets = inside_brackets
    line.comments_after = MagicMock(return_value=[])
    return line


def make_opening_bracket():
    return make_leaf(token.LPAR, "(")


# --- BVA ---

class TestBVADepth:
    def test_depth_zero_is_body_false(self):
        """BVA: depth=0 (min), is_body=False — result depth equals original."""
        original = make_original_line(depth=0)
        leaves = [make_leaf(token.NAME, "x")]
        opening = make_opening_bracket()
        result = bracket_split_build_line(leaves, original, opening, is_body=False)
        # A correct implementation must preserve original depth when is_body=False
        assert result.depth == 0

    def test_depth_zero_is_body_true(self):
        """BVA: depth=0, is_body=True — result depth must be 0+1=1."""
        original = make_original_line(depth=0)
        leaves = [make_leaf(token.NAME, "x")]
        opening = make_opening_bracket()
        result = bracket_split_build_line(leaves, original, opening, is_body=True)
        assert result.depth == 1

    def test_depth_one_is_body_true(self):
        """BVA: depth=1 (min+1), is_body=True — result depth must be 2."""
        original = make_original_line(depth=1)
        leaves = [make_leaf(token.NAME, "x")]
        opening = make_opening_bracket()
        result = bracket_split_build_line(leaves, original, opening, is_body=True)
        assert result.depth == 2

    def test_large_depth_is_body_true(self):
        """BVA: large depth, is_body=True — result depth incremented by exactly 1."""
        original = make_original_line(depth=100)
        leaves = [make_leaf(token.NAME, "x")]
        opening = make_opening_bracket()
        result = bracket_split_build_line(leaves, original, opening, is_body=True)
        assert result.depth == 101

    def test_empty_leaves_is_body_false(self):
        """BVA: empty leaves collection — must still produce a valid line."""
        original = make_original_line(depth=0)
        opening = make_opening_bracket()
        result = bracket_split_build_line([], original, opening, is_body=False)
        # An empty leaves list should produce a line with no leaves appended
        assert result.depth == 0

    def test_empty_leaves_is_body_true(self):
        """BVA: empty leaves, is_body=True — no crash, no trailing comma inserted."""
        original = make_original_line(depth=0, is_import=True)
        opening = make_opening_bracket()
        # Should not raise
        result = bracket_split_build_line([], original, opening, is_body=True)
        assert result.depth == 1
        assert result.inside_brackets is True

    def test_single_leaf_is_body_true(self):
        """BVA: single element leaves, is_body=True — prefix normalized."""
        original = make_original_line(depth=0)
        leaf = make_leaf(token.NAME, "x", prefix="   ")
        opening = make_opening_bracket()
        with patch("black.normalize_prefix") as mock_np, \
             patch("black.should_explode", return_value=False):
            result = bracket_split_build_line([leaf], original, opening, is_body=True)
            mock_np.assert_called_once_with(leaf, inside_brackets=True)


# --- ECP ---

class TestECPIsBodyFalse:
    def test_is_body_false_no_inside_brackets(self):
        """ECP valid class: is_body=False means inside_brackets stays default (False)."""
        original = make_original_line(depth=2)
        leaves = [make_leaf(token.NAME, "a"), make_leaf(token.NAME, "b")]
        opening = make_opening_bracket()
        result = bracket_split_build_line(leaves, original, opening, is_body=False)
        # A correct implementation should NOT set inside_brackets for is_body=False
        assert result.inside_brackets is False

    def test_is_body_false_depth_unchanged(self):
        """ECP valid class: is_body=False depth must equal original depth."""
        original = make_original_line(depth=3)
        leaves = [make_leaf(token.NAME, "x")]
        opening = make_opening_bracket()
        result = bracket_split_build_line(leaves, original, opening, is_body=False)
        assert result.depth == 3

    def test_is_body_false_no_trailing_comma_added(self):
        """ECP valid class: is_body=False, is_import=True — no comma added."""
        original = make_original_line(depth=0, is_import=True)
        leaf_a = make_leaf(token.NAME, "a")
        opening = make_opening_bracket()
        result = bracket_split_build_line([leaf_a], original, opening, is_body=False)
        # Result leaves should not have an extra comma injected
        # Check by counting leaves in result using the real line's leaves attribute
        assert result.depth == 0


class TestECPIsBodyTrue:
    def test_is_body_true_inside_brackets_set(self):
        """ECP valid class: is_body=True sets inside_brackets=True."""
        original = make_original_line(depth=0)
        leaves = [make_leaf(token.NAME, "x")]
        opening = make_opening_bracket()
        with patch("black.should_explode", return_value=False):
            result = bracket_split_build_line(leaves, original, opening, is_body=True)
        assert result.inside_brackets is True

    def test_is_body_true_depth_incremented(self):
        """ECP valid class: is_body=True increments depth by exactly 1."""
        original = make_original_line(depth=5)
        leaves = [make_leaf(token.NAME, "x")]
        opening = make_opening_bracket()
        with patch("black.should_explode", return_value=False):
            result = bracket_split_build_line(leaves, original, opening, is_body=True)
        assert result.depth == 6


class TestECPImportTrailingComma:
    def test_import_body_without_trailing_comma_gets_one(self):
        """ECP: is_body=True, is_import=True, last real leaf not comma — comma inserted."""
        original = make_original_line(depth=0, is_import=True)
        leaf_a = make_leaf(token.NAME, "a")
        opening = make_opening_bracket()
        with patch("black.normalize_prefix"), \
             patch("black.should_explode", return_value=False):
            result = bracket_split_build_line([leaf_a], original, opening, is_body=True)
        # The result line must end with a comma leaf
        assert len(result.leaves) >= 1
        last_leaf = result.leaves[-1]
        assert last_leaf.type == token.COMMA, (
            "A correct implementation must add a trailing comma to import bodies"
        )

    def test_import_body_already_has_trailing_comma_no_duplicate(self):
        """ECP: is_body=True, is_import=True, last real leaf IS comma — no extra comma."""
        original = make_original_line(depth=0, is_import=True)
        leaf_a = make_leaf(token.NAME, "a")
        leaf_comma = make_leaf(token.COMMA, ",")
        opening = make_opening_bracket()
        with patch("black.normalize_prefix"), \
             patch("black.should_explode", return_value=False):
            result = bracket_split_build_line(
                [leaf_a, leaf_comma], original, opening, is_body=True
            )
        # Must not have two consecutive commas
        comma_count = sum(1 for lf in result.leaves if lf.type == token.COMMA)
        assert comma_count == 1, (
            "A correct implementation must not add a duplicate trailing comma"
        )

    def test_non_import_body_no_trailing_comma(self):
        """ECP: is_body=True, is_import=False — no trailing comma added."""
        original = make_original_line(depth=0, is_import=False)
        leaf_a = make_leaf(token.NAME, "a")
        opening = make_opening_bracket()
        with patch("black.normalize_prefix"), \
             patch("black.should_explode", return_value=False):
            result = bracket_split_build_line([leaf_a], original, opening, is_body=True)
        comma_count = sum(1 for lf in result.leaves if lf.type == token.COMMA)
        assert comma_count == 0, (
            "A correct implementation must NOT add trailing comma for non-import bodies"
        )

    def test_import_body_standalone_comment_last_then_name(self):
        """ECP: last real (non-comment) leaf is a name, comment before it — comma after name."""
        original = make_original_line(depth=0, is_import=True)
        leaf_a = make_leaf(token.NAME, "a")
        leaf_comment = make_leaf(STANDALONE_COMMENT, "# comment")
        # leaves = [name, standalone_comment]: loop scans backward, skips comment, adds comma after name
        opening = make_opening_bracket()
        with patch("black.normalize_prefix"), \
             patch("black.should_explode", return_value=False):
            result = bracket_split_build_line(
                [leaf_a, leaf_comment], original, opening, is_body=True
            )
        # A comma must be present (inserted before the comment)
        assert any(lf.type == token.COMMA for lf in result.leaves), (
            "A correct implementation must insert comma before trailing standalone comment"
        )

    def test_import_body_all_standalone_comments(self):
        """ECP edge: all leaves are STANDALONE_COMMENTs — loop never breaks, no comma inserted."""
        original = make_original_line(depth=0, is_import=True)
        comment1 = make_leaf(STANDALONE_COMMENT, "# c1")
        comment2 = make_leaf(STANDALONE_COMMENT, "# c2")
        opening = make_opening_bracket()
        with patch("black.normalize_prefix"), \
             patch("black.should_explode", return_value=False):
            result = bracket_split_build_line(
                [comment1, comment2], original, opening, is_body=True
            )
        # No NAME/COMMA leaves → loop exhausts without inserting comma
        comma_count = sum(1 for lf in result.leaves if lf.type == token.COMMA)
        assert comma_count == 0


class TestECPComments:
    def test_comments_appended_after_leaf(self):
        """ECP: comments_after returns leaves — they must be appended after their leaf."""
        original = make_original_line(depth=0, is_import=False)
        leaf_a = make_leaf(token.NAME, "a")
        comment = make_leaf(token.COMMENT, "# hi")
        original.comments_after = MagicMock(side_effect=lambda lf: [comment] if lf is leaf_a else [])
        opening = make_opening_bracket()
        result = bracket_split_build_line([leaf_a], original, opening, is_body=False)
        # comment must follow leaf_a in result leaves
        assert leaf_a in result.leaves
        assert comment in result.leaves
        idx_leaf = result.leaves.index(leaf_a)
        idx_comment = result.leaves.index(comment)
        assert idx_comment == idx_leaf + 1, (
            "A correct implementation appends comment immediately after its leaf"
        )

    def test_no_comments_only_leaves(self):
        """ECP: comments_after returns [] — result contains only the original leaves."""
        original = make_original_line(depth=0)
        original.comments_after = MagicMock(return_value=[])
        leaf_a = make_leaf(token.NAME, "a")
        leaf_b = make_leaf(token.NAME, "b")
        opening = make_opening_bracket()
        result = bracket_split_build_line([leaf_a, leaf_b], original, opening, is_body=False)
        assert result.leaves == [leaf_a, leaf_b]


# --- Mutation Detection ---

class TestMutationDetection:
    def test_mutation_depth_plus_one_not_zero(self):
        """Mutation: `result.depth += 1` mutated to `result.depth = 1` or no-op.
        With depth=5, result must be 6, not 5 or 1."""
        original = make_original_line(depth=5)
        leaves = [make_leaf(token.NAME, "x")]
        opening = make_opening_bracket()
        with patch("black.should_explode", return_value=False):
            result = bracket_split_build_line(leaves, original, opening, is_body=True)
        assert result.depth == 6  # detects += replaced with = 1 or no-op

    def test_mutation_is_body_check_inverted(self):
        """Mutation: `if is_body` → `if not is_body`. With is_body=False, depth must NOT change."""
        original = make_original_line(depth=3)
        leaves = [make_leaf(token.NAME, "x")]
        opening = make_opening_bracket()
        result = bracket_split_build_line(leaves, original, opening, is_body=False)
        assert result.depth == 3  # detects inverted is_body check
        assert result.inside_brackets is False

    def test_mutation_range_direction_backward_loop(self):
        """Mutation: `range(len(leaves)-1, -1, -1)` mutated to `range(len(leaves))` (forward).
        The comma insertion logic must find the LAST non-comment leaf, not first.
        With [name_a, name_b], comma should be after name_b, not name_a."""
        original = make_original_line(depth=0, is_import=True)
        leaf_a = make_leaf(token.NAME, "a")
        leaf_b = make_leaf(token.NAME, "b")
        opening = make_opening_bracket()
        with patch("black.normalize_prefix"), \
             patch("black.should_explode", return_value=False):
            result = bracket_split_build_line([leaf_a, leaf_b], original, opening, is_body=True)
        # The comma must be inserted right after leaf_b (index 1), giving [a, b, comma]
        # If loop went forward, comma would be inserted after leaf_a
        assert result.leaves[-1].type == token.COMMA or result.leaves[-2].type == token.COMMA
        # More precise: leaf_b must come before the comma
        comma_positions = [i for i, lf in enumerate(result.leaves) if lf.type == token.COMMA]
        b_position = result.leaves.index(leaf_b)
        assert all(cp > b_position for cp in comma_positions), (
            "Comma must be inserted after the last non-comment leaf (leaf_b), not before it"
        )

    def test_mutation_insert_position_off_by_one(self):
        """Mutation: `leaves.insert(i+1, ...)` → `leaves.insert(i, ...)`.
        Comma must be inserted AFTER the last non-comment leaf, not BEFORE it."""
        original = make_original_line(depth=0, is_import=True)
        leaf_a = make_leaf(token.NAME, "a")
        opening = make_opening_bracket()
        with patch("black.normalize_prefix"), \
             patch("black.should_explode", return_value=False):
            result = bracket_split_build_line([leaf_a], original, opening, is_body=True)
        # With one name leaf, correct result is [name, comma]
        assert result.leaves[0].type == token.NAME
        assert result.leaves[1].type == token.COMMA, (
            "Comma must be AFTER the name leaf (insert at i+1, not i)"
        )

    def test_mutation_standalone_comment_continue_vs_break(self):
        """Mutation: `continue` replaced by `break` in standalone comment check.
        With [name, standalone_comment], if `continue` is replaced by `break`,
        the comma would be incorrectly placed or not placed at all."""
        original = make_original_line(depth=0, is_import=True)
        leaf_name = make_leaf(token.NAME, "os")
        leaf_sc = make_leaf(STANDALONE_COMMENT, "# comment")
        opening = make_opening_bracket()
        with patch("black.normalize_prefix"), \
             patch("black.should_explode", return_value=False):
            result = bracket_split_build_line(
                [leaf_name, leaf_sc], original, opening, is_body=True
            )
        # A correct implementation skips the standalone comment and inserts comma after name
        # The comma must be between name and the standalone comment in the result
        names = [lf for lf in result.leaves if lf.type == token.NAME]
        commas = [lf for lf in result.leaves if lf.type == token.COMMA]
        assert len(commas) == 1, "Exactly one comma must be inserted"
        comma_pos = result.leaves.index(commas[0])
        name_pos = result.leaves.index(names[0])
        assert comma_pos > name_pos, "Comma must follow the name, not precede it"

    def test_mutation_comma_break_vs_continue(self):
        """Mutation: `break` on finding existing comma replaced by `continue`.
        With [name, comma], loop must stop at comma, not insert another one."""
        original = make_original_line(depth=0, is_import=True)
        leaf_a = make_leaf(token.NAME, "a")
        leaf_comma = make_leaf(token.COMMA, ",")
        opening = make_opening_bracket()
        with patch("black.normalize_prefix"), \
             patch("black.should_explode", return_value=False):
            result = bracket_split_build_line(
                [leaf_a, leaf_comma], original, opening, is_body=True
            )
        comma_count = sum(1 for lf in result.leaves if lf.type == token.COMMA)
        assert comma_count == 1, (
            "Must break on finding existing comma — not continue adding more"
        )

    def test_mutation_preformatted_true_not_false(self):
        """Mutation: `preformatted=True` → `preformatted=False` in append call.
        We verify append is called with preformatted=True by checking result correctness
        for a multi-leaf scenario (black.Line.append behavior depends on preformatted)."""
        original = make_original_line(depth=0)
        leaf_a = make_leaf(token.NAME, "a")
        leaf_b = make_leaf(token.NAME, "b")
        opening = make_opening_bracket()
        result = bracket_split_build_line([leaf_a, leaf_b], original, opening, is_body=False)
        # Both leaves must appear in the result in order
        assert result.leaves == [leaf_a, leaf_b]

    def test_mutation_should_explode_only_when_is_body(self):
        """Mutation: `if is_body: result.should_explode = ...` moved outside if-block.
        When is_body=False, should_explode must NOT be set (or set to default False)."""
        original = make_original_line(depth=0)
        leaves = [make_leaf(token.NAME, "x")]
        opening = make_opening_bracket()
        with patch("black.should_explode") as mock_se:
            result = bracket_split_build_line(leaves, original, opening, is_body=False)
            mock_se.assert_not_called(), (
                "should_explode must only be computed when is_body=True"
            )

    def test_mutation_depth_added_to_result_not_original(self):
        """Mutation: `result.depth += 1` vs accidentally `original.depth += 1`.
        Verify original.depth is unchanged after call."""
        original = make_original_line(depth=4)
        leaves = [make_leaf(token.NAME, "x")]
        opening = make_opening_bracket()
        with patch("black.should_explode", return_value=False):
            bracket_split_build_line(leaves, original, opening, is_body=True)
        assert original.depth == 4, (
            "original.depth must not be mutated — only result.depth should be incremented"
        )
```

```python
# test_whitebox.py
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
```
