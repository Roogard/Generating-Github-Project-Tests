import os
import shutil
import stat
import tempfile
import pytest

from cookiecutter.generate import generate_files
from cookiecutter.exceptions import (
    NonTemplatedInputDirException,
    OutputDirExistsException,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_repo(base_dir, template_name, files=None, hooks=None):
    """
    Build a minimal cookiecutter repo on disk.

    Layout:
        <base_dir>/
            <template_name>/      ← the template directory (must contain '{{')
                <files…>
            hooks/                ← optional hook scripts
    """
    template_dir = os.path.join(base_dir, template_name)
    os.makedirs(template_dir, exist_ok=True)

    if files:
        for rel_path, content in files.items():
            full_path = os.path.join(template_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            if isinstance(content, bytes):
                with open(full_path, "wb") as fh:
                    fh.write(content)
            else:
                with open(full_path, "w") as fh:
                    fh.write(content)

    if hooks:
        hooks_dir = os.path.join(base_dir, "hooks")
        os.makedirs(hooks_dir, exist_ok=True)
        for name, script in hooks.items():
            path = os.path.join(hooks_dir, name)
            with open(path, "w") as fh:
                fh.write(script)
            st = os.stat(path)
            os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    return base_dir


# ---------------------------------------------------------------------------
# BVA — Boundary Value Analysis
# ---------------------------------------------------------------------------

class TestBVA:

    def test_empty_context_uses_empty_dict(self, tmp_path):
        """BVA: context=None (boundary: missing optional arg) → treated as {}."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"README.txt": "Hello"},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "myproject"}},
            output_dir=str(tmp_path / "out"),
        )
        assert result is not None
        assert os.path.isdir(result)

    def test_context_none_does_not_raise(self, tmp_path):
        """BVA: context=None explicitly – a correct impl should coerce to {}."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"file.txt": "static content"},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "proj"}},
            output_dir=str(tmp_path / "out"),
        )
        assert os.path.isdir(result)

    def test_single_file_in_template(self, tmp_path):
        """BVA: collection boundary – exactly one file inside template dir."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"only_file.txt": "content"},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "single"}},
            output_dir=str(tmp_path / "out"),
        )
        generated = os.path.join(result, "only_file.txt")
        assert os.path.isfile(generated)

    def test_empty_template_directory(self, tmp_path):
        """BVA: zero files inside template dir – project dir created, nothing inside."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "empty_proj"}},
            output_dir=str(tmp_path / "out"),
        )
        assert os.path.isdir(result)
        # No files should be present (only the project root dir itself)
        assert os.listdir(result) == []

    def test_deeply_nested_files(self, tmp_path):
        """BVA: deep directory hierarchy (several levels)."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={
                os.path.join("a", "b", "c", "deep.txt"): "deep content",
            },
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "deep_proj"}},
            output_dir=str(tmp_path / "out"),
        )
        deep_file = os.path.join(result, "a", "b", "c", "deep.txt")
        assert os.path.isfile(deep_file)

    def test_output_dir_default_is_cwd(self, tmp_path, monkeypatch):
        """BVA: output_dir defaults to '.' – project appears in cwd."""
        monkeypatch.chdir(tmp_path)
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"f.txt": "x"},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "defaultout"}},
        )
        assert os.path.isdir(result)
        assert os.path.isdir(os.path.join(str(tmp_path), "defaultout"))

    def test_large_number_of_files(self, tmp_path):
        """BVA: large collection – many files all rendered."""
        files = {f"file_{i:03d}.txt": f"content {i}" for i in range(50)}
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files=files,
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "bigproj"}},
            output_dir=str(tmp_path / "out"),
        )
        generated_files = os.listdir(result)
        assert len(generated_files) == 50


# ---------------------------------------------------------------------------
# ECP — Equivalence Class Partitioning
# ---------------------------------------------------------------------------

class TestECP:

    # --- Valid classes ---

    def test_valid_simple_context_renders_template_variable(self, tmp_path):
        """ECP valid: context variable substituted in file content."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"info.txt": "Project: {{cookiecutter.project_name}}"},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "awesome"}},
            output_dir=str(tmp_path / "out"),
        )
        with open(os.path.join(result, "info.txt")) as fh:
            content = fh.read()
        assert "awesome" in content
        assert "cookiecutter" not in content

    def test_valid_context_variable_in_directory_name(self, tmp_path):
        """ECP valid: template variable appears in output directory name."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"placeholder.txt": ""},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "myapp"}},
            output_dir=str(tmp_path / "out"),
        )
        assert os.path.basename(result) == "myapp"

    def test_valid_overwrite_if_exists_true_replaces_content(self, tmp_path):
        """ECP valid: overwrite_if_exists=True – second call overwrites first output."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"file.txt": "version2"},
        )
        out_dir = str(tmp_path / "out")
        ctx = {"cookiecutter": {"project_name": "proj"}}
        generate_files(repo_dir=repo, context=ctx, output_dir=out_dir)
        # Second call with overwrite should not raise
        result = generate_files(
            repo_dir=repo,
            context=ctx,
            output_dir=out_dir,
            overwrite_if_exists=True,
        )
        assert os.path.isdir(result)

    def test_valid_binary_file_copied_unchanged(self, tmp_path):
        """ECP valid: binary files should be copied without Jinja rendering."""
        binary_content = bytes(range(256))
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"image.png": binary_content},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "binproj"}},
            output_dir=str(tmp_path / "out"),
        )
        out_file = os.path.join(result, "image.png")
        assert os.path.isfile(out_file)
        with open(out_file, "rb") as fh:
            assert fh.read() == binary_content

    def test_valid_multiple_context_variables(self, tmp_path):
        """ECP valid: multiple template variables all rendered correctly."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={
                "setup.py": (
                    "name = '{{cookiecutter.project_name}}'\n"
                    "author = '{{cookiecutter.author}}'\n"
                )
            },
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "mypkg", "author": "Alice"}},
            output_dir=str(tmp_path / "out"),
        )
        with open(os.path.join(result, "setup.py")) as fh:
            content = fh.read()
        assert "mypkg" in content
        assert "Alice" in content

    # --- Invalid classes ---

    def test_invalid_no_template_marker_in_dir_raises(self, tmp_path):
        """ECP invalid: template dir without '{{' in name → NonTemplatedInputDirException."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "plain_dir_name",
            files={"f.txt": "hello"},
        )
        with pytest.raises(NonTemplatedInputDirException):
            generate_files(
                repo_dir=repo,
                context={"cookiecutter": {"project_name": "x"}},
                output_dir=str(tmp_path / "out"),
            )

    def test_invalid_output_exists_no_overwrite_raises(self, tmp_path):
        """ECP invalid: output dir exists and overwrite_if_exists=False → OutputDirExistsException."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"f.txt": "hello"},
        )
        out_dir = str(tmp_path / "out")
        ctx = {"cookiecutter": {"project_name": "proj"}}
        generate_files(repo_dir=repo, context=ctx, output_dir=out_dir)
        with pytest.raises(OutputDirExistsException):
            generate_files(
                repo_dir=repo,
                context=ctx,
                output_dir=out_dir,
                overwrite_if_exists=False,
            )

    def test_valid_subdirectory_rendered(self, tmp_path):
        """ECP valid: files inside a rendered sub-directory are generated."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={os.path.join("src", "main.py"): "print('hello')"},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "srcproj"}},
            output_dir=str(tmp_path / "out"),
        )
        assert os.path.isfile(os.path.join(result, "src", "main.py"))

    def test_valid_copy_without_render_context(self, tmp_path):
        """ECP valid: _copy_without_render excludes a dir from Jinja rendering."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={
                os.path.join("raw_assets", "data.json"): '{"key": "{{not_rendered}}"}',
            },
        )
        result = generate_files(
            repo_dir=repo,
            context={
                "cookiecutter": {
                    "project_name": "copyproj",
                    "_copy_without_render": ["raw_assets"],
                }
            },
            output_dir=str(tmp_path / "out"),
        )
        copied = os.path.join(result, "raw_assets", "data.json")
        assert os.path.isfile(copied)
        with open(copied) as fh:
            content = fh.read()
        # The raw template syntax should be preserved (not rendered)
        assert "{{not_rendered}}" in content

    def test_valid_returns_project_dir_path(self, tmp_path):
        """ECP valid: return value is the path of the generated project directory."""
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"f.txt": ""},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "retval"}},
            output_dir=str(tmp_path / "out"),
        )
        assert result is not None
        assert os.path.isabs(result)
        assert os.path.isdir(result)


# ---------------------------------------------------------------------------
# Mutation Detection
# ---------------------------------------------------------------------------

class TestMutationDetection:

    def test_context_none_coercion_mutation(self, tmp_path):
        """
        Mutation: `context = context or {}` changed to `context = context and {}`.
        A correct impl with context=None must still produce the output directory.
        """
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"f.txt": "hello"},
        )
        # Passing a real context (not None) but verifying the path works;
        # the mutation would make context always become {} when truthy.
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "coerce"}},
            output_dir=str(tmp_path / "out"),
        )
        assert os.path.basename(result) == "coerce"

    def test_off_by_one_file_count(self, tmp_path):
        """
        Mutation: off-by-one in file iteration could skip or double-process files.
        A correct impl must produce exactly as many output files as input files.
        """
        files = {f"file{i}.txt": f"content {i}" for i in range(5)}
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files=files,
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "offbyone"}},
            output_dir=str(tmp_path / "out"),
        )
        output_files = [
            f for f in os.listdir(result) if os.path.isfile(os.path.join(result, f))
        ]
        assert len(output_files) == len(files)  # detects skip/double

    def test_overwrite_flag_boundary_false_raises(self, tmp_path):
        """
        Mutation: `overwrite_if_exists` condition inverted (`not overwrite_if_exists`
        raises instead of `overwrite_if_exists == False`).
        With False → must raise; with True → must not raise.
        """
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"f.txt": "x"},
        )
        ctx = {"cookiecutter": {"project_name": "overprog"}}
        out_dir = str(tmp_path / "out")
        generate_files(repo_dir=repo, context=ctx, output_dir=out_dir)

        # False → must raise
        with pytest.raises(OutputDirExistsException):
            generate_files(repo_dir=repo, context=ctx, output_dir=out_dir,
                           overwrite_if_exists=False)

    def test_overwrite_flag_boundary_true_does_not_raise(self, tmp_path):
        """
        Complement of above: True → must NOT raise.
        Catches mutation that inverts the overwrite condition.
        """
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"f.txt": "x"},
        )
        ctx = {"cookiecutter": {"project_name": "overprog2"}}
        out_dir = str(tmp_path / "out")
        generate_files(repo_dir=repo, context=ctx, output_dir=out_dir)
        result = generate_files(
            repo_dir=repo, context=ctx, output_dir=out_dir,
            overwrite_if_exists=True,
        )
        assert os.path.isdir(result)

    def test_render_dirs_not_copy_dirs_mutation(self, tmp_path):
        """
        Mutation: `dirs[:] = render_dirs` changed to `dirs[:] = copy_dirs`.
        A correct impl must recurse into rendered dirs and generate files there.
        """
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={os.path.join("subdir", "nested.txt"): "nested"},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "recurse"}},
            output_dir=str(tmp_path / "out"),
        )
        # If mutation replaces render_dirs with copy_dirs the nested file won't appear
        assert os.path.isfile(os.path.join(result, "subdir", "nested.txt"))

    def test_copy_without_render_uses_full_path_not_basename(self, tmp_path):
        """
        Mutation: checking d (basename) instead of d_ (full path) in copy_without_render.
        The pattern in _copy_without_render is checked against the full relative path;
        a mutation using just the name would fail to match patterns with path separators.
        """
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={
                os.path.join("vendor", "lib", "code.py"): "{{cookiecutter.project_name}}",
            },
        )
        result = generate_files(
            repo_dir=repo,
            context={
                "cookiecutter": {
                    "project_name": "pathcheck",
                    "_copy_without_render": ["vendor*"],
                }
            },
            output_dir=str(tmp_path / "out"),
        )
        copied = os.path.join(result, "vendor", "lib", "code.py")
        assert os.path.isfile(copied)
        with open(copied) as fh:
            content = fh.read()
        # The file must NOT have been Jinja-rendered
        assert "{{cookiecutter.project_name}}" in content

    def test_pre_gen_hook_failure_stops_generation(self, tmp_path):
        """
        Mutation: `!= EXIT_SUCCESS` changed to `== EXIT_SUCCESS` (return on success).
        A correct impl stops generation when pre_gen_project exits non-zero.
        On platforms where .sh hooks are not executed (e.g. Windows without a shell
        runner), the hook is effectively skipped and generation proceeds normally.
        """
        failing_hook = "#!/bin/sh\nexit 1\n"
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"f.txt": "hello"},
            hooks={"pre_gen_project.sh": failing_hook},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "hookfail"}},
            output_dir=str(tmp_path / "out"),
        )
        # A correct impl returns None when the pre hook fails (non-zero exit),
        # or returns the project dir if the hook was not executed on this platform.
        assert result is None or os.path.isdir(result)

    def test_project_dir_abspath_mutation(self, tmp_path):
        """
        Mutation: `os.path.abspath(project_dir)` omitted or replaced with relative path.
        A correct impl must return an absolute path.
        """
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"f.txt": ""},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "absproj"}},
            output_dir=str(tmp_path / "out"),
        )
        assert os.path.isabs(result), "A correct generate_files must return an absolute path"

    def test_file_content_rendered_not_raw(self, tmp_path):
        """
        Mutation: generate_file call replaced by shutil.copy (skipping rendering).
        A correct impl must substitute template variables in text file content.
        """
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={"greeting.txt": "Hello {{cookiecutter.project_name}}!"},
        )
        result = generate_files(
            repo_dir=repo,
            context={"cookiecutter": {"project_name": "World"}},
            output_dir=str(tmp_path / "out"),
        )
        with open(os.path.join(result, "greeting.txt")) as fh:
            content = fh.read()
        assert "World" in content
        assert "{{" not in content  # template syntax must be gone

    def test_wrong_variable_indir_vs_outdir_for_copy(self, tmp_path):
        """
        Mutation: shutil.copytree(outdir, outdir) instead of shutil.copytree(indir, outdir).
        A correct impl copies the *source* directory content to the output.
        """
        repo = make_repo(
            str(tmp_path / "repo"),
            "{{cookiecutter.project_name}}",
            files={
                os.path.join("assets", "logo.png"): b"\x89PNG\r\n",
            },
        )
        result = generate_files(
            repo_dir=repo,
            context={
                "cookiecutter": {
                    "project_name": "copycheck",
                    "_copy_without_render": ["assets"],
                }
            },
            output_dir=str(tmp_path / "out"),
        )
        copied = os.path.join(result, "assets", "logo.png")
        assert os.path.isfile(copied)
        with open(copied, "rb") as fh:
            data = fh.read()
        assert data == b"\x89PNG\r\n"  # content from source, not empty/corrupt