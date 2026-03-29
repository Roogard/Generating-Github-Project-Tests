def bracket_split_build_line(
    leaves: List[Leaf], original: Line, opening_bracket: Leaf, *, is_body: bool = False
) -> Line:
    """Return a new line with given `leaves` and respective comments from `original`.

    If `is_body` is True, the result line is one-indented inside brackets and as such
    has its first leaf's prefix normalized and a trailing comma added when expected.
    """
    result = Line(depth=original.depth)
    if is_body:
        result.inside_brackets = True
        result.depth += 1
        if leaves:
            # Since body is a new indent level, remove spurious leading whitespace.
            normalize_prefix(leaves[0], inside_brackets=True)
            # Ensure a trailing comma for imports, but be careful not to add one after
            # any comments.
            if original.is_import:
                for i in range(len(leaves) - 1, -1, -1):
                    if leaves[i].type == STANDALONE_COMMENT:
                        continue
                    elif leaves[i].type == token.COMMA:
                        break
                    else:
                        leaves.insert(i + 1, Leaf(token.COMMA, ","))
                        break
    # Populate the line
    for leaf in leaves:
        result.append(leaf, preformatted=True)
        for comment_after in original.comments_after(leaf):
            result.leaves.append(comment_after)
    if is_body:
        result.should_explode = should_explode(result, opening_bracket)
    return result