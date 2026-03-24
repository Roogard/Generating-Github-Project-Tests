def longest_common_prefix_v3(strings: list[str]) -> str:
    """Find longest common prefix using divide and conquer.

    Args:
        strings: A list of strings to compare.

    Returns:
        The longest common prefix, or empty string if none exists.

    Examples:
        >>> longest_common_prefix_v3(["flower", "flow", "flight"])
        'fl'
    """
    if not strings:
        return ""
    return _longest_common_recursive(strings, 0, len(strings) - 1)