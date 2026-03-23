def partition_all(n, seq):
    """ Partition all elements of sequence into tuples of length at most n

    The final tuple may be shorter to accommodate extra elements.

    >>> list(partition_all(2, [1, 2, 3, 4]))
    [(1, 2), (3, 4)]

    >>> list(partition_all(2, [1, 2, 3, 4, 5]))
    [(1, 2), (3, 4), (5,)]

    See Also:
        partition
    """
    args = [iter(seq)] * n
    it = zip_longest(*args, fillvalue=no_pad)
    try:
        prev = next(it)
    except StopIteration:
        return
    for item in it:
        yield prev
        prev = item
    if prev[-1] is no_pad:
        try:
            # If seq defines __len__, then
            # we can quickly calculate where no_pad starts
            end = len(seq) % n
            if prev[end - 1] is no_pad or prev[end] is not no_pad:
                raise LookupError(
                    'The sequence passed to `parition_all` has invalid length'
                )
            yield prev[:end]
        except TypeError:
            # Get first index of no_pad without using .index()
            # https://github.com/pytoolz/toolz/issues/387
            # Binary search from CPython's bisect module,
            # modified for identity testing.
            lo, hi = 0, n
            while lo < hi:
                mid = (lo + hi) // 2
                if prev[mid] is no_pad:
                    hi = mid
                else:
                    lo = mid + 1
            yield prev[:lo]
    else:
        yield prev