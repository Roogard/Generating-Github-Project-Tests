def run_hook(hook_name, project_dir, context):
    """
    Try to find and execute a hook from the specified project directory.

    :param hook_name: The hook to execute.
    :param project_dir: The directory to execute the script from.
    :param context: Cookiecutter project context.
    """
    script = find_hook(hook_name)
    if script is None:
        logger.debug('No %s hook found', hook_name)
        return
    logger.debug('Running hook %s', hook_name)
    run_script_with_context(script, project_dir, context)