def run_hook(hook_name, project_dir, context):
    """
    Try to find and execute a hook from the specified project directory.

    :param hook_name: The hook to execute.
    :param project_dir: The directory to execute the script from.
    :param context: Cookiecutter project context.
    """
    script = find_hooks().get(hook_name)
    if script is None:
        logging.debug('No hooks found')
        return EXIT_SUCCESS
    return run_script_with_context(script, project_dir, context)