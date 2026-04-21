"""Clone a GitHub repo and extract all Python function definitions using tree-sitter."""
import json
import os
import re
import subprocess
import urllib.request

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, QueryCursor

LANGUAGES = {"python": Language(tspython.language())}
PARSERS = {name: Parser(lang) for name, lang in LANGUAGES.items()}
EXTENSIONS = {".py": "python"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}

FUNCTION_QUERIES = {
    "python": """
        (function_definition name: (identifier) @fn_name) @fn
        (decorated_definition (function_definition name: (identifier) @fn_name)) @fn
    """,
}
IMPORT_QUERIES = {
    "python": "(import_statement) @imp (import_from_statement) @imp",
}


def clone_repo(url, target_dir):
    subprocess.run(["git", "clone", "--depth=1", url, target_dir], check=True)


def clone_repo_at_commit(url, target_dir, commit_sha):
    subprocess.run(["git", "clone", url, target_dir], check=True)
    subprocess.run(["git", "checkout", commit_sha], cwd=target_dir, check=True)


def extract_functions(repo_path):
    functions = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            language = EXTENSIONS.get(ext)
            if not language:
                continue
            path = os.path.join(root, file)
            with open(path, "rb") as f:
                source_bytes = f.read()
            tree = PARSERS[language].parse(source_bytes)
            query = LANGUAGES[language].query(FUNCTION_QUERIES[language])
            cursor = QueryCursor(query)
            imports = _get_imports(source_bytes, language)
            rel_path = os.path.relpath(path, repo_path)
            seen = set()
            for _pattern_idx, match_captures in cursor.matches(tree.root_node):
                fn_list = match_captures.get("fn", [])
                name_list = match_captures.get("fn_name", [])
                if not fn_list or not name_list:
                    continue
                fn_node = fn_list[0]
                name_node = name_list[0]
                span = (fn_node.start_byte, fn_node.end_byte)
                if span in seen:
                    continue
                seen.add(span)
                class_name = None
                parent = fn_node.parent
                while parent is not None:
                    if parent.type == "class_definition":
                        for child in parent.children:
                            if child.type == "identifier":
                                class_name = source_bytes[child.start_byte:child.end_byte].decode(errors="replace")
                                break
                        break
                    parent = parent.parent
                functions.append({
                    "name": source_bytes[name_node.start_byte:name_node.end_byte].decode(errors="replace"),
                    "source": source_bytes[fn_node.start_byte:fn_node.end_byte].decode(errors="replace"),
                    "language": language,
                    "file_path": rel_path,
                    "imports": imports,
                    "start_line": fn_node.start_point[0] + 1,
                    "end_line": fn_node.end_point[0] + 1,
                    "class_name": class_name,
                })
    return functions


def read_readme(repo_path: str, max_chars: int = 3000) -> str:
    for name in ("README.md", "README.rst", "README.txt", "README"):
        p = os.path.join(repo_path, name)
        if os.path.isfile(p):
            return open(p, encoding="utf-8", errors="replace").read()[:max_chars]
    return ""


def get_issue_description(repo_path: str, github_url: str, max_chars: int = 3000) -> str:
    """Return the GitHub issue/PR body referenced by the HEAD commit. Empty string on any failure."""
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%B", "HEAD"],
            cwd=repo_path, capture_output=True, text=True, timeout=10,
        )
        commit_msg = r.stdout if r.returncode == 0 else ""
        numbers = re.findall(r'#(\d+)', commit_msg)
        if not numbers:
            return ""
        m = re.search(r'github\.com/([^/]+/[^/?#]+)', github_url)
        if not m:
            return ""
        slug = m.group(1).rstrip("/").removesuffix(".git")
        issue_num = numbers[0]
        url = f"https://api.github.com/repos/{slug}/issues/{issue_num}"
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "ggpt/1.0"}
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        title = data.get("title", "")
        body = data.get("body") or ""
        return f"# {title}\n\n{body}"[:max_chars]
    except Exception:
        return ""


def extract_callees(fn_source: str, all_functions: list, max_callees: int = 4) -> list:
    """Return function dicts for internal helpers called by fn_source (1 level deep).

    Parses fn_source with tree-sitter to collect call names, then matches against
    all_functions extracted from the same repo. Capped at max_callees to keep the
    LLM context from growing unbounded.
    """
    try:
        source_bytes = fn_source.encode("utf-8")
        tree = PARSERS["python"].parse(source_bytes)
    except Exception:
        return []

    call_query = LANGUAGES["python"].query("(call function: [(identifier) @name (attribute attribute: (identifier) @name)])")
    cursor = QueryCursor(call_query)
    called = {
        source_bytes[node.start_byte:node.end_byte].decode(errors="replace")
        for node in cursor.captures(tree.root_node).get("name", [])
    }

    seen_names: set = set()
    callees = []
    for fn in all_functions:
        if fn["name"] in called and fn["name"] not in seen_names:
            seen_names.add(fn["name"])
            callees.append({"name": fn["name"], "source": fn["source"]})
            if len(callees) >= max_callees:
                break
    return callees


def extract_test_examples(repo_path: str, fn_names: set, max_examples: int = 3) -> dict:
    """Find existing test functions in the repo that call any of fn_names.

    Returns {fn_name: [test_source, ...]} with at most max_examples per function.
    Only searches files whose names start with 'test_' or end with '_test.py'.
    """
    results: dict = {name: [] for name in fn_names}
    call_query_str = IMPORT_QUERIES.get("python")  # reuse parser infra

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file in files:
            if not (file.startswith("test_") or file.endswith("_test.py")):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "rb") as f:
                    source_bytes = f.read()
            except OSError:
                continue
            tree = PARSERS["python"].parse(source_bytes)
            # Find all top-level function definitions that start with 'test_'
            query = LANGUAGES["python"].query(FUNCTION_QUERIES["python"])
            cursor = QueryCursor(query)
            for _pattern_idx, match_captures in cursor.matches(tree.root_node):
                fn_list = match_captures.get("fn", [])
                name_list = match_captures.get("fn_name", [])
                if not fn_list or not name_list:
                    continue
                fn_node = fn_list[0]
                name_node = name_list[0]
                test_name = source_bytes[name_node.start_byte:name_node.end_byte].decode(errors="replace")
                if not test_name.startswith("test_"):
                    continue
                fn_source = source_bytes[fn_node.start_byte:fn_node.end_byte].decode(errors="replace")
                # Check which target functions are called inside this test body
                for target in fn_names:
                    if len(results[target]) >= max_examples:
                        continue
                    # Simple string search is fast enough and avoids a second parse
                    if target in fn_source:
                        results[target].append(fn_source)
                        break  # one test counts for at most one target

    return {k: v for k, v in results.items() if v}


def _get_imports(source_bytes, language):
    query_str = IMPORT_QUERIES.get(language)
    if not query_str:
        return ""
    tree = PARSERS[language].parse(source_bytes)
    query = LANGUAGES[language].query(query_str)
    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)
    lines = [source_bytes[node.start_byte:node.end_byte].decode(errors="replace")
             for node in captures.get("imp", [])]
    return "\n".join(lines)


