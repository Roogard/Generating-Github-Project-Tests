"""Tool kit safety properties.

These pin three Claude-Code-style invariants:

  1. Path safety — tools refuse paths that escape both repo_dir and test_dir.
  2. Read-before-Edit — Edit refuses to operate on files the agent hasn't Read.
  3. Test-file write hygiene — Write to ctx.test_file_path strips markdown
     fences and relative imports.
"""
from pathlib import Path

from src.skills.tools import build_tools


def _get_tool(ctx, name):
    return next(t for t in build_tools(ctx) if t.name == name)


def test_glob_finds_files_under_repo(ctx):
    (Path(ctx.repo_dir) / "foo.py").write_text("x = 1\n")
    glob_tool = _get_tool(ctx, "Glob")
    out = glob_tool.invoke({"pattern": "*.py"})
    assert "foo.py" in out


def test_read_outside_repo_rejected(ctx, tmp_path):
    """Path safety: a file outside both repo_dir and test_dir is rejected."""
    outside = tmp_path / "elsewhere.txt"
    outside.write_text("secret")
    read_tool = _get_tool(ctx, "Read")
    out = read_tool.invoke({"file_path": str(outside)})
    assert "ERROR" in out
    assert "outside" in out


def test_edit_requires_prior_read(ctx):
    """Edit refuses on a file the agent hasn't Read this session
    (mirrors Claude Code's must-Read-before-Edit rule)."""
    f = Path(ctx.repo_dir) / "x.py"
    f.write_text("hello")
    edit_tool = _get_tool(ctx, "Edit")
    out = edit_tool.invoke({
        "file_path": "x.py", "old_string": "hello", "new_string": "world",
    })
    assert "must Read" in out


def test_edit_works_after_read(ctx):
    """Once Read is called, Edit is allowed on that file."""
    f = Path(ctx.repo_dir) / "x.py"
    f.write_text("hello")
    read_tool = _get_tool(ctx, "Read")
    read_tool.invoke({"file_path": "x.py"})
    edit_tool = _get_tool(ctx, "Edit")
    out = edit_tool.invoke({
        "file_path": "x.py", "old_string": "hello", "new_string": "world",
    })
    assert "edited" in out
    assert f.read_text() == "world"


def test_write_to_test_file_strips_markdown_fence(ctx):
    write_tool = _get_tool(ctx, "Write")
    code = "```python\nimport pytest\ndef test_x(): pass\n```"
    out = write_tool.invoke({"file_path": ctx.test_file_path, "content": code})
    assert "wrote" in out
    on_disk = Path(ctx.test_file_path).read_text()
    assert "```" not in on_disk
    assert "def test_x" in on_disk


def test_write_to_test_file_strips_relative_imports(ctx):
    write_tool = _get_tool(ctx, "Write")
    code = "from . import sibling\nimport os\ndef test_x(): pass\n"
    write_tool.invoke({"file_path": ctx.test_file_path, "content": code})
    on_disk = Path(ctx.test_file_path).read_text()
    assert "from . import" not in on_disk
    assert "import os" in on_disk
