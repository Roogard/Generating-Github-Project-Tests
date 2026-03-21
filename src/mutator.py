"""
Mutation testing engine.

Measures test quality by generating mutants (small code changes) and checking
which agents' tests can detect ("kill") them.

Two mutation sources:
    1. Custom AST mutants — operator swaps, constant tweaks, boolean flips, etc.
       These are fast and don't require mutmut.
    2. mutmut — industry-standard mutation testing tool (used if available).

run_all_agents(func_file, test_files_dict, repo_clone_dir, source, original_file)
    Generates all mutants once, then tests every (agent, mutant) combination
    in parallel using a single ProcessPoolExecutor. Returns:
        agent_kills   — dict[test_type -> set of mutant IDs killed]
        agent_totals  — dict[test_type -> total mutant count]
        mutant_count  — total number of mutants generated

compute_unique_kills(agent_kills)
    For each agent, counts mutants that ONLY that agent kills — its unique contribution.
"""
import ast
import concurrent.futures
import copy
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile


MUTMUT_TIMEOUT = 600
CUSTOM_MUTANT_TIMEOUT = 10

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
    open(os.path.join(src_dir, "__init__.py"), "w").close()

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


def _test_combination(args):
    test_type, mid, mutated_source, test_file, target_file, repo_clone_dir = args
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_clone_dir + os.pathsep + env.get("PYTHONPATH", "")

    if target_file:
        tmp_dir = tempfile.mkdtemp()
        # Write at full relative path so package imports (e.g. "from algorithms.arrays.X import Y")
        # resolve to the mutated file instead of the original in repo_clone_dir
        rel_path = os.path.relpath(target_file, repo_clone_dir)
        tmp_full = os.path.join(tmp_dir, rel_path)
        os.makedirs(os.path.dirname(tmp_full), exist_ok=True)
        with open(tmp_full, "w", encoding="utf-8") as f:
            f.write(mutated_source)
        # Create __init__.py for all parent directories so the package is importable
        parent = os.path.dirname(rel_path)
        if parent:
            parts = parent.split(os.sep)
            for i in range(1, len(parts) + 1):
                init_file = os.path.join(tmp_dir, *parts[:i], "__init__.py")
                if not os.path.exists(init_file):
                    open(init_file, "w").close()
        # Also write at bare basename for tests that import without the package path
        tmp_base = os.path.join(tmp_dir, os.path.basename(target_file))
        if tmp_base != tmp_full:
            with open(tmp_base, "w", encoding="utf-8") as f:
                f.write(mutated_source)
        env["PYTHONPATH"] = tmp_dir + os.pathsep + env["PYTHONPATH"]
    else:
        tmp_dir = None

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-x", "-q", "--tb=no", "--no-header"],
            capture_output=True, text=True, env=env, timeout=CUSTOM_MUTANT_TIMEOUT,
        )
        return test_type, mid, result.returncode != 0
    except (subprocess.TimeoutExpired, Exception):
        return test_type, mid, False
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _test_single_mutant(args):
    mid, mutated_source, test_file, target_file, backup_source, repo_clone_dir = args
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_clone_dir + os.pathsep + env.get("PYTHONPATH", "")

    # Each worker gets its own temp copy to avoid file contention
    if target_file:
        tmp_dir = tempfile.mkdtemp()
        tmp_target = os.path.join(tmp_dir, os.path.basename(target_file))
        with open(tmp_target, "w", encoding="utf-8") as f:
            f.write(mutated_source)
        # Point PYTHONPATH to the temp dir first so imports resolve to mutated code
        env["PYTHONPATH"] = tmp_dir + os.pathsep + env["PYTHONPATH"]
    else:
        tmp_dir = None

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-x", "-q", "--tb=no", "--no-header"],
            capture_output=True, text=True, env=env, timeout=CUSTOM_MUTANT_TIMEOUT,
        )
        return mid, result.returncode != 0
    except (subprocess.TimeoutExpired, Exception):
        return mid, False
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _run_custom_mutants(function_file, test_file, repo_clone_dir, source, start_id, original_file=None):
    mutants = _generate_custom_mutants(source)
    killed = set()
    survived = set()

    if original_file and os.path.exists(original_file):
        target_file = original_file
        with open(target_file, "r", encoding="utf-8") as f:
            backup_source = f.read()
    else:
        target_file = None
        backup_source = None

    if not mutants:
        return killed, survived, 0

    worker_args = []
    for i, (tag, mutated_source, desc) in enumerate(mutants):
        mid = start_id + i
        worker_args.append((mid, mutated_source, test_file, target_file, backup_source, repo_clone_dir))

    max_workers = min(os.cpu_count() or 4, len(worker_args))
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_test_single_mutant, args): args[0] for args in worker_args}
        for future in concurrent.futures.as_completed(futures):
            mid, was_killed = future.result()
            if was_killed:
                killed.add(mid)
            else:
                survived.add(mid)

    return killed, survived, len(mutants)


def run_all_agents(func_file, test_files_dict, repo_clone_dir, source, original_file=None):
    """Generate mutants once and test all agents against them in a single parallel pass.

    test_files_dict: {test_type: test_file_path}
    Returns: agent_kills {test_type: set}, agent_totals {test_type: int}, mutant_count int,
             mutant_descriptions [{"id": int, "tag": str, "description": str}]
    """
    mutants = _generate_custom_mutants(source)
    agent_kills = {tt: set() for tt in test_files_dict}
    agent_totals = {tt: 0 for tt in test_files_dict}

    mutant_descriptions = [
        {"id": i + 1, "tag": tag, "description": desc}
        for i, (tag, _source, desc) in enumerate(mutants)
    ]

    if not mutants:
        return agent_kills, agent_totals, 0, []

    if original_file and os.path.exists(original_file):
        target_file = original_file
    else:
        target_file = None

    worker_args = []
    for i, (_tag, mutated_source, _desc) in enumerate(mutants):
        mid = i + 1
        for test_type, test_file in test_files_dict.items():
            worker_args.append((test_type, mid, mutated_source, test_file, target_file, repo_clone_dir))

    max_workers = min(os.cpu_count() or 4, len(worker_args), 16)
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_test_combination, args): args for args in worker_args}
        for future in concurrent.futures.as_completed(futures):
            test_type, mid, was_killed = future.result()
            if was_killed:
                agent_kills[test_type].add(mid)

    for tt in test_files_dict:
        agent_totals[tt] = len(mutants)

    return agent_kills, agent_totals, len(mutants), mutant_descriptions


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
