def nth(n, seq):
    """ The nth element in a sequence

    >>> nth(1, 'ABC')
    'B'
    """
    if isinstance(seq, (tuple, list, Sequence)):
        return seq[n]
    else:
        return next(itertools.islice(seq, n, None))