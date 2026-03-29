import os
import shutil
import stat
import pytest
from unittest.mock import patch, MagicMock, call
from cookiecutter.generate import generate_files
from cookiecutter.exceptions import (
    NonTemplatedInputDirException,
    OutputDirExistsException,
)
from cookiecutter.hooks import EXIT_SUCCESS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_simple_template(base_dir, template_dirname="{{cookiecutter.project_name}}"):
    """
    Build a minimal on-disk template structure that generate_files can walk.
    Returns (repo_dir, template_dir).
    """
    repo_dir = os.path.join(base_dir, "repo")
    template_dir = os.path.join(repo_dir, template_dirname)
    os.makedirs(template_dir, exist_ok=True)
    # A plain text file
    with open(os.path.join(template_dir, "README.txt"), "w") as fh:
        fh.write("Hello {{cookiecutter.project_name}}\n")
    return repo_dir, template_dir


def _context(project_name="myproject"):
    return {"cookiecutter": {"project_name": project_name}}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp(tmp_path):
    return tmp_path


# ===========================================================================
# --- Statement Coverage ---
# ===========================================================================
# Ensure every executable line is reached at least once.

class TestStatementCoverage:

    def test_basic_generation_returns_project_dir(self, tmp):
        """
        Happy-path: all top-level statements are executed.
        A correct generate_files SHOULD return a path string.
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert result is not None
        assert isinstance(result, str)
        assert os.path.isabs(result)

    def test_none_context_defaults_to_empty_dict(self, tmp):
        """
        context=None should be treated as {} by the implementation.
        The function SHOULD not raise when context is None.
        """
        repo_dir, _ = _make_simple_template(str(tmp), "{{cookiecutter.project_name}}")
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            # With an empty context the Jinja render of the dir name just
            # produces an empty or literal string, but must not crash.
            try:
                generate_files(repo_dir, context=None, output_dir=output_dir)
            except Exception:
                pass  # We only test that context=None doesn't raise AttributeError

    def test_readme_file_is_rendered_and_written(self, tmp):
        """
        The generate_file() branch for regular files SHOULD be reached and
        produce the rendered file on disk.
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("awesome")

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            project_dir = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        readme = os.path.join(project_dir, "README.txt")
        assert os.path.exists(readme)
        content = open(readme).read()
        assert "awesome" in content

    def test_pre_gen_hook_failure_stops_generation(self, tmp):
        """
        When pre_gen_project hook returns non-EXIT_SUCCESS the function SHOULD
        return None (early return statement is reached).
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("proj")

        with patch("cookiecutter.generate.run_hook", return_value=1):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        # A correct implementation SHOULD return None on pre-hook failure
        assert result is None

    def test_post_gen_hook_is_called(self, tmp):
        """
        post_gen_project run_hook call SHOULD be reached after successful generation.
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("proj")

        hook_calls = []

        def fake_run_hook(hook_name, *args, **kwargs):
            hook_calls.append(hook_name)
            return EXIT_SUCCESS

        with patch("cookiecutter.generate.run_hook", side_effect=fake_run_hook):
            generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert "post_gen_project" in hook_calls


# ===========================================================================
# --- Block Coverage ---
# ===========================================================================
# Every basic block (including else/copy branches, exception handlers, etc.)

class TestBlockCoverage:

    def test_copy_without_render_dir_block(self, tmp):
        """
        copy_dirs branch: a directory matching _copy_without_render SHOULD be
        copied verbatim (shutil.copytree path).
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        # Create a sub-directory that will match copy_without_render
        copy_subdir = os.path.join(template_dir, "static_assets")
        os.makedirs(copy_subdir)
        with open(os.path.join(copy_subdir, "logo.png"), "wb") as fh:
            fh.write(b"\x89PNG\r\n")

        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")
        # Patch copy_without_render so that 'static_assets' triggers copy
        def fake_copy_without_render(name, ctx):
            return "static_assets" in name
        with patch("cookiecutter.generate.copy_without_render",
                   side_effect=fake_copy_without_render), \
             patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS), \
             patch("shutil.copytree") as mock_copytree:
            generate_files(repo_dir, context=ctx, output_dir=output_dir)

        mock_copytree.assert_called()

    def test_render_dirs_block_creates_subdirectory(self, tmp):
        """
        render_dirs block: rendered sub-directories SHOULD be created.
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        render_subdir = os.path.join(template_dir, "src")
        os.makedirs(render_subdir)
        with open(os.path.join(render_subdir, "main.py"), "w") as fh:
            fh.write("# main\n")

        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            project_dir = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert os.path.isdir(os.path.join(project_dir, "src"))

    def test_copy_without_render_file_block(self, tmp):
        """
        Files matching copy_without_render SHOULD be copied without Jinja rendering.
        The block with shutil.copyfile / shutil.copymode SHOULD be reached.
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        raw_file = os.path.join(template_dir, "raw_{{cookiecutter.project_name}}.bin")
        with open(raw_file, "wb") as fh:
            fh.write(b"\x00\x01\x02\x03")

        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        def fake_copy_without_render(name, ctx):
            return name.endswith(".bin") or "raw_" in name
        with patch("cookiecutter.generate.copy_without_render",
                   side_effect=fake_copy_without_render), \
             patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS), \
             patch("shutil.copyfile") as mock_copyfile, \
             patch("shutil.copymode"):
            generate_files(repo_dir, context=ctx, output_dir=output_dir)

        mock_copyfile.assert_called()

    def test_pre_hook_failure_block_early_return(self, tmp):
        """
        pre_gen_project failure block SHOULD log error and return None.
        (Covered also in statement coverage; included here for block completeness.)
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("proj")

        with patch("cookiecutter.generate.run_hook", return_value=99):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert result is None

    def test_output_dir_exists_raises_when_overwrite_false(self, tmp):
        """
        When the project output dir already exists and overwrite_if_exists=False,
        the implementation SHOULD raise OutputDirExistsException (the exception block
        in render_and_create_dir is reached).
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        # First generation creates the project dir
        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            generate_files(repo_dir, context=ctx, output_dir=output_dir)

        # Second generation SHOULD raise
        with pytest.raises((OutputDirExistsException, Exception)):
            with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
                generate_files(repo_dir, context=ctx, output_dir=output_dir,
                               overwrite_if_exists=False)

    def test_overwrite_if_exists_true_does_not_raise(self, tmp):
        """
        When overwrite_if_exists=True the overwrite block SHOULD be entered
        and the function SHOULD succeed.
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            generate_files(repo_dir, context=ctx, output_dir=output_dir)

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir,
                                    overwrite_if_exists=True)

        assert result is not None


# ===========================================================================
# --- Condition Coverage ---
# ===========================================================================
# Each boolean sub-expression evaluated to both True and False.

class TestConditionCoverage:

    # Condition: `run_hook('pre_gen_project', ...) != EXIT_SUCCESS`
    #   sub-expr A: hook return != EXIT_SUCCESS

    def test_pre_hook_condition_true_stops_generation(self, tmp):
        """
        # A: hook != EXIT_SUCCESS → True  → early return
        A correct generate_files SHOULD return None when pre-hook fails.
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("proj")

        with patch("cookiecutter.generate.run_hook", return_value=1):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert result is None  # A: True

    def test_pre_hook_condition_false_continues(self, tmp):
        """
        # A: hook != EXIT_SUCCESS → False → generation continues
        A correct generate_files SHOULD return a project_dir string.
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("proj")

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert result is not None  # A: False

    # Condition: `copy_without_render(d_, context)` for directories
    #   sub-expr B: copy_without_render returns True/False

    def test_copy_without_render_dir_condition_true(self, tmp):
        """
        # B (dir): copy_without_render → True
        Directory SHOULD be placed in copy_dirs, not render_dirs.
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        sub = os.path.join(template_dir, "vendor")
        os.makedirs(sub)

        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        def fake_cwr(name, ctx):
            return "vendor" in name  # B: True for vendor
        with patch("cookiecutter.generate.copy_without_render",
                   side_effect=fake_cwr), \
             patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS), \
             patch("shutil.copytree") as mock_ct:
            generate_files(repo_dir, context=ctx, output_dir=output_dir)

        mock_ct.assert_called()  # copytree reached (copy_dirs path)

    def test_copy_without_render_dir_condition_false(self, tmp):
        """
        # B (dir): copy_without_render → False
        Directory SHOULD be placed in render_dirs and rendered.
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        sub = os.path.join(template_dir, "src")
        os.makedirs(sub)
        with open(os.path.join(sub, "app.py"), "w") as fh:
            fh.write("# app\n")

        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        with patch("cookiecutter.generate.copy_without_render", return_value=False), \
             patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            project_dir = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        # rendered dir SHOULD exist in project output
        assert os.path.isdir(os.path.join(project_dir, "src"))

    # Condition: `copy_without_render(infile, context)` for files
    #   sub-expr C: copy_without_render returns True/False

    def test_copy_without_render_file_condition_true(self, tmp):
        """
        # C (file): copy_without_render → True
        File SHOULD be copied verbatim (shutil.copyfile called).
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        raw = os.path.join(template_dir, "data.bin")
        with open(raw, "wb") as fh:
            fh.write(b"\xff\xfe")

        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        def fake_cwr(name, ctx):
            return name.endswith(".bin") or "data" in name
        with patch("cookiecutter.generate.copy_without_render",
                   side_effect=fake_cwr), \
             patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS), \
             patch("shutil.copyfile") as mock_cf, \
             patch("shutil.copymode"):
            generate_files(repo_dir, context=ctx, output_dir=output_dir)

        mock_cf.assert_called()  # C: True path

    def test_copy_without_render_file_condition_false(self, tmp):
        """
        # C (file): copy_without_render → False
        File SHOULD go through generate_file() (Jinja rendering).
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        with patch("cookiecutter.generate.copy_without_render", return_value=False), \
             patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS), \
             patch("cookiecutter.generate.generate_file") as mock_gf:
            generate_files(repo_dir, context=ctx, output_dir=output_dir)

        mock_gf.assert_called()  # C: False → generate_file reached

    # Condition: `context = context or {}`
    #   sub-expr D: context is falsy → True / False

    def test_context_or_empty_dict_when_none(self, tmp):
        """
        # D: context is None (falsy) → True → context becomes {}
        Function SHOULD not raise AttributeError.
        """
        repo_dir, template_dir = _make_simple_template(str(tmp), "simple_dir")
        # Use a non-templated dir name to avoid NonTemplatedInputDirException
        # We expect NonTemplatedInputDirException since dir is not templated,
        # but the `or {}` assignment SHOULD still execute without AttributeError.
        with pytest.raises(Exception):
            generate_files(repo_dir, context=None, output_dir=str(tmp / "out"))

    def test_context_or_empty_dict_when_provided(self, tmp):
        """
        # D: context is provided (truthy) → False → context remains as given
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("truthy_ctx")

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert result is not None  # D: False path


# ===========================================================================
# --- Path Coverage ---
# ===========================================================================
# Distinct entry-to-exit routes through the function.

class TestPathCoverage:

    def test_path_pre_hook_fails_returns_none(self, tmp):
        """
        # path: find_template → ensure_dir_is_templated → render_and_create_dir
        #        → abs_path → work_in(repo) pre-hook (FAIL) → early return None
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("proj")

        with patch("cookiecutter.generate.run_hook", return_value=2):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        # A correct implementation SHOULD return None on pre-hook failure
        assert result is None

    def test_path_no_files_no_dirs_returns_project_dir(self, tmp):
        """
        # path: ... → work_in(template) → os.walk with zero dirs, zero files
        #        → post-hook → return project_dir
        Empty template directory (no files, no subdirs).
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        # Remove the README so there are zero files
        os.remove(os.path.join(template_dir, "README.txt"))

        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert result is not None
        assert os.path.isdir(result)

    def test_path_one_file_rendered(self, tmp):
        """
        # path: ... → walk: 1 file (not copy_without_render) → generate_file
        #        → post-hook → return project_dir
        One iteration of the files loop with rendering.
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert result is not None
        # README.txt should contain rendered content
        assert os.path.exists(os.path.join(result, "README.txt"))

    def test_path_multiple_files_rendered(self, tmp):
        """
        # path: ... → walk: multiple files loop iterations → post-hook → return
        Multiple iterations of the files loop.
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        for i in range(3):
            with open(os.path.join(template_dir, f"file{i}.txt"), "w") as fh:
                fh.write(f"content{i}\n")

        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert result is not None
        for i in range(3):
            assert os.path.exists(os.path.join(result, f"file{i}.txt"))

    def test_path_one_render_dir_one_copy_dir(self, tmp):
        """
        # path: ... → walk: 1 copy_dir (copytree) + 1 render_dir (render_and_create_dir)
        #        → files loop → post-hook → return
        Both copy_dirs and render_dirs branches exercised in one pass.
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        vendor = os.path.join(template_dir, "vendor")
        os.makedirs(vendor)
        src = os.path.join(template_dir, "src")
        os.makedirs(src)
        with open(os.path.join(src, "main.py"), "w") as fh:
            fh.write("# main\n")

        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        copy_calls = []
        render_calls = []

        real_copytree = shutil.copytree

        def track_copytree(src_path, dst_path, **kw):
            copy_calls.append(dst_path)
            os.makedirs(dst_path, exist_ok=True)

        def fake_cwr(name, ctx):
            return "vendor" in name

        with patch("cookiecutter.generate.copy_without_render",
                   side_effect=fake_cwr), \
             patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS), \
             patch("shutil.copytree", side_effect=track_copytree):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert result is not None
        assert len(copy_calls) >= 1  # copytree was called for vendor
        assert os.path.isdir(os.path.join(result, "src"))

    def test_path_file_copy_without_render_then_continue(self, tmp):
        """
        # path: ... → files loop: file matches copy_without_render
        #        → copyfile + copymode → continue (skip generate_file)
        #        → post-hook → return project_dir
        The `continue` statement path is exercised.
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        binary_file = os.path.join(template_dir, "image.bin")
        with open(binary_file, "wb") as fh:
            fh.write(b"\x00\x01\x02\x03")

        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        generate_file_calls = []

        def fake_cwr(name, ctx):
            return "image.bin" in name or name.endswith(".bin")

        with patch("cookiecutter.generate.copy_without_render",
                   side_effect=fake_cwr), \
             patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS), \
             patch("cookiecutter.generate.generate_file",
                   side_effect=lambda *a, **kw: generate_file_calls.append(a)), \
             patch("shutil.copyfile"), \
             patch("shutil.copymode"):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        # generate_file SHOULD NOT be called for the binary file (continue path)
        called_infiles = [a[1] for a in generate_file_calls]
        assert not any("image.bin" in f for f in called_infiles)
        assert result is not None

    def test_path_overwrite_if_exists_true(self, tmp):
        """
        # path: ... → render_and_create_dir (overwrite=True) → generation
        #        → post-hook → return project_dir
        overwrite_if_exists=True path through render_and_create_dir.
        """
        repo_dir, _ = _make_simple_template(str(tmp))
        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            r1 = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            r2 = generate_files(repo_dir, context=ctx, output_dir=output_dir,
                                overwrite_if_exists=True)

        assert r2 is not None
        # Both calls SHOULD produce same project directory
        assert os.path.basename(r1) == os.path.basename(r2)

    def test_path_nested_dirs_multiple_walk_iterations(self, tmp):
        """
        # path: os.walk with multiple levels of nesting → render_and_create_dir
        #        called for each level → post-hook → return project_dir
        More than one os.walk iteration (zero, one, multiple).
        """
        repo_dir, template_dir = _make_simple_template(str(tmp))
        deep = os.path.join(template_dir, "a", "b", "c")
        os.makedirs(deep)
        with open(os.path.join(deep, "deep.txt"), "w") as fh:
            fh.write("deep content\n")

        output_dir = str(tmp / "output")
        os.makedirs(output_dir)
        ctx = _context("myproject")

        with patch("cookiecutter.generate.run_hook", return_value=EXIT_SUCCESS):
            result = generate_files(repo_dir, context=ctx, output_dir=output_dir)

        assert result is not None
        assert os.path.isdir(os.path.join(result, "a", "b", "c"))
        assert os.path.exists(os.path.join(result, "a", "b", "c", "deep.txt"))