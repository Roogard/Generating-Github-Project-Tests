def run_script(script_path, cwd='.'):
    """
    Executes a script from a working directory.

    :param script_path: Absolute path to the script to run.
    :param cwd: The directory to run the script from.
    """
    run_thru_shell = sys.platform.startswith('win')
    if script_path.endswith('.py'):
        script_command = [sys.executable, script_path]
    else:
        script_command = [script_path]

    utils.make_executable(script_path)

    proc = subprocess.Popen(
        script_command,
        shell=run_thru_shell,
        cwd=cwd
    )
    return proc.wait()