def generate_files(repo_dir, context=None, output_dir='.',
                   overwrite_if_exists=False):
    """
    Renders the templates and saves them to files.

    :param repo_dir: Project template input directory.
    :param context: Dict for populating the template's variables.
    :param output_dir: Where to output the generated project dir into.
    :param overwrite_if_exists: Overwrite the contents of the output directory
        if it exists
    """

    template_dir = find_template(repo_dir)
    logging.debug('Generating project from {0}...'.format(template_dir))
    context = context or {}

    unrendered_dir = os.path.split(template_dir)[1]
    ensure_dir_is_templated(unrendered_dir)
    project_dir = render_and_create_dir(unrendered_dir,
                                        context,
                                        output_dir,
                                        overwrite_if_exists)

    # We want the Jinja path and the OS paths to match. Consequently, we'll:
    #   + CD to the template folder
    #   + Set Jinja's path to '.'
    #
    #  In order to build our files to the correct folder(s), we'll use an
    # absolute path for the target folder (project_dir)

    project_dir = os.path.abspath(project_dir)
    logging.debug('project_dir is {0}'.format(project_dir))

    # run pre-gen hook from repo_dir
    with work_in(repo_dir):
        if run_hook('pre_gen_project', project_dir, context) != EXIT_SUCCESS:
            logging.error("Stopping generation because pre_gen_project"
                          " hook script didn't exit sucessfully")
            return

    with work_in(template_dir):
        env = Environment(keep_trailing_newline=True)
        env.loader = FileSystemLoader('.')

        for root, dirs, files in os.walk('.'):
            # We must separate the two types of dirs into different lists.
            # The reason is that we don't want ``os.walk`` to go through the
            # unrendered directories, since they will just be copied.
            copy_dirs = []
            render_dirs = []

            for d in dirs:
                d_ = os.path.normpath(os.path.join(root, d))
                # We check the full path, because that's how it can be
                # specified in the ``_copy_without_render`` setting, but
                # we store just the dir name
                if copy_without_render(d_, context):
                    copy_dirs.append(d)
                else:
                    render_dirs.append(d)

            for copy_dir in copy_dirs:
                indir = os.path.normpath(os.path.join(root, copy_dir))
                outdir = os.path.normpath(os.path.join(project_dir, indir))
                logging.debug(
                    'Copying dir {0} to {1} without rendering'
                    ''.format(indir, outdir)
                )
                shutil.copytree(indir, outdir)

            # We mutate ``dirs``, because we only want to go through these dirs
            # recursively
            dirs[:] = render_dirs
            for d in dirs:
                unrendered_dir = os.path.join(project_dir, root, d)
                render_and_create_dir(unrendered_dir, context, output_dir,
                                      overwrite_if_exists)

            for f in files:
                infile = os.path.normpath(os.path.join(root, f))
                if copy_without_render(infile, context):
                    outfile_tmpl = Template(infile)
                    outfile_rendered = outfile_tmpl.render(**context)
                    outfile = os.path.join(project_dir, outfile_rendered)
                    logging.debug(
                        'Copying file {0} to {1} without rendering'
                        ''.format(infile, outfile)
                    )
                    shutil.copyfile(infile, outfile)
                    shutil.copymode(infile, outfile)
                    continue
                logging.debug('f is {0}'.format(f))
                generate_file(project_dir, infile, context, env)

    # run post-gen hook from repo_dir
    with work_in(repo_dir):
        run_hook('post_gen_project', project_dir, context)

    return project_dir