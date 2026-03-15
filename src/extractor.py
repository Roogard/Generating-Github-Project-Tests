"""
Function extractor.

Clones a GitHub repo with git, then walks every .py file and uses tree-sitter to
parse it and extract all top-level and nested function definitions.

Each function is returned as a plain dict with:
    name       — function name
    source     — full source text of the function
    language   — "python"
    file_path  — relative path inside the repo
    imports    — all import statements from the same file (used as context for test generation)
"""
import subprocess
import os

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, QueryCursor

LANGUAGES = {
    "python": Language(tspython.language()),
}

PARSERS = {name: Parser(lang) for name, lang in LANGUAGES.items()}

EXTENSIONS = {
    ".py": "python",
}

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
            captures = cursor.captures(tree.root_node)

            imports = get_imports(source_bytes, language)
            rel_path = os.path.relpath(path, repo_path)

            fn_nodes = captures.get("fn", [])
            fn_name_nodes = captures.get("fn_name", [])

            seen = set()
            for fn_node, name_node in zip(fn_nodes, fn_name_nodes):
                span = (fn_node.start_byte, fn_node.end_byte)
                if span in seen:
                    continue
                seen.add(span)

                functions.append({
                    "name": source_bytes[name_node.start_byte:name_node.end_byte].decode(),
                    "source": source_bytes[fn_node.start_byte:fn_node.end_byte].decode(),
                    "language": language,
                    "file_path": rel_path,
                    "imports": imports,
                })

    return functions


def get_imports(source_bytes, language):
    query_str = IMPORT_QUERIES.get(language)
    if not query_str:
        return ""

    tree = PARSERS[language].parse(source_bytes)
    query = LANGUAGES[language].query(query_str)
    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)

    lines = []
    for node in captures.get("imp", []):
        lines.append(source_bytes[node.start_byte:node.end_byte].decode())

    return "\n".join(lines)
