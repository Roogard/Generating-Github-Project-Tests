def longest_common_prefix_v2(strings: list[str]) -> str:
    """Find longest common prefix using vertical scanning.

    Args:
        strings: A list of strings to compare.

    Returns:
        The longest common prefix, or empty string if none exists.

    Examples:
        >>> longest_common_prefix_v2(["flower", "flow", "flight"])
        'fl'
    """
    if not strings:
        return ""
    for index in range(len(strings[0])):
        for string in strings[1:]:
            if index == len(string) or string[index] != strings[0][index]:
                return strings[0][0:index]
    return strings[0]