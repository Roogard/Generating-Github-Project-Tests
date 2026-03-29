import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from black import generate_ignored_nodes

# ---------------------------------------------------------------------------
# Helpers – build lightweight fake tree nodes so we don't need a full parse
# ---------------------------------------------------------------------------

def _make_comment(value):
    c = MagicMock()
    c.value = value
    return c


def _make_container(prefix="", comments=None, next_sibling=None, type_val=None):
    """Build a fake LN (Leaf/Node) suitable for use as a container."""
    import blib2to3.pgen2.token as _token
    node = MagicMock()
    node.prefix = prefix
    # type must not equal ENDMARKER so iteration continues by default
    node.type = type_val if type_val is not None else _token.NAME
    node.next_sibling = next_sibling
    return node, comments if comments is not None else []


# ---------------------------------------------------------------------------
# We intercept the two key helpers via patching so we can control behaviour
# without a real CST.
# ---------------------------------------------------------------------------

# --- Statement Coverage ---

def test_statement_container_is_none():
    """container_of returns None → generator yields nothing immediately.
    # path: while-false → generator empty
    """
    leaf = MagicMock()
    with patch("black.container_of", return_value=None):
        result = list(generate_ignored_nodes(leaf))
    # A correct implementation should yield nothing when there is no container
    assert result == []


def test_statement_container_is_endmarker():
    """container_of returns an ENDMARKER node → loop exits without yielding.
    # path: while-false (type==ENDMARKER)
    """
    from blib2to3.pgen2 import token as _token
    leaf = MagicMock()
    container = MagicMock()
    container.type = _token.ENDMARKER
    with patch("black.container_of", return_value=container):
        result = list(generate_ignored_nodes(leaf))
    assert result == []


def test_statement_yield_single_container_no_comments():
    """One container, no comments, no next_sibling → yields exactly that container.
    # path: while-true → no comments → is_fmt_on False → yield → next_sibling None → stop
    """
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1  # not ENDMARKER
    container.next_sibling = None

    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=[]):
        result = list(generate_ignored_nodes(leaf))

    assert len(result) == 1
    assert result[0] is container


def test_statement_fmt_on_in_comment_stops_generator():
    """Comment with FMT_ON value makes is_fmt_on=True → early return, nothing yielded.
    # path: while-true → comment is fmt_on → return
    """
    from black import FMT_ON
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1
    container.next_sibling = None
    fmt_on_comment = _make_comment(next(iter(FMT_ON)))

    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=[fmt_on_comment]):
        result = list(generate_ignored_nodes(leaf))

    assert result == []


def test_statement_fmt_off_in_comment_allows_yield():
    """Comment with FMT_OFF keeps is_fmt_on=False → container is yielded.
    # path: while-true → comment is fmt_off → is_fmt_on False → yield → stop
    """
    from black import FMT_OFF
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1
    container.next_sibling = None
    fmt_off_comment = _make_comment(next(iter(FMT_OFF)))

    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=[fmt_off_comment]):
        result = list(generate_ignored_nodes(leaf))

    assert len(result) == 1
    assert result[0] is container


# --- Block Coverage ---

def test_block_multiple_siblings_all_yielded():
    """Multiple siblings without any fmt:on comment → all yielded.
    Tests blocks: loop body executed multiple times, next_sibling chain followed.
    # path: while-true (iter-1) → yield c1 → while-true (iter-2) → yield c2 → stop
    """
    leaf = MagicMock()
    c2 = MagicMock()
    c2.type = 1
    c2.next_sibling = None

    c1 = MagicMock()
    c1.type = 1
    c1.next_sibling = c2

    with patch("black.container_of", return_value=c1), \
         patch("black.list_comments", return_value=[]):
        result = list(generate_ignored_nodes(leaf))

    assert len(result) == 2
    assert result[0] is c1
    assert result[1] is c2


def test_block_fmt_on_after_first_sibling():
    """First sibling yielded, second has fmt:on → only first yielded.
    Tests the early-return block inside the loop.
    # path: while-true → yield c1 → while-true → fmt_on → return
    """
    from black import FMT_ON
    leaf = MagicMock()

    c2 = MagicMock()
    c2.type = 1
    c2.next_sibling = None

    c1 = MagicMock()
    c1.type = 1
    c1.next_sibling = c2

    fmt_on_comment = _make_comment(next(iter(FMT_ON)))

    def list_comments_side_effect(prefix, is_endmarker):
        if prefix is c2.prefix:
            return [fmt_on_comment]
        return []

    # We match by identity of the .prefix attribute
    c1.prefix = object()
    c2.prefix = object()

    def lc(prefix, is_endmarker=False):
        if prefix is c2.prefix:
            return [fmt_on_comment]
        return []

    with patch("black.container_of", return_value=c1), \
         patch("black.list_comments", side_effect=lc):
        result = list(generate_ignored_nodes(leaf))

    assert len(result) == 1
    assert result[0] is c1


def test_block_fmt_off_then_fmt_on_in_same_prefix():
    """Comments processed in order: fmt:off then fmt:on → is_fmt_on ends True → nothing yielded.
    Tests the inner-loop else branch (fmt_off resets is_fmt_on to False, then fmt_on sets True).
    # path: while-true → comment fmt_off (is_fmt_on=False) → comment fmt_on (is_fmt_on=True) → return
    """
    from black import FMT_ON, FMT_OFF
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1
    container.next_sibling = None

    comments = [
        _make_comment(next(iter(FMT_OFF))),
        _make_comment(next(iter(FMT_ON))),
    ]

    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=comments):
        result = list(generate_ignored_nodes(leaf))

    assert result == []


def test_block_fmt_on_then_fmt_off_in_same_prefix():
    """Comments in order: fmt:on then fmt:off → is_fmt_on ends False → container yielded.
    Tests opposite ordering of inner comment loop.
    # path: while-true → comment fmt_on (True) → comment fmt_off (False) → yield → stop
    """
    from black import FMT_ON, FMT_OFF
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1
    container.next_sibling = None

    comments = [
        _make_comment(next(iter(FMT_ON))),
        _make_comment(next(iter(FMT_OFF))),
    ]

    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=comments):
        result = list(generate_ignored_nodes(leaf))

    assert len(result) == 1
    assert result[0] is container


def test_block_irrelevant_comment_does_not_change_fmt_state():
    """A comment whose value is neither FMT_ON nor FMT_OFF leaves is_fmt_on=False → yield.
    Tests the implicit else branch of both inner conditionals.
    # condition: comment.value in FMT_ON: False, comment.value in FMT_OFF: False
    """
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1
    container.next_sibling = None
    irrelevant = _make_comment("# just a regular comment")

    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=[irrelevant]):
        result = list(generate_ignored_nodes(leaf))

    assert len(result) == 1
    assert result[0] is container


# --- Condition Coverage ---

def test_condition_container_none_vs_not_none():
    """
    while condition: container is not None → False (None) / True (non-None).
    # container is not None: False
    """
    leaf = MagicMock()
    with patch("black.container_of", return_value=None):
        result = list(generate_ignored_nodes(leaf))
    # correct impl must yield nothing
    assert result == []


def test_condition_container_not_none_and_not_endmarker():
    """
    # container is not None: True, container.type != ENDMARKER: True → enters loop
    """
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1  # not ENDMARKER
    container.next_sibling = None
    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=[]):
        result = list(generate_ignored_nodes(leaf))
    assert len(result) == 1


def test_condition_container_type_equals_endmarker():
    """
    # container is not None: True, container.type != ENDMARKER: False → loop exits
    """
    from blib2to3.pgen2 import token as _token
    leaf = MagicMock()
    container = MagicMock()
    container.type = _token.ENDMARKER
    with patch("black.container_of", return_value=container):
        result = list(generate_ignored_nodes(leaf))
    assert result == []


def test_condition_comment_value_in_fmt_on_true():
    """
    # comment.value in FMT_ON: True → is_fmt_on set True → return
    """
    from black import FMT_ON
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1
    container.next_sibling = None
    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=[_make_comment(next(iter(FMT_ON)))]):
        result = list(generate_ignored_nodes(leaf))
    assert result == []


def test_condition_comment_value_in_fmt_on_false_fmt_off_true():
    """
    # comment.value in FMT_ON: False, comment.value in FMT_OFF: True → is_fmt_on set False
    Container should still be yielded since is_fmt_on is False at end.
    """
    from black import FMT_OFF
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1
    container.next_sibling = None
    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=[_make_comment(next(iter(FMT_OFF)))]):
        result = list(generate_ignored_nodes(leaf))
    assert len(result) == 1


def test_condition_comment_value_in_fmt_on_false_fmt_off_false():
    """
    # comment.value in FMT_ON: False, comment.value in FMT_OFF: False
    Irrelevant comment → state unchanged → yield container.
    """
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1
    container.next_sibling = None
    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=[_make_comment("# unrelated")]):
        result = list(generate_ignored_nodes(leaf))
    assert len(result) == 1


def test_condition_is_fmt_on_true_triggers_return():
    """
    # is_fmt_on: True at end of comment loop → early return
    """
    from black import FMT_ON
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1
    container.next_sibling = MagicMock()  # would be visited if not returned
    container.next_sibling.type = 1
    container.next_sibling.next_sibling = None
    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=[_make_comment(next(iter(FMT_ON)))]):
        result = list(generate_ignored_nodes(leaf))
    assert result == []


def test_condition_is_fmt_on_false_continues():
    """
    # is_fmt_on: False at end of comment loop → no early return, container yielded
    """
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1
    container.next_sibling = None
    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=[]):
        result = list(generate_ignored_nodes(leaf))
    assert len(result) == 1


# --- Path Coverage ---

def test_path_zero_iterations_none_container():
    """
    # path: container_of → None → while False → generator returns immediately
    Zero-iteration path of the while loop.
    """
    leaf = MagicMock()
    with patch("black.container_of", return_value=None):
        result = list(generate_ignored_nodes(leaf))
    assert result == []


def test_path_zero_iterations_endmarker_container():
    """
    # path: container_of → ENDMARKER node → while False → generator returns immediately
    """
    from blib2to3.pgen2 import token as _token
    leaf = MagicMock()
    container = MagicMock()
    container.type = _token.ENDMARKER
    with patch("black.container_of", return_value=container):
        result = list(generate_ignored_nodes(leaf))
    assert result == []


def test_path_one_iteration_no_comments_then_stop():
    """
    # path: while-true(1) → no comments → is_fmt_on False → yield c1 → next_sibling None → stop
    One iteration of the loop.
    """
    leaf = MagicMock()
    c1 = MagicMock()
    c1.type = 1
    c1.next_sibling = None
    with patch("black.container_of", return_value=c1), \
         patch("black.list_comments", return_value=[]):
        result = list(generate_ignored_nodes(leaf))
    assert len(result) == 1
    assert result[0] is c1


def test_path_one_iteration_fmt_on_early_return():
    """
    # path: while-true(1) → fmt_on comment → is_fmt_on True → return (no yield)
    """
    from black import FMT_ON
    leaf = MagicMock()
    c1 = MagicMock()
    c1.type = 1
    c1.next_sibling = None
    with patch("black.container_of", return_value=c1), \
         patch("black.list_comments", return_value=[_make_comment(next(iter(FMT_ON)))]):
        result = list(generate_ignored_nodes(leaf))
    assert result == []


def test_path_multiple_iterations_all_yielded():
    """
    # path: while-true(1) → yield c1 → while-true(2) → yield c2 → while-true(3) → yield c3 → stop
    Three-iteration path.
    """
    leaf = MagicMock()
    c3 = MagicMock(); c3.type = 1; c3.next_sibling = None
    c2 = MagicMock(); c2.type = 1; c2.next_sibling = c3
    c1 = MagicMock(); c1.type = 1; c1.next_sibling = c2

    with patch("black.container_of", return_value=c1), \
         patch("black.list_comments", return_value=[]):
        result = list(generate_ignored_nodes(leaf))

    assert len(result) == 3
    assert result[0] is c1
    assert result[1] is c2
    assert result[2] is c3


def test_path_multiple_iterations_fmt_on_terminates_mid_chain():
    """
    # path: while-true(1) → yield c1 → while-true(2) → fmt_on → return
    Iterator stops mid-chain due to fmt:on in second container's prefix.
    """
    from black import FMT_ON
    leaf = MagicMock()

    c2 = MagicMock(); c2.type = 1; c2.next_sibling = None
    c2.prefix = "c2_prefix"
    c1 = MagicMock(); c1.type = 1; c1.next_sibling = c2
    c1.prefix = "c1_prefix"

    fmt_on_comment = _make_comment(next(iter(FMT_ON)))

    def lc(prefix, is_endmarker=False):
        if prefix == "c2_prefix":
            return [fmt_on_comment]
        return []

    with patch("black.container_of", return_value=c1), \
         patch("black.list_comments", side_effect=lc):
        result = list(generate_ignored_nodes(leaf))

    assert len(result) == 1
    assert result[0] is c1


def test_path_comment_loop_multiple_comments_mixed():
    """
    # path: while-true(1) → comment fmt_on (True) → comment fmt_off (False) →
    #        is_fmt_on False → yield → stop
    Inner comment loop runs multiple times (multiple comments in prefix).
    """
    from black import FMT_ON, FMT_OFF
    leaf = MagicMock()
    container = MagicMock()
    container.type = 1
    container.next_sibling = None

    comments = [
        _make_comment(next(iter(FMT_ON))),
        _make_comment(next(iter(FMT_OFF))),
    ]

    with patch("black.container_of", return_value=container), \
         patch("black.list_comments", return_value=comments):
        result = list(generate_ignored_nodes(leaf))

    # After fmt:on then fmt:off, is_fmt_on should be False → yield
    assert len(result) == 1
    assert result[0] is container


def test_path_sibling_becomes_endmarker_stops_loop():
    """
    # path: while-true(1) → yield c1 → c1.next_sibling is ENDMARKER →
    #        while-true(2, ENDMARKER) → loop exits
    Chain terminates because next sibling is ENDMARKER.
    """
    from blib2to3.pgen2 import token as _token
    leaf = MagicMock()

    endmarker = MagicMock()
    endmarker.type = _token.ENDMARKER

    c1 = MagicMock()
    c1.type = 1
    c1.next_sibling = endmarker

    with patch("black.container_of", return_value=c1), \
         patch("black.list_comments", return_value=[]):
        result = list(generate_ignored_nodes(leaf))

    # c1 should be yielded; ENDMARKER stops the loop before yielding again
    assert len(result) == 1
    assert result[0] is c1