def split(src, sep=None, maxsplit=None):
    """Splits an iterable based on a separator. Like :meth:`str.split`,
    but for all iterables. Returns a list of lists.

    >>> split(['hi', 'hello', None, None, 'sup', None, 'soap', None])
    [['hi', 'hello'], ['sup'], ['soap']]

    See :func:`split_iter` docs for more info.
    """
    return list(split_iter(src, sep, maxsplit))