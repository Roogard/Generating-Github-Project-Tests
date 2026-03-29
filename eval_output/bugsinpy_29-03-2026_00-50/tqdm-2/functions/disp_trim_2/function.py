def disp_trim(data, length):
    """
    Trim a string which may contain ANSI control characters.
    """
    if len(data) == disp_len(data):
        return data[:length]

    while disp_len(data) > length:  # carefully delete one char at a time
        data = data[:-1]
    if RE_ANSI.search(data):  # assume ANSI reset is required
        return data + "\033[0m"
    return data