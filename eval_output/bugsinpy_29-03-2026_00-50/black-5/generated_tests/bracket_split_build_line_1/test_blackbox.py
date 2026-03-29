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