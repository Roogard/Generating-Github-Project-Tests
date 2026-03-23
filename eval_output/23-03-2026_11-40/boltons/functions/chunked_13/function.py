def flatten(iterable):
    """``flatten()`` returns a collapsed list of all the elements from
    *iterable* while collapsing any nested iterables.

    >>> nested = [[1, 2], [[3], [4, 5]]]
    >>> flatten(nested)
    [1, 2, 3, 4, 5]
    """
    return list(flatten_iter(iterable))