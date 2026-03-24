def max_profit_optimized(prices: list[int]) -> int:
    """Find maximum profit using Kadane-style single pass.

    Args:
        prices: List of stock prices per day.

    Returns:
        Maximum achievable profit (0 if no profitable trade exists).

    Examples:
        >>> max_profit_optimized([7, 1, 5, 3, 6, 4])
        5
        >>> max_profit_optimized([7, 6, 4, 3, 1])
        0
    """
    cur_max, max_so_far = 0, 0
    for i in range(1, len(prices)):
        cur_max = max(0, cur_max + prices[i] - prices[i - 1])
        max_so_far = max(max_so_far, cur_max)
    return max_so_far