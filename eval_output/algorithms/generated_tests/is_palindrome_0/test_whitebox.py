from algorithms.linked_list.is_palindrome import is_palindrome

# --- Statement Coverage ---

def test_empty_list():
    # Covers: if not head: return True
    assert is_palindrome(None) == True

def test_single_node():
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    head = Node(1)
    # Covers: fast, slow = head.next, head; while fast and fast.next: (false);
    # second = slow.next; slow.next = None; node = None; while second: (false);
    # while node: (false); return True
    assert is_palindrome(head) == True

def test_two_node_palindrome():
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    n1 = Node(1)
    n2 = Node(1)
    n1.next = n2
    # Covers: fast, slow = head.next, head; while fast and fast.next: (false);
    # second = slow.next; slow.next = None; node = None; while second: (true);
    # nxt = second.next; second.next = node; node = second; second = nxt; while second: (false);
    # while node: (true); if node.val != head.val: (false); node = node.next; head = head.next;
    # while node: (false); return True
    assert is_palindrome(n1) == True

def test_two_node_non_palindrome():
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    n1 = Node(1)
    n2 = Node(2)
    n1.next = n2
    # Covers: while node: (true); if node.val != head.val: (true); return False
    assert is_palindrome(n1) == False

def test_three_node_palindrome():
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    n1 = Node(1)
    n2 = Node(2)
    n3 = Node(1)
    n1.next = n2
    n2.next = n3
    # Covers: fast, slow = head.next, head; while fast and fast.next: (true);
    # fast = fast.next.next; slow = slow.next; while fast and fast.next: (false);
    # second = slow.next; slow.next = None; node = None; while second: (true);
    # nxt = second.next; second.next = node; node = second; second = nxt; while second: (false);
    # while node: (true); if node.val != head.val: (false); node = node.next; head = head.next;
    # while node: (false); return True
    assert is_palindrome(n1) == True

def test_three_node_non_palindrome():
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    n1 = Node(1)
    n2 = Node(2)
    n3 = Node(3)
    n1.next = n2
    n2.next = n3
    # Covers: while node: (true); if node.val != head.val: (true); return False
    assert is_palindrome(n1) == False

def test_four_node_palindrome():
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    n1 = Node(1)
    n2 = Node(2)
    n3 = Node(2)
    n4 = Node(1)
    n1.next = n2
    n2.next = n3
    n3.next = n4
    # Covers: fast, slow = head.next, head; while fast and fast.next: (true);
    # fast = fast.next.next; slow = slow.next; while fast and fast.next: (true);
    # fast = fast.next.next; slow = slow.next; while fast and fast.next: (false);
    # second = slow.next; slow.next = None; node = None; while second: (true);
    # nxt = second.next; second.next = node; node = second; second = nxt; while second: (true);
    # nxt = second.next; second.next = node; node = second; second = nxt; while second: (false);
    # while node: (true); if node.val != head.val: (false); node = node.next; head = head.next;
    # while node: (true); if node.val != head.val: (false); node = node.next; head = head.next;
    # while node: (false); return True
    assert is_palindrome(n1) == True

def test_four_node_non_palindrome():
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    n1 = Node(1)
    n2 = Node(2)
    n3 = Node(3)
    n4 = Node(1)
    n1.next = n2
    n2.next = n3
    n3.next = n4
    # Covers: while node: (true); if node.val != head.val: (true); return False
    assert is_palindrome(n1) == False

# --- Block Coverage ---
# All blocks covered by statement coverage tests.

# --- Condition Coverage ---

def test_condition_fast_and_fast_next_both_true():
    # fast: True, fast.next: True
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    n1 = Node(1)
    n2 = Node(2)
    n3 = Node(1)
    n1.next = n2
    n2.next = n3
    # This is a palindrome, so result should be True
    assert is_palindrome(n1) == True

def test_condition_fast_true_fast_next_false():
    # fast: True, fast.next: False (list length 2)
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    n1 = Node(1)
    n2 = Node(1)
    n1.next = n2
    assert is_palindrome(n1) == True

def test_condition_fast_false():
    # fast: False (list length 1)
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    head = Node(1)
    assert is_palindrome(head) == True

def test_condition_node_val_eq_head_val_true():
    # node.val != head.val: False (equal)
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    n1 = Node(1)
    n2 = Node(1)
    n1.next = n2
    assert is_palindrome(n1) == True

def test_condition_node_val_eq_head_val_false():
    # node.val != head.val: True (not equal)
    class Node:
        def __init__(self, val):
            self.val = val
            self.next = None
    n1 = Node(1)
    n2 = Node(2)
    n1.next = n2
    assert is_palindrome(n1) == False

# --- Path Coverage ---

# Path 1: empty list -> return True
# Covered by test_empty_list

# Path 2: single node -> fast false -> second None -> node None -> return True
# Covered by test_single_node

# Path 3: two nodes, palindrome -> fast true, fast.next false -> second not None, reverse one node -> compare equal -> return True
# Covered by test_two_node_palindrome

# Path 4: two nodes, non-palindrome -> fast true, fast.next false -> second not None, reverse one node -> compare not equal -> return False
# Covered by test_two_node_non_palindrome

# Path 5: three nodes, palindrome -> fast true, fast.next true -> fast false -> second not None, reverse one node -> compare equal -> return True
# Covered by test_three_node_palindrome

# Path 6: three nodes, non-palindrome -> fast true, fast.next true -> fast false -> second not None, reverse one node -> compare not equal -> return False
# Covered by test_three_node_non_palindrome

# Path 7: four nodes, palindrome -> fast true, fast.next true -> fast true, fast.next true -> fast false -> second not None, reverse two nodes -> compare equal twice -> return True
# Covered by test_four_node_palindrome

# Path 8: four nodes, non-palindrome -> fast true, fast.next true -> fast true, fast.next true -> fast false -> second not None, reverse two nodes -> compare not equal on first -> return False
# Covered by test_four_node_non_palindrome