def is_palindrome(head: object | None) -> bool:
    """Check if a linked list is a palindrome by reversing the second half.

    Args:
        head: Head node of the linked list (must have .val and .next attrs).

    Returns:
        True if the list is a palindrome, False otherwise.

    Examples:
        >>> is_palindrome(None)
        True
    """
    if not head:
        return True
    fast, slow = head.next, head
    while fast and fast.next:
        fast = fast.next.next
        slow = slow.next
    second = slow.next
    slow.next = None
    node = None
    while second:
        nxt = second.next
        second.next = node
        node = second
        second = nxt
    while node:
        if node.val != head.val:
            return False
        node = node.next
        head = head.next
    return True