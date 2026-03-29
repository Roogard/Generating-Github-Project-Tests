@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-c", "--code", type=str, help="Format the code passed in as a string.")
@click.option(
    "-l",
    "--line-length",
    type=int,
    default=DEFAULT_LINE_LENGTH,
    help="How many characters per line to allow.",
    show_default=True,
)
@click.option(
    "-t",
    "--target-version",
    type=click.Choice([v.name.lower() for v in TargetVersion]),
    callback=target_version_option_callback,
    multiple=True,
    help=(
        "Python versions that should be supported by Black's output. [default: "
        "per-file auto-detection]"
    ),
)
@click.option(
    "--py36",
    is_flag=True,
    help=(
        "Allow using Python 3.6-only syntax on all input files.  This will put "
        "trailing commas in function signatures and calls also after *args and "
        "**kwargs. Deprecated; use --target-version instead. "
        "[default: per-file auto-detection]"
    ),
)
@click.option(
    "--pyi",
    is_flag=True,
    help=(
        "Format all input files like typing stubs regardless of file extension "
        "(useful when piping source on standard input)."
    ),
)
@click.option(
    "-S",
    "--skip-string-normalization",
    is_flag=True,
    help="Don't normalize string quotes or prefixes.",
)
@click.option(
    "--check",
    is_flag=True,
    help=(
        "Don't write the files back, just return the status.  Return code 0 "
        "means nothing would change.  Return code 1 means some files would be "
        "reformatted.  Return code 123 means there was an internal error."
    ),
)
@click.option(
    "--diff",
    is_flag=True,
    help="Don't write the files back, just output a diff for each file on stdout.",
)
@click.option(
    "--fast/--safe",
    is_flag=True,
    help="If --fast given, skip temporary sanity checks. [default: --safe]",
)
@click.option(
    "--include",
    type=str,
    default=DEFAULT_INCLUDES,
    help=(
        "A regular expression that matches files and directories that should be "
        "included on recursive searches.  An empty value means all files are "
        "included regardless of the name.  Use forward slashes for directories on "
        "all platforms (Windows, too).  Exclusions are calculated first, inclusions "
        "later."
    ),
    show_default=True,
)
@click.option(
    "--exclude",
    type=str,
    default=DEFAULT_EXCLUDES,
    help=(
        "A regular expression that matches files and directories that should be "
        "excluded on recursive searches.  An empty value means no paths are excluded. "
        "Use forward slashes for directories on all platforms (Windows, too).  "
        "Exclusions are calculated first, inclusions later."
    ),
    show_default=True,
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help=(
        "Don't emit non-error messages to stderr. Errors are still emitted; "
        "silence those with 2>/dev/null."
    ),
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help=(
        "Also emit messages to stderr about files that were not changed or were "
        "ignored due to --exclude=."
    ),
)
@click.version_option(version=__version__)
@click.argument(
    "src",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, readable=True, allow_dash=True
    ),
    is_eager=True,
)
@click.option(
    "--config",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, readable=True, allow_dash=False
    ),
    is_eager=True,
    callback=read_pyproject_toml,
    help="Read configuration from PATH.",
)
@click.pass_context
def main(
    ctx: click.Context,
    code: Optional[str],
    line_length: int,
    target_version: List[TargetVersion],
    check: bool,
    diff: bool,
    fast: bool,
    pyi: bool,
    py36: bool,
    skip_string_normalization: bool,
    quiet: bool,
    verbose: bool,
    include: str,
    exclude: str,
    src: Tuple[str, ...],
    config: Optional[str],
) -> None:
    """The uncompromising code formatter."""
    write_back = WriteBack.from_configuration(check=check, diff=diff)
    if target_version:
        if py36:
            err("Cannot use both --target-version and --py36")
            ctx.exit(2)
        else:
            versions = set(target_version)
    elif py36:
        err(
            "--py36 is deprecated and will be removed in a future version. "
            "Use --target-version py36 instead."
        )
        versions = PY36_VERSIONS
    else:
        # We'll autodetect later.
        versions = set()
    mode = Mode(
        target_versions=versions,
        line_length=line_length,
        is_pyi=pyi,
        string_normalization=not skip_string_normalization,
    )
    if config and verbose:
        out(f"Using configuration from {config}.", bold=False, fg="blue")
    if code is not None:
        print(format_str(code, mode=mode))
        ctx.exit(0)
    try:
        include_regex = re_compile_maybe_verbose(include)
    except re.error:
        err(f"Invalid regular expression for include given: {include!r}")
        ctx.exit(2)
    try:
        exclude_regex = re_compile_maybe_verbose(exclude)
    except re.error:
        err(f"Invalid regular expression for exclude given: {exclude!r}")
        ctx.exit(2)
    report = Report(check=check, diff=diff, quiet=quiet, verbose=verbose)
    root = find_project_root(src)
    sources: Set[Path] = set()
    path_empty(src, quiet, verbose, ctx)
    for s in src:
        p = Path(s)
        if p.is_dir():
            sources.update(
                gen_python_files_in_dir(
                    p, root, include_regex, exclude_regex, report, get_gitignore(root)
                )
            )
        elif p.is_file() or s == "-":
            # if a file was explicitly given, we don't care about its extension
            sources.add(p)
        else:
            err(f"invalid path: {s}")
    if len(sources) == 0:
        if verbose or not quiet:
            out("No Python files are present to be formatted. Nothing to do 😴")
        ctx.exit(0)

    if len(sources) == 1:
        reformat_one(
            src=sources.pop(),
            fast=fast,
            write_back=write_back,
            mode=mode,
            report=report,
        )
    else:
        reformat_many(
            sources=sources, fast=fast, write_back=write_back, mode=mode, report=report
        )

    if verbose or not quiet:
        out("Oh no! 💥 💔 💥" if report.return_code else "All done! ✨ 🍰 ✨")
        click.secho(str(report), err=True)
    ctx.exit(report.return_code)