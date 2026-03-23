def _sliding_window_deque(iterable, n):
    # Normal path for other values of n.
    iterator = iter(iterable)
    window = deque(islice(iterator, n - 1), maxlen=n)
    for x in iterator:
        window.append(x)
        yield tuple(window)