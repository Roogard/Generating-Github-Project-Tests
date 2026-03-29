def run_script_with_context(script_path, cwd, context):
    """
    Executes a script after rendering with it Jinja.

    :param script_path: Absolute path to the script to run.
    :param cwd: The directory to run the script from.
    :param context: Cookiecutter project template context.
    """
    _, extension = os.path.splitext(script_path)

    contents = io.open(script_path, 'r', encoding='utf-8').read()

    with tempfile.NamedTemporaryFile(
        delete=False,
        mode='w',
        suffix=extension,
        encoding='utf-8'
    ) as temp:
        temp.write(Template(contents).render(**context))

    return run_script(temp.name, cwd)