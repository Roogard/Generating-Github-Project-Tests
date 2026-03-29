def target_version_option_callback(
    c: click.Context, p: Union[click.Option, click.Parameter], v: Tuple[str, ...]
) -> List[TargetVersion]:
    """Compute the target versions from a --target-version flag.

    This is its own function because mypy couldn't infer the type correctly
    when it was a lambda, causing mypyc trouble.
    """
    return [TargetVersion[val.upper()] for val in v]