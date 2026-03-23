import json
import os
import re
import subprocess
import sys
import tempfile

from src.agents import call_agent, call_agent_with_context
from src.writer import write_function, write_tests
from src.runner import run_single_test
from src.mutator import run_all_agents, compute_unique_kills

#agent policy on line 344, which is where the cool stuff is
#essentially, this document has all the different actions the agent can take
#as well aas the steps and decision policy




SPECIAL_PROMPTS = {"refine", "fix", "mutate", "coverage"}

ALL_MUTATION_TAGS = [
    "cond_neg", "boundary_up", "boundary_down", "ret_none", "not_removal",
    "aug_swap", "bool_swap", "exc_broaden", "arith_swap", "cmp_swap",
    "logic_swap", "sign_flip", "stmt_del", "const_replace", "llm_mutant",
]


def discover_test_types(config):
    explicit = config["harness"]["test_types"]
    if explicit:
        return list(explicit)
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    types = []
    for f in sorted(os.listdir(prompts_dir)):
        if f.endswith(".md"):
            name = f[:-3]
            if name not in SPECIAL_PROMPTS:
                types.append(name)
    return types


def make_initial_state(fn, index, output_dir, repo_clone_dir, config):
    test_types = discover_test_types(config)
    return {
        "function_info": fn,
        "index": index,
        "output_dir": output_dir,
        "repo_clone_dir": repo_clone_dir,
        "config": config,
        "generated_tests": {},
        "test_results": {},
        "mutation_score": 0.0,
        "mutant_count": 0,
        "agent_kills": {},
        "survived_mutants": [],
        "killed_mutants": [],
        "history": [],
        "step_count": 0,
        "done": False,
        "planned_generates": test_types,
        "fix_attempts": 0,
        "line_coverage": 0.0,
        "branch_coverage": 0.0,
        "unique_kills": {},
        "assertion_density": 0.0,
        "test_diversity": 0.0,
        "quality_score": 0.0,
        "llm_mutation_score": 0.0,
        "missing_lines": [],
        "missing_branches": [],
        "score_history": [],
        "grpo_rewards": {
            "mutation": 0.0,
            "branch_coverage": 0.0,
            "assertion_density": 0.0,
            "test_diversity": 0.0,
            "unique_kills_ratio": 0.0,
            "llm_mutation": 0.0,
            "quality_score": 0.0,
        },
    }


def _compute_assertion_density(generated_tests):
    total_asserts = 0
    total_test_fns = 0
    for code in generated_tests.values():
        total_asserts += len(re.findall(r'^\s*assert\b', code, re.MULTILINE))
        total_test_fns += len(re.findall(r'^\s*def test_', code, re.MULTILINE))
    if total_test_fns == 0:
        return 0.0
    return min((total_asserts / total_test_fns) / 3.0, 1.0)


def _compute_test_diversity(killed_mutants):
    if not killed_mutants:
        return 0.0
    killed_tags = set(m["tag"] for m in killed_mutants)
    return len(killed_tags) / len(ALL_MUTATION_TAGS)


def compute_quality_score(state):
    score = (
        0.50 * state["mutation_score"]
        + 0.25 * state["branch_coverage"]
        + 0.15 * state["assertion_density"]
        + 0.10 * state["test_diversity"]
    )
    state["quality_score"] = round(score, 4)
    return score


def _test_dir(state):
    fn = state["function_info"]
    return os.path.join(state["output_dir"], "test_cases", f"{fn['name']}_{state['index']}")


def _test_file(state, tt):
    return os.path.join(_test_dir(state), f"test_{tt}.py")


def _handle_generate_tests(state, action):
    test_type = action[len("generate_"):-len("_tests")]
    config = state["config"]
    code = call_agent(test_type, state["function_info"], config)
    if code.strip():
        state["generated_tests"][test_type] = code
        return f"generated {len(code)} chars"
    return "empty response"


def _handle_run_tests(state):
    fn = state["function_info"]
    config = state["config"]
    test_timeout = config["timeouts"]["test"]
    write_tests(fn, {f"{tt}_tests": code for tt, code in state["generated_tests"].items()},
                state["output_dir"], state["index"])

    passed = failed = errors = 0
    for tt in state["generated_tests"]:
        path = _test_file(state, tt)
        if not os.path.exists(path):
            continue
        result = run_single_test(path, state["repo_clone_dir"], timeout=test_timeout)
        state["test_results"][tt] = result
        passed += len(result["passed"])
        failed += len(result["failed"])
        errors += len(result["errors"])

    state["assertion_density"] = _compute_assertion_density(state["generated_tests"])
    return f"{passed} passed, {failed} failed, {errors} errors"


def _handle_run_mutation_testing(state):
    fn = state["function_info"]
    config = state["config"]

    total_passed = sum(len(r.get("passed", [])) for r in state["test_results"].values())
    if total_passed == 0:
        return "no passing tests, skipping mutation testing"

    func_file = os.path.join(state["output_dir"], "functions", f"{fn['name']}_{state['index']}", "function.py")
    original_file = os.path.join(state["repo_clone_dir"], fn["file_path"]) if fn.get("file_path") else None

    test_files_dict = {tt: _test_file(state, tt) for tt in state["generated_tests"]
                      if os.path.exists(_test_file(state, tt))}
    if not test_files_dict:
        return "no test files on disk"

    agent_kills, _, mutant_count, mutant_descriptions = run_all_agents(
        func_file, test_files_dict, state["repo_clone_dir"], fn["source"],
        original_file=original_file, fn=fn, config=config
    )

    all_killed_ids = set().union(*agent_kills.values()) if agent_kills else set()

    state["agent_kills"] = agent_kills
    state["mutant_count"] = mutant_count
    state["unique_kills"] = compute_unique_kills(agent_kills)
    state["survived_mutants"] = [m for m in mutant_descriptions if m["id"] not in all_killed_ids]
    state["killed_mutants"] = [m for m in mutant_descriptions if m["id"] in all_killed_ids]
    state["mutation_score"] = len(all_killed_ids) / mutant_count if mutant_count > 0 else 0.0
    state["test_diversity"] = _compute_test_diversity(state["killed_mutants"])

    llm_mutants = [m for m in mutant_descriptions if m["tag"] == "llm_mutant"]
    if llm_mutants:
        llm_ids = set(m["id"] for m in llm_mutants)
        state["llm_mutation_score"] = len(all_killed_ids & llm_ids) / len(llm_ids)
    else:
        state["llm_mutation_score"] = 0.0

    compute_quality_score(state)

    total_unique = sum(state["unique_kills"].values())
    state["grpo_rewards"]["mutation"] = state["mutation_score"]
    state["grpo_rewards"]["test_diversity"] = state["test_diversity"]
    state["grpo_rewards"]["llm_mutation"] = state["llm_mutation_score"]
    state["grpo_rewards"]["unique_kills_ratio"] = total_unique / mutant_count if mutant_count > 0 else 0.0

    killed_count = len(all_killed_ids)
    parts = [f"{killed_count}/{mutant_count} killed ({state['mutation_score']:.1%})"]
    if llm_mutants:
        parts.append(f"llm={state['llm_mutation_score']:.1%}")
    parts.append(f"quality={state['quality_score']:.2f}")
    return ", ".join(parts)


def _handle_run_coverage(state):
    fn = state["function_info"]
    config = state["config"]
    coverage_timeout = config["timeouts"]["coverage"]

    total_passed = sum(len(r.get("passed", [])) for r in state["test_results"].values())
    if total_passed == 0:
        return "no passing tests, skipping coverage"

    # only include test files that have passing tests (skip broken ones that crash pytest-cov)
    test_files = []
    for tt in state["generated_tests"]:
        r = state["test_results"].get(tt, {})
        if not r.get("passed"):
            continue
        path = _test_file(state, tt)
        if os.path.exists(path):
            test_files.append(os.path.abspath(path))
    if not test_files:
        return "no passing test files on disk"

    original_file = os.path.join(state["repo_clone_dir"], fn["file_path"])
    source_dir = os.path.dirname(original_file)

    report_fd, report_file = tempfile.mkstemp(suffix=".json")
    os.close(report_fd)

    env = os.environ.copy()
    env["PYTHONPATH"] = state["repo_clone_dir"] + os.pathsep + env.get("PYTHONPATH", "")

    cmd = [sys.executable, "-m", "pytest"] + test_files + [
        f"--cov={source_dir}", "--cov-branch",
        f"--cov-report=json:{report_file}", "-q", "--no-header",
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, env=env,
                       cwd=state["repo_clone_dir"], timeout=coverage_timeout)
    except subprocess.TimeoutExpired:
        return "coverage timed out"

    if not os.path.exists(report_file) or os.path.getsize(report_file) == 0:
        if os.path.exists(report_file):
            os.remove(report_file)
        return "coverage report not generated"

    try:
        with open(report_file, encoding="utf-8") as f:
            cov_data = json.load(f)
        os.remove(report_file)
    except (json.JSONDecodeError, ValueError):
        if os.path.exists(report_file):
            os.remove(report_file)
        return "coverage report empty or invalid"

    target = fn["file_path"].replace("\\", "/")
    file_data = None
    for fpath, fdata in cov_data.get("files", {}).items():
        if fpath.replace("\\", "/").endswith(target):
            file_data = fdata
            break

    start = fn.get("start_line", 0)
    end = fn.get("end_line", 0)

    if file_data and start and end:
        executed = [ln for ln in file_data.get("executed_lines", []) if start <= ln <= end]
        missing = [ln for ln in file_data.get("missing_lines", []) if start <= ln <= end]
        total_lines = len(executed) + len(missing)
        state["line_coverage"] = len(executed) / total_lines if total_lines > 0 else 0.0

        all_branches = file_data.get("missing_branches", []) + file_data.get("executed_branches", [])
        fn_all_branches = [b for b in all_branches if start <= b[0] <= end]
        fn_missing_branches = [b for b in file_data.get("missing_branches", []) if start <= b[0] <= end]
        total_branches = len(fn_all_branches)
        if total_branches > 0:
            state["branch_coverage"] = (total_branches - len(fn_missing_branches)) / total_branches
        else:
            state["branch_coverage"] = 0.0

        state["missing_lines"] = missing
        state["missing_branches"] = fn_missing_branches
    elif file_data:
        summary = file_data.get("summary", {})
        state["line_coverage"] = summary.get("percent_covered", 0.0) / 100.0
        num_branches = summary.get("num_branches", 0)
        if num_branches > 0:
            state["branch_coverage"] = summary.get("covered_branches", 0) / num_branches
        else:
            state["branch_coverage"] = 0.0
        state["missing_lines"] = file_data.get("missing_lines", [])
        state["missing_branches"] = file_data.get("missing_branches", [])
    else:
        totals = cov_data.get("totals", {})
        state["line_coverage"] = totals.get("percent_covered", 0.0) / 100.0
        state["branch_coverage"] = 0.0
        state["missing_lines"] = []
        state["missing_branches"] = []

    compute_quality_score(state)
    state["grpo_rewards"]["branch_coverage"] = state["branch_coverage"]
    state["grpo_rewards"]["assertion_density"] = state["assertion_density"]
    state["grpo_rewards"]["quality_score"] = state["quality_score"]
    state["score_history"].append(state["quality_score"])
    return f"line: {state['line_coverage']:.1%}, branch: {state['branch_coverage']:.1%}, quality={state['quality_score']:.2f}"


def _handle_refine_tests(state):
    config = state["config"]
    survived = state["survived_mutants"]
    if not survived:
        return "no survived mutants to refine against"

    survived_text = "\n".join(f"- [{m['tag']}] {m['description']}" for m in survived)
    refined_count = 0
    for tt in list(state["generated_tests"].keys()):
        extra = (
            f"### Current tests\n```python\n{state['generated_tests'][tt]}\n```\n\n"
            f"### Survived mutants\nThese mutations were NOT caught by the current tests:\n{survived_text}\n\n"
            "Generate an improved complete test file that kills the surviving mutants."
        )
        new_code = call_agent_with_context("refine", state["function_info"], extra, config)
        if new_code.strip():
            state["generated_tests"][tt] = new_code
            refined_count += 1
    return f"refined {refined_count} agents"


def _handle_generate_coverage_tests(state):
    fn = state["function_info"]
    config = state["config"]
    missing_lines = state["missing_lines"]
    missing_branches = state["missing_branches"]

    if not missing_lines and not missing_branches:
        return "no uncovered lines or branches"

    source_lines = fn["source"].split("\n")
    start = fn.get("start_line", 1)
    numbered = "\n".join(f"{start + i:4d}: {line}" for i, line in enumerate(source_lines))

    existing_tests = "\n\n".join(
        f"### {tt}\n```python\n{code}\n```"
        for tt, code in state["generated_tests"].items()
    )

    parts = [f"### Function source (with line numbers)\n```\n{numbered}\n```\n"]
    if missing_lines:
        parts.append(f"### Uncovered lines\n{', '.join(str(ln) for ln in missing_lines)}\n")
    if missing_branches:
        branch_strs = [f"{b[0]}->{b[1]}" for b in missing_branches]
        parts.append(f"### Uncovered branches\n{', '.join(branch_strs)}\n")
    if existing_tests:
        parts.append(f"### Existing tests\n{existing_tests}\n")
    parts.append("Generate tests that cover the uncovered lines and branches listed above.")

    extra = "\n".join(parts)
    code = call_agent_with_context("coverage", fn, extra, config)
    if code.strip():
        state["generated_tests"]["coverage"] = code
        return f"generated {len(code)} chars"
    return "empty response"


def _handle_fix_tests(state):
    config = state["config"]
    state["fix_attempts"] += 1
    fixed_count = 0
    for tt in list(state["test_results"].keys()):
        r = state["test_results"][tt]
        if not r["errors"] and not r["failed"]:
            continue
        extra = (
            f"### Current test code\n```python\n{state['generated_tests'].get(tt, '')}\n```\n\n"
            f"### Error output\n**stdout:**\n```\n{r['stdout']}\n```\n\n"
            f"**stderr:**\n```\n{r['stderr']}\n```\n\n"
            "Fix the tests so they pass. Return the complete corrected test file."
        )
        new_code = call_agent_with_context("fix", state["function_info"], extra, config)
        if new_code.strip():
            state["generated_tests"][tt] = new_code
            fixed_count += 1
    return f"fixed {fixed_count} test types"


def _handle_stop(state):
    state["done"] = True
    return "stopped"


_HANDLERS = {
    "run_tests": _handle_run_tests,
    "run_mutation_testing": _handle_run_mutation_testing,
    "run_coverage": _handle_run_coverage,
    "refine_tests": _handle_refine_tests,
    "fix_tests": _handle_fix_tests,
    "generate_coverage_tests": _handle_generate_coverage_tests,
    "stop": _handle_stop,
}


def _dispatch(state, action):
    handler = _HANDLERS.get(action)
    if handler:
        return handler(state)
    if action.startswith("generate_") and action.endswith("_tests"):
        return _handle_generate_tests(state, action)
    return f"unknown action: {action}"


def step(state, action):
    new = dict(state)
    new["generated_tests"] = dict(state["generated_tests"])
    new["test_results"] = dict(state["test_results"])
    new["agent_kills"] = dict(state["agent_kills"])
    new["survived_mutants"] = list(state["survived_mutants"])
    new["killed_mutants"] = list(state["killed_mutants"])
    new["history"] = list(state["history"])
    new["planned_generates"] = list(state["planned_generates"])
    new["unique_kills"] = dict(state["unique_kills"])
    new["missing_lines"] = list(state["missing_lines"])
    new["missing_branches"] = list(state["missing_branches"])
    new["score_history"] = list(state["score_history"])
    new["grpo_rewards"] = dict(state["grpo_rewards"])
    new["step_count"] = state["step_count"] + 1

    outcome = _dispatch(new, action)
    new["history"].append({"step": new["step_count"], "action": action, "outcome": outcome})
    return new


#the main function worth looking at. this decides when the agent does what. Right now, it 
#it is just a simple policy with set rules, but will be replaces with an agent soon
def supervisor_policy(state):
    config = state["config"]
    quality_threshold = config["harness"]["quality_threshold"]
    max_fix_attempts = config["harness"]["max_fix_attempts"]
    history_actions = [h["action"] for h in state["history"]]

    for tt in state["planned_generates"]:
        if tt not in state["generated_tests"]:
            return f"generate_{tt}_tests"

    refine_count = history_actions.count("refine_tests")
    fix_count = history_actions.count("fix_tests")
    run_count = history_actions.count("run_tests")
    regen_count = sum(1 for a in history_actions[len(state["planned_generates"]):]
                      if a.startswith("generate_") and a.endswith("_tests"))

    if run_count == 0 or run_count <= refine_count + fix_count + regen_count:
        return "run_tests"

    has_broken = any(r["errors"] or r["failed"] for r in state["test_results"].values())
    if has_broken and state["fix_attempts"] < max_fix_attempts:
        return "fix_tests"

    mutation_run_count = history_actions.count("run_mutation_testing")
    if mutation_run_count == 0 or mutation_run_count <= refine_count + regen_count:
        return "run_mutation_testing"

    coverage_run_count = history_actions.count("run_coverage")
    if coverage_run_count == 0 or coverage_run_count <= refine_count + regen_count:
        return "run_coverage"

    if state["quality_score"] >= quality_threshold:
        return "stop"

    # stop if no tests pass after 2+ run_tests attempts — function is untestable
    total_passed = sum(len(r.get("passed", [])) for r in state["test_results"].values())
    if total_passed == 0 and run_count >= 2:
        return "stop"

    if state["unique_kills"] and state["quality_score"] < quality_threshold:
        for tt, count in state["unique_kills"].items():
            regen_action = f"generate_{tt}_tests"
            if count == 0 and regen_action not in history_actions[len(state["planned_generates"]):]:
                return regen_action

    coverage_gen_count = history_actions.count("generate_coverage_tests")
    if state["branch_coverage"] < 0.90 and coverage_gen_count == 0:
        return "generate_coverage_tests"

    if refine_count < 3:
        score_history = state["score_history"]
        if refine_count == 0:
            return "refine_tests"
        if len(score_history) >= 2 and score_history[-1] - score_history[-2] < 0.02:
            return "stop"
        return "refine_tests"

    return "stop"


def _serialize_state_for_log(state):
    out = {}
    for k, v in state.items():
        if k == "agent_kills":
            out[k] = {tt: sorted(ids) for tt, ids in v.items()}
        elif k == "function_info":
            out[k] = {"name": v["name"], "file_path": v.get("file_path", ""), "language": v.get("language", "")}
        elif k in ("repo_clone_dir", "output_dir", "config"):
            continue
        else:
            out[k] = v
    return out


def _save_trajectory(state):
    traj_dir = os.path.join(state["output_dir"], "trajectories")
    os.makedirs(traj_dir, exist_ok=True)
    fn = state["function_info"]
    path = os.path.join(traj_dir, f"{fn['name']}_{state['index']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_serialize_state_for_log(state), f, indent=2, default=str)


def run_harness(fn, index, output_dir, repo_clone_dir, config, max_steps=None):
    if max_steps is None:
        max_steps = config["harness"]["max_steps"]
    write_function(fn, output_dir, index)
    state = make_initial_state(fn, index, output_dir, repo_clone_dir, config)

    for i in range(max_steps):
        action = supervisor_policy(state)
        print(f"  [{fn['name']}] step {i + 1}: {action}")
        state = step(state, action)
        print(f"    -> {state['history'][-1]['outcome']}")
        if state["done"]:
            break

    _save_trajectory(state)
    return state
