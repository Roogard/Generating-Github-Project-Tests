"""Web-triggered QuixBugs benchmark runner.

Called from `api/routes.py::_execute_benchmark` as a background task. Each
program becomes its own `Run` row via `_persist_benchmark_run`, so results
land in the DB and show up on the Analytics page.

Oracle bookkeeping (buggy↔fixed swap, F→P / F→F / P→F / P→P counting) is
performed inside the agent env (`src/agent/env.py::TestGenEnv.summary`).
"""
from __future__ import annotations

import os
import shutil
import tempfile
import time
from datetime import datetime

from src.pipeline import PRESETS, run_agent_on_function
from src.repo_utils import clone_repo, extract_functions, read_readme


QUIXBUGS_URL = "https://github.com/jkoppel/QuixBugs"


# ── persistence ─────────────────────────────────────────────────────────────

def _persist_benchmark_run(
    *,
    benchmark_id: str,
    repo_url: str,
    cfg: dict,
    use_rag: bool,
    fn: dict,
    fn_result: dict,
    elapsed: float,
) -> None:
    """Persist one benchmark invocation into the Runs + Functions tables."""
    from api import store
    from api.models import Function as FnRow
    from api.constants import RunStatus

    metrics = fn_result.get("metrics") or {}
    tests_passed = fn_result.get("tests_passed", 0)
    tests_failed = fn_result.get("tests_failed", 0)
    tests_errored = fn_result.get("tests_errored", 0)
    tests_run = fn_result.get("tests_run", 0)

    try:
        with store.session_scope() as db:
            run = store.create_run(db,
                repo_url=repo_url,
                function_name=fn["name"],
                mode="quixbugs",
                benchmark_id=benchmark_id,
                status=RunStatus.DONE,
                provider=cfg.get("provider"),
                model=cfg.get("model"),
                use_rag=use_rag,
                output_dir=fn_result.get("output_dir"),
                progress_current=1,
                progress_total=1,
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
                elapsed_seconds=round(elapsed, 1),
            )
            db.add(FnRow(
                run_id=run.id,
                name=fn["name"],
                file_path=fn.get("file_path", ""),
                source=fn.get("source"),
                test_code=fn_result.get("test_code") or None,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                coverage_pct=fn_result.get("coverage_pct"),
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
                     max_turns: int, use_rag: bool, ingest_golden: bool) -> dict:
    from src.vectordb import ingest_example

    instance_id = f"quixbugs-{program}"
    instance_output = os.path.join(run_dir, instance_id)
    os.makedirs(instance_output, exist_ok=True)
    print(f"\n{'─' * 55}\n  {instance_id}")

    buggy_src = os.path.join(qb_dir, "python_programs", f"{program}.py")
    fixed_src = os.path.join(qb_dir, "correct_python_programs", f"{program}.py")
    if not os.path.isfile(buggy_src) or not os.path.isfile(fixed_src):
        print("  [skip] missing buggy/fixed file")
        return {"instance_id": instance_id, "status": "missing"}

    tmp = tempfile.mkdtemp()
    try:
        target = os.path.join(tmp, f"{program}.py")
        shutil.copy(buggy_src, target)

        all_functions = extract_functions(tmp)
        functions = [f for f in all_functions if f["name"] == program]
        if not functions:
            functions = all_functions
        if not functions:
            return {"instance_id": instance_id, "status": "no_targets"}
        fn = functions[0]
        fn["spec"] = read_readme(qb_dir)
        fn["test_examples"] = []
        fn["callees"] = []

        benchmark_context = {
            "buggy_path": buggy_src,
            "fixed_path": fixed_src,
            "target_path": target,
        }

        t0 = time.time()
        fn_result = run_agent_on_function(
            fn, cfg, tmp, instance_output,
            python_bin=None, timeout=timeout, max_turns=max_turns,
            benchmark_context=benchmark_context,
        )
        elapsed = time.time() - t0

        metrics = fn_result.get("metrics") or {}
        f2p = int(metrics.get("f2p") or 0)
        f2f = int(metrics.get("f2f") or 0)
        p2f = int(metrics.get("p2f") or 0)
        detected = bool(metrics.get("detected"))
        resolved = bool(metrics.get("resolved"))

        ingested = False
        if ingest_golden and resolved and fn_result.get("test_code"):
            try:
                ingest_example(
                    fn={"name": fn["name"], "source": fn["source"], "file_path": fn.get("file_path", "")},
                    repo_url=f"quixbugs:{program}",
                    test_code=fn_result["test_code"],
                    passed=fn_result.get("tests_passed", 0),
                    failed=fn_result.get("tests_failed", 0),
                    coverage_pct=fn_result.get("coverage_pct"),
                )
                ingested = True
            except Exception as e:
                print(f"  [rag] ingest failed: {e}")

        _persist_benchmark_run(
            benchmark_id=program,
            repo_url=f"quixbugs:{program}",
            cfg=cfg,
            use_rag=use_rag,
            fn=fn,
            fn_result=fn_result,
            elapsed=elapsed,
        )

        print(f"  → detected={detected}  F→P={f2p}  F→F={f2f}  P→F={p2f}  "
              f"resolved={resolved}  ingested={ingested}  {round(elapsed, 1)}s")
        return {
            "instance_id": instance_id, "program": program, "status": "ok",
            "tests_run": fn_result.get("tests_run", 0),
            "tests_passed": fn_result.get("tests_passed", 0),
            "tests_failed": fn_result.get("tests_failed", 0),
            **metrics,
            "ingested": ingested,
            "elapsed_seconds": round(elapsed, 1),
        }
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        return {"instance_id": instance_id, "status": "error", "error": str(e)}
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
    """Run the QuixBugs benchmark. phase ∈ {'populate', 'measure'}."""
    assert phase in ("populate", "measure"), f"phase must be populate|measure, got {phase!r}"
    preset_cfg = PRESETS.get(preset, PRESETS["default"])
    timeout = preset_cfg["timeout"]
    max_turns = preset_cfg["max_turns"]

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
              f"[{cfg.get('provider')}/{cfg.get('model') or 'default'}]  turns<={max_turns}\n")
        return [
            _run_one_quixbug(prog, qb_tmp, run_dir, cfg, timeout, max_turns,
                             use_rag=use_rag_eff, ingest_golden=ingest_golden)
            for prog in programs
        ]
    finally:
        shutil.rmtree(qb_tmp, ignore_errors=True)
