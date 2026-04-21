"""Web-triggered QuixBugs benchmark runner.

Called from `api/routes.py::_execute_benchmark` as a background task. Each
program processed here becomes its own `Run` row via `_persist_benchmark_run`,
so all results land in the DB and are visible on the Analytics page.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import time
from datetime import datetime

from src.repo_utils import clone_repo, extract_functions, read_readme
from src.pipeline import run_for_repo, PRESETS
from src.test_runner import run_tests as _run_tests_file


QUIXBUGS_URL = "https://github.com/jkoppel/QuixBugs"


# ── persistence ─────────────────────────────────────────────────────────────

def _persist_benchmark_run(
    *,
    benchmark_id: str,
    repo_url: str,
    cfg: dict,
    use_rag: bool,
    functions: list,
    instance_output: str,
    run_result: dict,
    metrics: dict,
) -> None:
    """Persist one benchmark invocation into the Runs + Functions tables.
    All SWT-bench metrics land as first-class Run columns.
    """
    from api import store
    from api.models import Function as FnRow
    from api.constants import RunStatus

    test_dir = os.path.join(instance_output, "tests")
    wb_path = os.path.join(test_dir, "test_whitebox.py")
    bb_path = os.path.join(test_dir, "test_blackbox.py")
    wb_code = open(wb_path, encoding="utf-8").read() if os.path.isfile(wb_path) else None
    bb_code = open(bb_path, encoding="utf-8").read() if os.path.isfile(bb_path) else None

    tests_passed = run_result.get("tests_passed", 0)
    tests_failed = len([f for f in run_result.get("failures", []) if f.get("kind") == "failure"])
    tests_errored = run_result.get("tests_errored", 0)
    tests_run = run_result.get("tests_run", 0)

    try:
        with store.session_scope() as db:
            run = store.create_run(db,
                repo_url=repo_url,
                function_name=",".join(fn["name"] for fn in functions),
                mode="quixbugs",
                benchmark_id=benchmark_id,
                status=RunStatus.DONE,
                provider=cfg.get("provider"),
                model=cfg.get("model"),
                use_rag=use_rag,
                output_dir=instance_output,
                progress_current=len(functions),
                progress_total=len(functions),
                finished_at=datetime.utcnow(),
                tests_run=tests_run,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                tests_errored=tests_errored,
                f2p=int(metrics.get("f2p") or 0),
                f2f=int(metrics.get("f2f") or 0),
                p2f=int(metrics.get("p2f") or 0),
                p2p=int(metrics.get("p2p") or 0),
                patch_applied=bool(metrics.get("patch_applied")),
                detected=bool(metrics.get("detected")),
                resolved=bool(metrics.get("resolved")),
                golden=bool(metrics.get("golden")),
                elapsed_seconds=metrics.get("elapsed_seconds"),
            )
            for idx, fn in enumerate(functions):
                db.add(FnRow(
                    run_id=run.id,
                    name=fn["name"],
                    file_path=fn.get("file_path", ""),
                    source=fn.get("source"),
                    whitebox_code=wb_code,
                    blackbox_code=bb_code,
                    tests_passed=tests_passed if idx == 0 else 0,
                    tests_failed=tests_failed if idx == 0 else 0,
                ))
            run_id = run.id
        print(f"  [sql] persisted run id={run_id} (benchmark_id={benchmark_id})")
    except Exception as e:
        print(f"  [sql] persist failed: {type(e).__name__}: {e}")


# ── QuixBugs ────────────────────────────────────────────────────────────────

def _quixbugs_programs(qb_dir: str) -> list[str]:
    pdir = os.path.join(qb_dir, "python_programs")
    out = []
    for fname in sorted(os.listdir(pdir)):
        if not fname.endswith(".py"):
            continue
        if fname.endswith("_test.py") or fname == "node.py":
            continue
        out.append(fname[:-3])
    return out


def _quixbugs_split(names: list[str], populate_count: int, seed: int) -> tuple[list[str], list[str]]:
    import random
    rng = random.Random(seed)
    shuffled = names[:]
    rng.shuffle(shuffled)
    pop = sorted(shuffled[:populate_count])
    meas = sorted(shuffled[populate_count:])
    return pop, meas


def _run_one_quixbug(program: str, qb_dir: str, run_dir: str, cfg: dict, timeout: int,
                     use_rag: bool, ingest_golden: bool) -> dict:
    from src.vectordb import ingest_example

    instance_id = f"quixbugs-{program}"
    instance_output = os.path.join(run_dir, instance_id)
    print(f"\n{'─' * 55}\n  {instance_id}")

    buggy_src = os.path.join(qb_dir, "python_programs", f"{program}.py")
    fixed_src = os.path.join(qb_dir, "correct_python_programs", f"{program}.py")
    if not os.path.isfile(buggy_src) or not os.path.isfile(fixed_src):
        print("  [skip] missing buggy/fixed file")
        return {"instance_id": instance_id, "project": "quixbugs", "program": program, "status": "missing"}

    tmp = tempfile.mkdtemp()
    try:
        target = os.path.join(tmp, f"{program}.py")
        shutil.copy(buggy_src, target)

        all_functions = extract_functions(tmp)
        functions = [f for f in all_functions if f["name"] == program]
        if not functions:
            functions = all_functions
        if not functions:
            return {"instance_id": instance_id, "project": "quixbugs", "program": program, "status": "no_targets"}

        spec = read_readme(qb_dir)
        for fn in functions:
            fn["spec"] = spec
            fn["test_examples"] = []
            fn["callees"] = []

        t0 = time.time()
        run_result = run_for_repo(functions, instance_output, tmp, cfg, timeout,
                                  use_rag=use_rag, python_bin=None)
        tests_run = run_result["tests_run"]
        tests_passed_buggy = run_result["tests_passed"]
        tests_errored = run_result["tests_errored"]
        failures = run_result["failures"]
        initial_passed = set(run_result["passed_names"])
        tests_failed_buggy = len([f for f in failures if f["kind"] == "failure"])

        # Oracle: swap in correct version, re-run each test file
        shutil.copy(fixed_src, target)
        f_to_p = f_to_f = p_to_f = 0
        patch_applied = True
        failed_names = {f["name"].split("::")[-1] for f in failures if f["kind"] == "failure"}
        test_dir = os.path.join(instance_output, "tests")
        if os.path.isdir(test_dir):
            for tfile in sorted(os.listdir(test_dir)):
                if tfile.startswith("test_") and tfile.endswith(".py"):
                    tpath = os.path.join(test_dir, tfile)
                    res = _run_tests_file(tpath, tmp, timeout, python_bin=None)
                    fixed_passed = {n.split("::")[-1] for n in res["passed"]}
                    fixed_failed = {n.split("::")[-1] for n in res["failed"]}
                    f_to_p += len(fixed_passed & failed_names)
                    f_to_f += len(fixed_failed & failed_names)
                    p_to_f += len(fixed_failed & initial_passed)

        detected = f_to_p > 0
        resolved = f_to_p > 0 and f_to_f == 0 and p_to_f == 0
        p_to_p = tests_passed_buggy - p_to_f
        elapsed = round(time.time() - t0, 1)

        golden = f_to_p > 0 and f_to_f == 0

        ingested = False
        if ingest_golden and resolved:
            wb_path = os.path.join(test_dir, "test_whitebox.py")
            bb_path = os.path.join(test_dir, "test_blackbox.py")
            wb_code = open(wb_path, encoding="utf-8").read() if os.path.isfile(wb_path) else ""
            bb_code = open(bb_path, encoding="utf-8").read() if os.path.isfile(bb_path) else ""
            for fn in functions:
                ingest_example(
                    fn={"name": fn["name"], "source": fn["source"], "file_path": fn.get("file_path", "")},
                    repo_url=f"quixbugs:{program}",
                    whitebox_code=wb_code,
                    blackbox_code=bb_code,
                    passed=tests_passed_buggy,
                    failed=tests_failed_buggy,
                    coverage_pct=None,
                )
                ingested = True

        _persist_benchmark_run(
            benchmark_id=program,
            repo_url=f"quixbugs:{program}",
            cfg=cfg,
            use_rag=use_rag,
            functions=functions,
            instance_output=instance_output,
            run_result=run_result,
            metrics={
                "patch_applied": patch_applied,
                "f2p": f_to_p, "f2f": f_to_f, "p2f": p_to_f, "p2p": p_to_p,
                "detected": detected, "resolved": resolved,
                "golden": golden, "elapsed_seconds": elapsed,
            },
        )

        print(f"  → tests={tests_run}  detected={detected}  F→P={f_to_p}  F→F={f_to_f}  P→F={p_to_f}  "
              f"resolved={resolved}  ingested={ingested}  {elapsed}s")
        return {
            "instance_id": instance_id, "project": "quixbugs", "program": program, "status": "ok",
            "tests_run": tests_run, "tests_passed": tests_passed_buggy,
            "tests_failed": tests_failed_buggy, "tests_errored": tests_errored,
            "patch_applied": patch_applied,
            "f2p": f_to_p, "f2f": f_to_f, "p2f": p_to_f, "p2p": p_to_p,
            "detected": detected, "resolved": resolved,
            "golden": golden, "ingested": ingested,
            "elapsed_seconds": elapsed,
        }
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        return {"instance_id": instance_id, "project": "quixbugs", "program": program,
                "status": "error", "error": str(e)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_quixbugs(
    *,
    phase: str,
    cfg: dict,
    preset: str = "default",
    seed: int = 42,
    populate_count: int = 30,
    use_rag: bool = True,
    output_dir: str = "./eval_output",
) -> list[dict]:
    """Run the QuixBugs benchmark. phase ∈ {'populate', 'measure'}.

    - populate: generate tests for the populate split, ingest golden examples into Chroma.
    - measure:  generate tests for the measure split, record SWT metrics to DB.
    """
    assert phase in ("populate", "measure"), f"phase must be populate|measure, got {phase!r}"
    timeout = PRESETS.get(preset, PRESETS["default"])["timeout"]

    qb_tmp = tempfile.mkdtemp()
    try:
        print(f"Cloning QuixBugs metadata...")
        clone_repo(QUIXBUGS_URL, qb_tmp)
        all_programs = _quixbugs_programs(qb_tmp)
        populate, measure = _quixbugs_split(all_programs, populate_count, seed)
        print(f"Total: {len(all_programs)}  populate: {len(populate)}  measure: {len(measure)}  seed: {seed}")

        if phase == "populate":
            programs = populate
            ingest_golden = True
            use_rag_eff = False
        else:
            programs = measure
            ingest_golden = False
            use_rag_eff = use_rag

        run_dir = os.path.join(output_dir, f"quixbugs_{phase}_{datetime.now().strftime('%d-%m-%Y_%H-%M')}")
        os.makedirs(run_dir, exist_ok=True)

        print(f"\n{phase.upper()}  —  {len(programs)} program(s)  "
              f"[{cfg.get('provider')}/{cfg.get('model') or 'default'}]\n")
        return [
            _run_one_quixbug(prog, qb_tmp, run_dir, cfg, timeout,
                             use_rag=use_rag_eff, ingest_golden=ingest_golden)
            for prog in programs
        ]
    finally:
        shutil.rmtree(qb_tmp, ignore_errors=True)
