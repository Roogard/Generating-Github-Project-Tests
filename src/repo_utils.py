"""Git clone helper.

Function-extraction (tree-sitter), callee analysis, and issue-fetching
helpers were removed in the issue-driven pivot — the agent localizes
relevant code itself via tools, and issue text is supplied by the caller
(user paste for `repo` source, HF dataset for `swtbench`).
"""
import subprocess


def clone_repo(url: str, target_dir: str) -> None:
    subprocess.run(["git", "clone", "--depth=1", url, target_dir], check=True)
