import pytest
from unittest.mock import MagicMock, PropertyMock
from black import generate_ignored_nodes
from blib2to3.pytree import Leaf, Node
from blib2to3.pgen2 import token
import black

# --- Helpers to build mock node structures ---

def make_leaf(leaf_type=token.NAME, value="x", prefix=""):
    """Create a real Leaf node."""
    leaf = Leaf(leaf_type, value, prefix=prefix)
    return leaf

def make_mock_container(prefix="", next_sibling=None, node_type=token.NAME):
    """Create a mock container node with controllable prefix, next_sibling, and type."""
    container = MagicMock()
    container.prefix = prefix
    container.next_sibling = next_sibling
    container.type = node_type
    return container

def chain_containers(*prefixes, last_next=None, node_type=token.NAME):
    """Build a linked list of mock containers from left to right."""
    containers = []
    for p in prefixes:
        c = make_mock_container(prefix=p, node_type=node_type)
        containers.append(c)
    # link them
    for i in range(len(containers) - 1):
        containers[i].next_sibling = containers[i + 1]
    containers[-1].next_sibling = last_next
    return containers


# --- BVA ---

class TestBVA:

    def test_no_containers_yields_nothing(self, monkeypatch):
        """container_of returns None => generator immediately stops."""
        leaf = make_leaf()
        monkeypatch.setattr(black, "container_of", lambda l: None)
        result = list(generate_ignored_nodes(leaf))
        assert result == []

    def test_single_container_no_fmt_comment_yields_it(self, monkeypatch):
        """Single container with no comments: should yield that one container."""
        c = make_mock_container(prefix="", next_sibling=None)
        monkeypatch.setattr(black, "container_of", lambda l: c)
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert result == [c]

    def test_single_container_endmarker_yields_nothing(self, monkeypatch):
        """Container whose type is ENDMARKER: loop condition stops immediately."""
        c = make_mock_container(prefix="", next_sibling=None, node_type=token.ENDMARKER)
        monkeypatch.setattr(black, "container_of", lambda l: c)
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        # ENDMARKER container must NOT be yielded
        assert result == []

    def test_two_containers_no_fmt_on_yields_both(self, monkeypatch):
        """Two containers, no fmt:on => both yielded."""
        c2 = make_mock_container(prefix="", next_sibling=None)
        c1 = make_mock_container(prefix="", next_sibling=c2)
        monkeypatch.setattr(black, "container_of", lambda l: c1)
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert result == [c1, c2]

    def test_many_containers_all_yielded_before_endmarker(self, monkeypatch):
        """Large chain: all containers before ENDMARKER should be yielded."""
        end = make_mock_container(prefix="", next_sibling=None, node_type=token.ENDMARKER)
        containers = chain_containers(*["" for _ in range(10)], last_next=end)
        monkeypatch.setattr(black, "container_of", lambda l: containers[0])
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert len(result) == 10
        assert result == containers

    def test_fmt_on_at_first_container_yields_nothing(self, monkeypatch):
        """fmt:on in first container prefix => nothing yielded (stops before yield)."""
        fmt_on_comment = MagicMock()
        fmt_on_comment.value = "# fmt: on"
        c = make_mock_container(prefix="# fmt: on\n", next_sibling=None)
        monkeypatch.setattr(black, "container_of", lambda l: c)
        monkeypatch.setattr(black, "list_comments",
                            lambda prefix, is_endmarker: [fmt_on_comment])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert result == []

    def test_fmt_on_at_second_container_yields_only_first(self, monkeypatch):
        """fmt:on in second container => only first container yielded."""
        fmt_on_comment = MagicMock()
        fmt_on_comment.value = "# fmt: on"
        c2 = make_mock_container(prefix="# fmt: on\n", next_sibling=None)
        c1 = make_mock_container(prefix="", next_sibling=c2)

        def fake_list_comments(prefix, is_endmarker):
            if "fmt: on" in prefix:
                return [fmt_on_comment]
            return []

        monkeypatch.setattr(black, "container_of", lambda l: c1)
        monkeypatch.setattr(black, "list_comments", fake_list_comments)
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert result == [c1]

    def test_fmt_on_at_last_of_three_yields_first_two(self, monkeypatch):
        """fmt:on at third container: first two must be yielded."""
        fmt_on_comment = MagicMock()
        fmt_on_comment.value = "# fmt: on"
        c3 = make_mock_container(prefix="# fmt: on\n", next_sibling=None)
        c2 = make_mock_container(prefix="", next_sibling=c3)
        c1 = make_mock_container(prefix="", next_sibling=c2)

        def fake_list_comments(prefix, is_endmarker):
            if "fmt: on" in prefix:
                return [fmt_on_comment]
            return []

        monkeypatch.setattr(black, "container_of", lambda l: c1)
        monkeypatch.setattr(black, "list_comments", fake_list_comments)
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert result == [c1, c2]


# --- ECP ---

class TestECP:

    def test_valid_class_no_fmt_comments(self, monkeypatch):
        """ECP valid: no fmt comments at all, all containers yielded."""
        c2 = make_mock_container(prefix="# some other comment\n", next_sibling=None)
        c1 = make_mock_container(prefix="# another comment\n", next_sibling=c2)
        monkeypatch.setattr(black, "container_of", lambda l: c1)
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert result == [c1, c2]

    def test_valid_class_fmt_off_only_all_yielded(self, monkeypatch):
        """ECP valid: only fmt:off comments present, all containers yielded (fmt:off doesn't stop generation)."""
        fmt_off_comment = MagicMock()
        fmt_off_comment.value = "# fmt: off"
        c2 = make_mock_container(prefix="# fmt: off\n", next_sibling=None)
        c1 = make_mock_container(prefix="", next_sibling=c2)

        def fake_list_comments(prefix, is_endmarker):
            if "fmt: off" in prefix:
                return [fmt_off_comment]
            return []

        monkeypatch.setattr(black, "container_of", lambda l: c1)
        monkeypatch.setattr(black, "list_comments", fake_list_comments)
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        # fmt:off does not trigger stopping, so both containers should be yielded
        assert result == [c1, c2]

    def test_valid_class_fmt_on_terminates(self, monkeypatch):
        """ECP valid: fmt:on causes early termination — containers after it not yielded."""
        fmt_on_comment = MagicMock()
        fmt_on_comment.value = "# fmt: on"
        c3 = make_mock_container(prefix="", next_sibling=None)
        c2 = make_mock_container(prefix="# fmt: on\n", next_sibling=c3)
        c1 = make_mock_container(prefix="", next_sibling=c2)

        def fake_list_comments(prefix, is_endmarker):
            if "fmt: on" in prefix:
                return [fmt_on_comment]
            return []

        monkeypatch.setattr(black, "container_of", lambda l: c1)
        monkeypatch.setattr(black, "list_comments", fake_list_comments)
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        # c2 has fmt:on so it stops; c3 never reached
        assert c2 not in result
        assert c3 not in result
        assert c1 in result

    def test_invalid_class_none_container(self, monkeypatch):
        """ECP invalid: container_of returns None, zero nodes yielded."""
        monkeypatch.setattr(black, "container_of", lambda l: None)
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert result == []

    def test_invalid_class_endmarker_container(self, monkeypatch):
        """ECP invalid: first container is ENDMARKER, zero nodes yielded."""
        c = make_mock_container(node_type=token.ENDMARKER)
        monkeypatch.setattr(black, "container_of", lambda l: c)
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert result == []

    def test_fmt_off_then_fmt_on_in_same_container(self, monkeypatch):
        """ECP: both fmt:off and fmt:on in same container's prefix — order matters.
        If fmt:on comes after fmt:off, is_fmt_on ends True => container not yielded.
        """
        fmt_off = MagicMock()
        fmt_off.value = "# fmt: off"
        fmt_on = MagicMock()
        fmt_on.value = "# fmt: on"
        c = make_mock_container(prefix="# fmt: off\n# fmt: on\n", next_sibling=None)

        monkeypatch.setattr(black, "container_of", lambda l: c)
        monkeypatch.setattr(black, "list_comments",
                            lambda prefix, is_endmarker: [fmt_off, fmt_on])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        # fmt:on is processed last => is_fmt_on=True => return before yield
        assert result == []

    def test_fmt_on_then_fmt_off_in_same_container(self, monkeypatch):
        """ECP: fmt:on comes first, then fmt:off in same container's comments.
        is_fmt_on ends False after processing => container IS yielded.
        """
        fmt_on = MagicMock()
        fmt_on.value = "# fmt: on"
        fmt_off = MagicMock()
        fmt_off.value = "# fmt: off"
        c = make_mock_container(prefix="# fmt: on\n# fmt: off\n", next_sibling=None)

        monkeypatch.setattr(black, "container_of", lambda l: c)
        monkeypatch.setattr(black, "list_comments",
                            lambda prefix, is_endmarker: [fmt_on, fmt_off])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        # fmt:off is processed last => is_fmt_on=False => container yielded
        assert result == [c]

    def test_multiple_containers_mixed_comments(self, monkeypatch):
        """ECP: fmt:off in middle container doesn't stop; fmt:on does."""
        fmt_off = MagicMock()
        fmt_off.value = "# fmt: off"
        fmt_on = MagicMock()
        fmt_on.value = "# fmt: on"

        c3 = make_mock_container(prefix="", next_sibling=None)
        c2 = make_mock_container(prefix="# fmt: on\n", next_sibling=c3)
        c1 = make_mock_container(prefix="# fmt: off\n", next_sibling=c2)

        def fake_list_comments(prefix, is_endmarker):
            if "fmt: on" in prefix:
                return [fmt_on]
            if "fmt: off" in prefix:
                return [fmt_off]
            return []

        monkeypatch.setattr(black, "container_of", lambda l: c1)
        monkeypatch.setattr(black, "list_comments", fake_list_comments)
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        # c1 has fmt:off (not fmt:on) => yielded; c2 has fmt:on => stops
        assert result == [c1]

    def test_result_is_iterator(self, monkeypatch):
        """ECP: The function must return an iterator/generator, not a list."""
        import types
        c = make_mock_container(prefix="", next_sibling=None)
        monkeypatch.setattr(black, "container_of", lambda l: c)
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        result = generate_ignored_nodes(leaf)
        assert isinstance(result, types.GeneratorType)


# --- Mutation Detection ---

class TestMutationDetection:

    def test_mutation_and_vs_or_in_loop_condition(self, monkeypatch):
        """Detects: 'container is not None and container.type != ENDMARKER'
        mutated to 'container is not None or container.type != ENDMARKER'.
        With None container, must yield nothing (not loop forever).
        """
        monkeypatch.setattr(black, "container_of", lambda l: None)
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert result == []

    def test_mutation_endmarker_check_wrong_type(self, monkeypatch):
        """Detects: 'container.type != token.ENDMARKER' mutated to use wrong token type.
        ENDMARKER containers must NOT appear in output.
        """
        end = make_mock_container(node_type=token.ENDMARKER)
        c1 = make_mock_container(prefix="", next_sibling=end)
        monkeypatch.setattr(black, "container_of", lambda l: c1)
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert end not in result
        assert c1 in result

    def test_mutation_is_fmt_on_initial_value_true_instead_of_false(self, monkeypatch):
        """Detects: 'is_fmt_on = False' mutated to 'is_fmt_on = True'.
        If initial value were True, a container with no comments would NOT be yielded.
        A container with empty prefix must be yielded when there are no fmt:on comments.
        """
        c = make_mock_container(prefix="", next_sibling=None)
        monkeypatch.setattr(black, "container_of", lambda l: c)
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        # Correct impl: is_fmt_on starts False => container IS yielded
        assert result == [c]

    def test_mutation_yield_before_fmt_on_check(self, monkeypatch):
        """Detects: yield placed before 'if is_fmt_on: return'.
        If mutated, the first container with fmt:on would still be yielded.
        Correct: fmt:on container must NOT be yielded.
        """
        fmt_on_comment = MagicMock()
        fmt_on_comment.value = "# fmt: on"
        c = make_mock_container(prefix="# fmt: on\n", next_sibling=None)
        monkeypatch.setattr(black, "container_of", lambda l: c)
        monkeypatch.setattr(black, "list_comments",
                            lambda prefix, is_endmarker: [fmt_on_comment])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert c not in result

    def test_mutation_next_sibling_not_advanced(self, monkeypatch):
        """Detects: 'container = container.next_sibling' mutated to infinite loop or omitted.
        With a finite chain ending in None, the generator must terminate.
        """
        c2 = make_mock_container(prefix="", next_sibling=None)
        c1 = make_mock_container(prefix="", next_sibling=c2)
        monkeypatch.setattr(black, "container_of", lambda l: c1)
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        # If next_sibling not advanced, this would loop forever — pytest timeout would catch it
        result = list(generate_ignored_nodes(leaf))
        assert result == [c1, c2]

    def test_mutation_fmt_on_in_fmt_off_check_swapped(self, monkeypatch):
        """Detects: 'comment.value in FMT_ON' and 'comment.value in FMT_OFF' swapped.
        A fmt:on comment must stop the generator; a fmt:off must not.
        """
        fmt_on = MagicMock()
        fmt_on.value = "# fmt: on"
        c2 = make_mock_container(prefix="", next_sibling=None)
        c1 = make_mock_container(prefix="# fmt: on\n", next_sibling=c2)

        def fake_list_comments(prefix, is_endmarker):
            if "fmt: on" in prefix:
                return [fmt_on]
            return []

        monkeypatch.setattr(black, "container_of", lambda l: c1)
        monkeypatch.setattr(black, "list_comments", fake_list_comments)
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        # Correct: fmt:on stops generation, so c1 must NOT be yielded
        assert c1 not in result
        assert c2 not in result

    def test_mutation_fmt_off_sets_is_fmt_on_true_instead_of_false(self, monkeypatch):
        """Detects: 'is_fmt_on = False' in fmt:off branch mutated to 'is_fmt_on = True'.
        A container that has only fmt:off comment must still be yielded.
        """
        fmt_off = MagicMock()
        fmt_off.value = "# fmt: off"
        c = make_mock_container(prefix="# fmt: off\n", next_sibling=None)
        monkeypatch.setattr(black, "container_of", lambda l: c)
        monkeypatch.setattr(black, "list_comments",
                            lambda prefix, is_endmarker: [fmt_off])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        # fmt:off should set is_fmt_on=False, so container IS yielded
        assert result == [c]

    def test_mutation_inclusive_vs_exclusive_container_type_check(self, monkeypatch):
        """Detects: '!= ENDMARKER' mutated to '== ENDMARKER' (wrong predicate direction).
        Non-ENDMARKER containers must be yielded; ENDMARKER must not.
        """
        c_normal = make_mock_container(prefix="", next_sibling=None, node_type=token.NAME)
        monkeypatch.setattr(black, "container_of", lambda l: c_normal)
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert c_normal in result

    def test_mutation_container_of_result_ignored(self, monkeypatch):
        """Detects: 'container = container_of(leaf)' replaced with hard-coded None or wrong value.
        The yielded containers must be reachable from the leaf's container.
        """
        c = make_mock_container(prefix="", next_sibling=None)
        called_with = []

        def tracking_container_of(l):
            called_with.append(l)
            return c

        monkeypatch.setattr(black, "container_of", tracking_container_of)
        monkeypatch.setattr(black, "list_comments", lambda prefix, is_endmarker: [])
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        assert called_with == [leaf]
        assert result == [c]

    def test_mutation_off_by_one_fmt_on_stops_not_continues(self, monkeypatch):
        """Off-by-one: generator stops AT the fmt:on container, not one after.
        Verifies that the container containing fmt:on is itself NOT yielded.
        """
        fmt_on = MagicMock()
        fmt_on.value = "# fmt: on"
        c3 = make_mock_container(prefix="", next_sibling=None)
        c2 = make_mock_container(prefix="# fmt: on\n", next_sibling=c3)
        c1 = make_mock_container(prefix="", next_sibling=c2)

        def fake_list_comments(prefix, is_endmarker):
            if "fmt: on" in prefix:
                return [fmt_on]
            return []

        monkeypatch.setattr(black, "container_of", lambda l: c1)
        monkeypatch.setattr(black, "list_comments", fake_list_comments)
        leaf = make_leaf()
        result = list(generate_ignored_nodes(leaf))
        # Only c1 should be yielded; c2 (with fmt:on) and c3 must not be
        assert result == [c1]
        assert c2 not in result
        assert c3 not in result