import ast
import copy
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile


MUTMUT_TIMEOUT = 600
CUSTOM_MUTANT_TIMEOUT = 30

IS_WINDOWS = platform.system() == "Windows"


def run_mutmut(function_file, test_file, repo_clone_dir, original_repo_path=None):
    with open(function_file, "r", encoding="utf-8") as f:
        source = f.read()

    mutmut_killed = set()
    mutmut_survived = set()
    mutmut_total = 0

    # mutmut 3.x does not support Windows — skip mutmut phase on Windows
    if not IS_WINDOWS:
        tmp = tempfile.mkdtemp()
        try:
            mutmut_killed, mutmut_survived, mutmut_total = _run_mutmut_phase(
                function_file, test_file, repo_clone_dir, tmp
            )
        except subprocess.TimeoutExpired:
            pass
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # Resolve the original source file in the repo clone so tests' imports
    # resolve to the mutated code instead of always hitting the unmutated original
    if original_repo_path:
        original_file = os.path.join(repo_clone_dir, original_repo_path)
    else:
        original_file = None

    custom_killed, custom_survived, custom_total = _run_custom_mutants(
        function_file, test_file, repo_clone_dir, source,
        start_id=mutmut_total + 1,
        original_file=original_file,
    )

    killed = mutmut_killed | custom_killed
    survived = mutmut_survived | custom_survived
    total = mutmut_total + custom_total

    return {
        "total_mutants": total,
        "killed": killed,
        "survived": survived,
        "mutmut_mutants": mutmut_total,
        "custom_mutants": custom_total,
    }


def _run_mutmut_phase(function_file, test_file, repo_clone_dir, tmp):
    src_dir = os.path.join(tmp, "src_module")
    test_dir = os.path.join(tmp, "tests")
    os.makedirs(src_dir)
    os.makedirs(test_dir)

    fn_basename = os.path.basename(function_file)
    fn_dest = os.path.join(src_dir, fn_basename)
    shutil.copy2(function_file, fn_dest)
    with open(os.path.join(src_dir, "__init__.py"), "w") as f:
        pass

    test_basename = os.path.basename(test_file)
    test_dest = os.path.join(test_dir, test_basename)
    shutil.copy2(test_file, test_dest)

    env = os.environ.copy()
    paths = [tmp, repo_clone_dir]
    existing = env.get("PYTHONPATH", "")
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)

    subprocess.run(
        [sys.executable, "-m", "mutmut", "run",
         "--paths-to-mutate", fn_dest,
         "--tests-dir", test_dir,
         "--no-progress",
         "--CI"],
        capture_output=True, text=True, env=env, cwd=tmp,
        timeout=MUTMUT_TIMEOUT,
    )

    # mutmut 3.x stores results in a JSON meta file inside mutants/
    meta_path = os.path.join(tmp, "mutants", "meta.json")
    return _parse_mutmut_results(meta_path)


def _parse_mutmut_results(meta_path):
    killed = set()
    survived = set()

    if not os.path.exists(meta_path):
        return killed, survived, 0

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    exit_codes = meta.get("exit_code_by_key", {})
    for i, (key, code) in enumerate(exit_codes.items()):
        mid = i + 1
        # exit code 0 = tests passed = mutant survived; nonzero = killed
        if code != 0:
            killed.add(mid)
        else:
            survived.add(mid)

    total = len(killed) + len(survived)
    return killed, survived, total


def _generate_custom_mutants(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    mutants = []

    # Condition negation: if x: -> if not x:
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            mutated = copy.deepcopy(tree)
            for m_node in ast.walk(mutated):
                if isinstance(m_node, ast.If) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                    m_node.test = ast.UnaryOp(op=ast.Not(), operand=m_node.test)
                    ast.fix_missing_locations(mutated)
                    break
            try:
                mutants.append(("cond_neg", ast.unparse(mutated), f"negate condition at line {node.lineno}"))
            except Exception:
                pass

    # Boundary shifts on comparisons with numeric constants
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for i, comparator in enumerate(node.comparators):
                if isinstance(comparator, ast.Constant) and isinstance(comparator.value, (int, float)):
                    # +1 shift
                    mutated = copy.deepcopy(tree)
                    for m_node in ast.walk(mutated):
                        if isinstance(m_node, ast.Compare) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                            m_node.comparators[i] = ast.Constant(value=comparator.value + 1)
                            ast.fix_missing_locations(mutated)
                            break
                    try:
                        mutants.append(("boundary_up", ast.unparse(mutated), f"boundary +1 at line {node.lineno}"))
                    except Exception:
                        pass

                    # -1 shift
                    mutated = copy.deepcopy(tree)
                    for m_node in ast.walk(mutated):
                        if isinstance(m_node, ast.Compare) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                            m_node.comparators[i] = ast.Constant(value=comparator.value - 1)
                            ast.fix_missing_locations(mutated)
                            break
                    try:
                        mutants.append(("boundary_down", ast.unparse(mutated), f"boundary -1 at line {node.lineno}"))
                    except Exception:
                        pass

    # Return value mutation: return x -> return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and node.value is not None:
            mutated = copy.deepcopy(tree)
            for m_node in ast.walk(mutated):
                if isinstance(m_node, ast.Return) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                    m_node.value = ast.Constant(value=None)
                    ast.fix_missing_locations(mutated)
                    break
            try:
                mutants.append(("ret_none", ast.unparse(mutated), f"return None at line {node.lineno}"))
            except Exception:
                pass

    # not removal: not expr -> expr
    for node in ast.walk(tree):
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            mutated = copy.deepcopy(tree)
            _replace_not_node(mutated, node.lineno, node.col_offset)
            ast.fix_missing_locations(mutated)
            try:
                mutants.append(("not_removal", ast.unparse(mutated), f"remove not at line {node.lineno}"))
            except Exception:
                pass

    # Augmented assignment swap: += -> -=, *= -> /=
    aug_swaps = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult}
    for node in ast.walk(tree):
        if isinstance(node, ast.AugAssign) and type(node.op) in aug_swaps:
            mutated = copy.deepcopy(tree)
            for m_node in ast.walk(mutated):
                if isinstance(m_node, ast.AugAssign) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                    m_node.op = aug_swaps[type(node.op)]()
                    ast.fix_missing_locations(mutated)
                    break
            try:
                mutants.append(("aug_swap", ast.unparse(mutated), f"swap augmented op at line {node.lineno}"))
            except Exception:
                pass

    # Boolean constant swap: True -> False, False -> True
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, bool):
            mutated = copy.deepcopy(tree)
            for m_node in ast.walk(mutated):
                if isinstance(m_node, ast.Constant) and isinstance(m_node.value, bool) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                    m_node.value = not m_node.value
                    ast.fix_missing_locations(mutated)
                    break
            try:
                mutants.append(("bool_swap", ast.unparse(mutated), f"swap bool at line {node.lineno}"))
            except Exception:
                pass

    # Exception type broadening: except ValueError -> except Exception
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is not None:
            if isinstance(node.type, ast.Name) and node.type.id != "Exception":
                mutated = copy.deepcopy(tree)
                for m_node in ast.walk(mutated):
                    if isinstance(m_node, ast.ExceptHandler) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                        m_node.type = ast.Name(id="Exception", ctx=ast.Load())
                        ast.fix_missing_locations(mutated)
                        break
                try:
                    mutants.append(("exc_broaden", ast.unparse(mutated), f"broaden except at line {node.lineno}"))
                except Exception:
                    pass

    # Arithmetic operator swap in BinOp: + -> -, * -> /, etc.
    arith_swaps = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult,
                   ast.FloorDiv: ast.Div, ast.Mod: ast.Mult, ast.Pow: ast.Mult}
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and type(node.op) in arith_swaps:
            mutated = copy.deepcopy(tree)
            for m_node in ast.walk(mutated):
                if isinstance(m_node, ast.BinOp) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                    m_node.op = arith_swaps[type(node.op)]()
                    ast.fix_missing_locations(mutated)
                    break
            try:
                mutants.append(("arith_swap", ast.unparse(mutated), f"swap arithmetic op at line {node.lineno}"))
            except Exception:
                pass

    # Comparison operator swap: < -> <=, > -> >=, == -> !=, etc.
    cmp_swaps = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
                 ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for j, op in enumerate(node.ops):
                if type(op) in cmp_swaps:
                    mutated = copy.deepcopy(tree)
                    for m_node in ast.walk(mutated):
                        if isinstance(m_node, ast.Compare) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                            m_node.ops[j] = cmp_swaps[type(op)]()
                            ast.fix_missing_locations(mutated)
                            break
                    try:
                        mutants.append(("cmp_swap", ast.unparse(mutated), f"swap comparison op at line {node.lineno}"))
                    except Exception:
                        pass

    # Logical operator swap: and -> or, or -> and
    logic_swaps = {ast.And: ast.Or, ast.Or: ast.And}
    for node in ast.walk(tree):
        if isinstance(node, ast.BoolOp) and type(node.op) in logic_swaps:
            mutated = copy.deepcopy(tree)
            for m_node in ast.walk(mutated):
                if isinstance(m_node, ast.BoolOp) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                    m_node.op = logic_swaps[type(node.op)]()
                    ast.fix_missing_locations(mutated)
                    break
            try:
                mutants.append(("logic_swap", ast.unparse(mutated), f"swap logical op at line {node.lineno}"))
            except Exception:
                pass

    # Unary sign flip: -x -> +x, +x -> -x
    sign_swaps = {ast.USub: ast.UAdd, ast.UAdd: ast.USub}
    for node in ast.walk(tree):
        if isinstance(node, ast.UnaryOp) and type(node.op) in sign_swaps:
            mutated = copy.deepcopy(tree)
            for m_node in ast.walk(mutated):
                if isinstance(m_node, ast.UnaryOp) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                    m_node.op = sign_swaps[type(node.op)]()
                    ast.fix_missing_locations(mutated)
                    break
            try:
                mutants.append(("sign_flip", ast.unparse(mutated), f"flip sign at line {node.lineno}"))
            except Exception:
                pass

    # Statement deletion: remove each statement in function bodies
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for stmt_idx in range(len(node.body)):
                if len(node.body) <= 1:
                    continue
                mutated = copy.deepcopy(tree)
                for m_node in ast.walk(mutated):
                    if isinstance(m_node, (ast.FunctionDef, ast.AsyncFunctionDef)) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                        m_node.body = m_node.body[:stmt_idx] + m_node.body[stmt_idx + 1:]
                        ast.fix_missing_locations(mutated)
                        break
                try:
                    mutants.append(("stmt_del", ast.unparse(mutated), f"delete statement {stmt_idx} in {node.name}"))
                except Exception:
                    pass

    # Constant replacement: numeric 0 -> 1, 1 -> 0, n -> n+1
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
            new_val = 1 if node.value == 0 else 0 if node.value == 1 else node.value + 1
            mutated = copy.deepcopy(tree)
            for m_node in ast.walk(mutated):
                if isinstance(m_node, ast.Constant) and isinstance(m_node.value, int) and not isinstance(m_node.value, bool) and m_node.lineno == node.lineno and m_node.col_offset == node.col_offset:
                    m_node.value = new_val
                    ast.fix_missing_locations(mutated)
                    break
            try:
                mutants.append(("const_replace", ast.unparse(mutated), f"replace constant {node.value} -> {new_val} at line {node.lineno}"))
            except Exception:
                pass

    return mutants


def _replace_not_node(tree, lineno, col_offset):
    for node in ast.walk(tree):
        for field, value in ast.iter_fields(node):
            if isinstance(value, ast.UnaryOp) and isinstance(value.op, ast.Not) and value.lineno == lineno and value.col_offset == col_offset:
                setattr(node, field, value.operand)
                return
            if isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, ast.UnaryOp) and isinstance(item.op, ast.Not) and item.lineno == lineno and item.col_offset == col_offset:
                        value[i] = item.operand
                        return


def _run_custom_mutants(function_file, test_file, repo_clone_dir, source, start_id, original_file=None):
    mutants = _generate_custom_mutants(source)
    killed = set()
    survived = set()

    # If we know the original file in the repo clone, overwrite it in-place
    # so that test imports (e.g. "from algorithms.array.foo import foo") resolve
    # to the mutated code. Restore after each test run.
    if original_file and os.path.exists(original_file):
        target_file = original_file
        with open(target_file, "r", encoding="utf-8") as f:
            backup_source = f.read()
    else:
        target_file = None
        backup_source = None

    env = os.environ.copy()
    env["PYTHONPATH"] = repo_clone_dir + os.pathsep + env.get("PYTHONPATH", "")

    for i, (tag, mutated_source, desc) in enumerate(mutants):
        mid = start_id + i
        try:
            if target_file:
                # Overwrite the original file with mutated source
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(mutated_source)

            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-x", "-q", "--tb=no", "--no-header"],
                capture_output=True, text=True, env=env, timeout=CUSTOM_MUTANT_TIMEOUT,
            )

            if result.returncode != 0:
                killed.add(mid)
            else:
                survived.add(mid)
        except (subprocess.TimeoutExpired, Exception):
            survived.add(mid)
        finally:
            # Restore original source after each mutant
            if target_file and backup_source is not None:
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(backup_source)

    return killed, survived, len(mutants)


def compute_unique_kills(all_agent_kills):
    result = {}
    agents = list(all_agent_kills.keys())
    for agent in agents:
        others = set()
        for other_agent in agents:
            if other_agent != agent:
                others |= all_agent_kills[other_agent]
        unique = all_agent_kills[agent] - others
        result[agent] = len(unique)
    return result
