import os

from src.agents import call_agent, call_agent_with_context
from src.writer import write_function, write_tests
from src.runner import run_single_test
from src.mutator import run_all_agents


HARNESS_TEST_TYPES = ["bva", "ecp", "path", "condition"]


def make_initial_state(fn, index, output_dir, repo_clone_dir):
    return {
        "function_info": fn,
        "index": index,
        "output_dir": output_dir,
        "repo_clone_dir": repo_clone_dir,
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
        "planned_generates": list(HARNESS_TEST_TYPES),
    }


def _dispatch(state, action):
    fn = state["function_info"]

    # generate_*_tests actions
    if action.startswith("generate_") and action.endswith("_tests"):
        test_type = action[len("generate_"):-len("_tests")]
        code = call_agent(test_type, fn)
        if code.strip():
            state["generated_tests"][test_type] = code
            return f"generated {len(code)} chars"
        return "empty response"

    if action == "run_tests":
        index = state["index"]
        output_dir = state["output_dir"]
        repo_clone_dir = state["repo_clone_dir"]

        # write_tests expects {"bva_tests": code, ...} format
        test_results_for_writer = {}
        for tt, code in state["generated_tests"].items():
            test_results_for_writer[f"{tt}_tests"] = code
        write_tests(fn, test_results_for_writer, output_dir, index)

        # run each test file
        total_passed = 0
        total_failed = 0
        total_errors = 0
        for tt in state["generated_tests"]:
            test_file = os.path.join(output_dir, "test_cases", f"{fn['name']}_{index}", f"test_{tt}.py")
            if not os.path.exists(test_file):
                continue
            result = run_single_test(test_file, repo_clone_dir)
            state["test_results"][tt] = {
                "passed": result["passed"],
                "failed": result["failed"],
                "errors": result["errors"],
            }
            total_passed += len(result["passed"])
            total_failed += len(result["failed"])
            total_errors += len(result["errors"])

        return f"{total_passed} passed, {total_failed} failed, {total_errors} errors"

    if action == "run_mutation_testing":
        index = state["index"]
        output_dir = state["output_dir"]
        repo_clone_dir = state["repo_clone_dir"]

        func_file = os.path.join(output_dir, "functions", f"{fn['name']}_{index}", "function.py")
        original_file = os.path.join(repo_clone_dir, fn["file_path"]) if fn.get("file_path") else None

        test_files_dict = {}
        for tt in state["generated_tests"]:
            test_file = os.path.join(output_dir, "test_cases", f"{fn['name']}_{index}", f"test_{tt}.py")
            if os.path.exists(test_file):
                test_files_dict[tt] = test_file

        if not test_files_dict:
            return "no test files on disk"

        agent_kills, agent_totals, mutant_count, mutant_descriptions = run_all_agents(
            func_file, test_files_dict, repo_clone_dir, fn["source"], original_file=original_file
        )

        state["agent_kills"] = agent_kills
        state["mutant_count"] = mutant_count

        # compute which mutants survived across all agents
        all_killed_ids = set()
        for kills in agent_kills.values():
            all_killed_ids |= kills

        state["survived_mutants"] = [m for m in mutant_descriptions if m["id"] not in all_killed_ids]
        state["killed_mutants"] = [m for m in mutant_descriptions if m["id"] in all_killed_ids]

        if mutant_count > 0:
            state["mutation_score"] = len(all_killed_ids) / mutant_count
        else:
            state["mutation_score"] = 0.0

        killed_count = len(all_killed_ids)
        return f"{killed_count}/{mutant_count} killed ({state['mutation_score']:.1%})"

    if action == "refine_tests":
        survived = state["survived_mutants"]
        if not survived:
            return "no survived mutants to refine against"

        survived_text = "\n".join(f"- [{m['tag']}] {m['description']}" for m in survived)

        refined_count = 0
        for tt in list(state["generated_tests"].keys()):
            current_tests = state["generated_tests"][tt]
            extra = f"### Current tests\n```python\n{current_tests}\n```\n\n"
            extra += f"### Survived mutants\nThese mutations were NOT caught by the current tests:\n{survived_text}\n\n"
            extra += "Generate an improved complete test file that kills the surviving mutants."

            new_code = call_agent_with_context("refine", fn, extra)
            if new_code.strip():
                state["generated_tests"][tt] = new_code
                refined_count += 1

        return f"refined {refined_count} agents"

    if action == "stop":
        state["done"] = True
        return "stopped"

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
    new["step_count"] = state["step_count"] + 1

    outcome = _dispatch(new, action)

    new["history"].append({
        "step": new["step_count"],
        "action": action,
        "outcome": outcome,
    })
    return new


def supervisor_policy(state):
    history_actions = [h["action"] for h in state["history"]]

    # phase 1: generate tests for planned agents
    for tt in state["planned_generates"]:
        if tt not in state["generated_tests"]:
            return f"generate_{tt}_tests"

    # phase 2: run tests if not yet run (or if refined since last run)
    has_test_results = bool(state["test_results"])
    refine_count = history_actions.count("refine_tests")
    run_count = history_actions.count("run_tests")

    if not has_test_results or (refine_count > 0 and run_count <= refine_count):
        return "run_tests"

    # phase 3: run mutation testing if not yet run (or if refined since last mutation run)
    mutation_run_count = history_actions.count("run_mutation_testing")
    if mutation_run_count == 0 or (refine_count > 0 and mutation_run_count <= refine_count):
        return "run_mutation_testing"

    # phase 4: evaluate
    if state["mutation_score"] >= 0.85:
        return "stop"

    # one refinement cycle max
    if refine_count == 0:
        return "refine_tests"

    return "stop"


def run_harness(fn, index, output_dir, repo_clone_dir, max_steps=15):
    # write the function file first
    write_function(fn, output_dir, index)

    state = make_initial_state(fn, index, output_dir, repo_clone_dir)

    for i in range(max_steps):
        action = supervisor_policy(state)
        print(f"  [{fn['name']}] step {i + 1}: {action}")
        state = step(state, action)

        last_outcome = state["history"][-1]["outcome"]
        print(f"    -> {last_outcome}")

        if state["done"]:
            break

    return state
