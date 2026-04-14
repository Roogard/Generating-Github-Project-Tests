from algorithms.linked_list.is_palindrome import is_palindrome

# Helper class for constructing linked lists
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def list_to_linked_list(lst):
    if not lst:
        return None
    head = ListNode(lst[0])
    current = head
    for val in lst[1:]:
        current.next = ListNode(val)
        current = current.next
    return head

# --- BVA ---

def test_bva_empty_list():
    # Input: empty list (None)
    assert is_palindrome(None) == True

def test_bva_single_element():
    # Input: list with one node
    head = list_to_linked_list([1])
    assert is_palindrome(head) == True

def test_bva_two_elements_palindrome():
    # Input: minimal even palindrome
    head = list_to_linked_list([1, 1])
    assert is_palindrome(head) == True

def test_bva_two_elements_non_palindrome():
    # Input: minimal even non-palindrome
    head = list_to_linked_list([1, 2])
    assert is_palindrome(head) == False

def test_bva_three_elements_palindrome():
    # Input: minimal odd palindrome
    head = list_to_linked_list([1, 2, 1])
    assert is_palindrome(head) == True

def test_bva_three_elements_non_palindrome():
    # Input: minimal odd non-palindrome
    head = list_to_linked_list([1, 2, 3])
    assert is_palindrome(head) == False

def test_bva_large_even_palindrome():
    # Input: typical even-length palindrome
    head = list_to_linked_list([1, 2, 3, 3, 2, 1])
    assert is_palindrome(head) == True

def test_bva_large_odd_palindrome():
    # Input: typical odd-length palindrome
    head = list_to_linked_list([1, 2, 3, 4, 3, 2, 1])
    assert is_palindrome(head) == True

def test_bva_large_non_palindrome():
    # Input: typical non-palindrome
    head = list_to_linked_list([1, 2, 3, 4, 5, 6])
    assert is_palindrome(head) == False

# --- ECP ---

def test_valid_empty():
    # Valid class: empty list (None)
    assert is_palindrome(None) == True

def test_valid_single_element():
    # Valid class: single element list (always palindrome)
    head = list_to_linked_list([5])
    assert is_palindrome(head) == True

def test_valid_even_length_palindrome():
    # Valid class: even-length palindrome
    head = list_to_linked_list([1, 2, 2, 1])
    assert is_palindrome(head) == True

def test_valid_odd_length_palindrome():
    # Valid class: odd-length palindrome
    head = list_to_linked_list([1, 2, 3, 2, 1])
    assert is_palindrome(head) == True

def test_valid_non_palindrome():
    # Valid class: non-palindrome list
    head = list_to_linked_list([1, 2, 3])
    assert is_palindrome(head) == False

def test_invalid_input_not_a_list():
    # Invalid class: input is not a linked list node (no .val or .next)
    # Expect an AttributeError when accessing .next
    try:
        is_palindrome("not a node")
        assert False, "Expected AttributeError"
    except AttributeError:
        pass

# --- Mutation Detection ---

def test_mutation_off_by_one_even_length():
    # detects off-by-one in loop bound (fast pointer movement)
    # For even length list, correct middle split should work.
    head = list_to_linked_list([1, 2, 3, 4, 4, 3, 2, 1])
    assert is_palindrome(head) == True

def test_mutation_off_by_one_odd_length():
    # detects off-by-one in loop bound (fast pointer movement)
    head = list_to_linked_list([1, 2, 3, 2, 1])
    assert is_palindrome(head) == True

def test_mutation_wrong_operator_and_vs_or():
    # detects wrong operator (while fast and fast.next vs while fast or fast.next)
    # If condition becomes 'or', fast could be None and fast.next would cause AttributeError
    # This test ensures fast and fast.next are both checked.
    head = list_to_linked_list([1, 2, 1])
    assert is_palindrome(head) == True

def test_mutation_boundary_inclusivity():
    # detects boundary inclusivity (handling of slow.next = None)
    # If slow.next not set to None, first half and reversed second half may not separate correctly.
    head = list_to_linked_list([1, 2, 2, 1])
    assert is_palindrome(head) == True

def test_mutation_missing_negation():
    # detects missing negation (if node.val == head.val return False)
    # Correct logic: if values differ, return False.
    head = list_to_linked_list([1, 2, 3])
    assert is_palindrome(head) == False

def test_mutation_wrong_constant_empty_handling():
    # detects wrong constant (return False for empty list)
    # Empty list is a palindrome.
    assert is_palindrome(None) == True