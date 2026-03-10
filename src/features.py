import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extractor import PARSERS


STATEMENT_TYPES = {
    "expression_statement", "return_statement", "assignment",
    "augmented_assignment", "delete_statement", "assert_statement",
    "pass_statement", "break_statement", "continue_statement",
    "global_statement", "nonlocal_statement", "print_statement",
}

CONTROL_FLOW_TYPES = {
    "if_statement", "elif_clause", "for_statement",
    "while_statement", "try_statement", "with_statement",
}


def _walk_tree(node, depth, counts, fn_name):
    t = node.type

    if t in STATEMENT_TYPES:
        counts["num_statements"] += 1
    if t == "if_statement":
        counts["num_if_branches"] += 1
    if t == "elif_clause":
        counts["num_elif_branches"] += 1
    if t == "else_clause":
        counts["num_else_branches"] += 1
    if t == "for_statement":
        counts["num_for_loops"] += 1
    if t == "while_statement":
        counts["num_while_loops"] += 1
    if t == "try_statement":
        counts["num_try_blocks"] += 1
    if t == "except_clause":
        counts["num_except_handlers"] += 1
    if t == "with_statement":
        counts["num_with_blocks"] += 1
    if t == "return_statement":
        counts["num_return_statements"] += 1
    if t == "raise_statement":
        counts["num_raise_statements"] += 1
    if t == "assert_statement":
        counts["num_assert_statements"] += 1
    if t == "call":
        counts["num_function_calls"] += 1
        # check for recursion
        if node.children and node.children[0].type == "identifier":
            if node.children[0].text and node.children[0].text.decode() == fn_name:
                counts["has_recursion"] = 1
    if t == "boolean_operator":
        counts["num_boolean_ops"] += 1
    if t == "comparison_operator":
        counts["num_comparisons"] += 1
    if t == "function_definition":
        counts["num_nested_functions"] += 1
    if t == "list_comprehension":
        counts["num_list_comprehensions"] += 1
    if t == "dictionary_comprehension":
        counts["num_dict_comprehensions"] += 1
    if t == "generator_expression":
        counts["num_generators"] += 1
    if t == "string":
        counts["num_string_literals"] += 1
    if t in ("integer", "float"):
        counts["num_numeric_literals"] += 1
    if t == "conditional_expression":
        counts["num_conditional_exprs"] += 1

    if t in CONTROL_FLOW_TYPES:
        new_depth = depth + 1
        if new_depth > counts["max_nesting_depth"]:
            counts["max_nesting_depth"] = new_depth
    else:
        new_depth = depth

    for child in node.children:
        _walk_tree(child, new_depth, counts, fn_name)


def _count_params(tree, counts):
    for child in tree.children:
        if child.type == "parameters":
            count = 0
            for p in child.children:
                if p.type in (
                    "identifier", "default_parameter", "typed_parameter",
                    "typed_default_parameter", "list_splat_pattern",
                    "dictionary_splat_pattern",
                ):
                    count += 1
                if p.type in ("default_parameter", "typed_default_parameter"):
                    counts["has_default_params"] = 1
                if p.type in ("list_splat_pattern", "dictionary_splat_pattern"):
                    counts["has_star_args"] = 1
            return count
    return 0


def extract_features(fn):
    source = fn["source"]
    language = fn.get("language", "python")
    name = fn["name"]

    source_bytes = source.encode("utf-8")
    tree = PARSERS[language].parse(source_bytes)
    root = tree.root_node

    # find the function_definition node
    func_node = None
    for child in root.children:
        if child.type == "function_definition":
            func_node = child
            break
        if child.type == "decorated_definition":
            for sub in child.children:
                if sub.type == "function_definition":
                    func_node = sub
                    break
            if func_node:
                break

    if not func_node:
        func_node = root

    counts = {
        "num_statements": 0,
        "num_if_branches": 0,
        "num_elif_branches": 0,
        "num_else_branches": 0,
        "num_for_loops": 0,
        "num_while_loops": 0,
        "num_try_blocks": 0,
        "num_except_handlers": 0,
        "num_with_blocks": 0,
        "num_return_statements": 0,
        "num_raise_statements": 0,
        "num_assert_statements": 0,
        "num_function_calls": 0,
        "num_boolean_ops": 0,
        "num_comparisons": 0,
        "num_nested_functions": 0,
        "num_list_comprehensions": 0,
        "num_dict_comprehensions": 0,
        "num_generators": 0,
        "num_string_literals": 0,
        "num_numeric_literals": 0,
        "num_conditional_exprs": 0,
        "max_nesting_depth": 0,
        "has_recursion": 0,
        "has_default_params": 0,
        "has_star_args": 0,
    }

    # walk the function body, not the definition itself
    body = None
    for child in func_node.children:
        if child.type == "block":
            body = child
            break

    if body:
        _walk_tree(body, 0, counts, name)

    # the function_definition itself shouldn't count as nested
    # (we walked from body, so any function_definition inside is truly nested)

    num_params = _count_params(func_node, counts)
    num_lines = source.count("\n") + 1
    num_imports = len(fn.get("imports", "").strip().split("\n")) if fn.get("imports", "").strip() else 0

    cyclomatic = (
        1
        + counts["num_if_branches"]
        + counts["num_elif_branches"]
        + counts["num_for_loops"]
        + counts["num_while_loops"]
        + counts["num_except_handlers"]
        + counts["num_boolean_ops"]
        + counts["num_conditional_exprs"]
    )

    features = {
        "num_params": num_params,
        "num_lines": num_lines,
        "num_imports": num_imports,
        "cyclomatic_complexity": cyclomatic,
    }
    features.update(counts)
    # remove intermediate keys not needed as features
    features.pop("num_conditional_exprs", None)

    return features
