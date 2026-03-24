import json
import os

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool as langchain_tool

from src.agents import get_supervisor_llm
from src.writer import write_function
from src.mutator import generate_all_mutants
from src.skills import SPECIAL_PROMPTS, dispatch


SUPERVISOR_SYSTEM_PROMPT = """\
You are a test quality supervisor. Your job is to maximize the quality_score of generated tests for a Python function by choosing one action at a time.

## Quality Score Formula
quality_score = 0.50 * mutation_score + 0.25 * branch_coverage + 0.15 * assertion_density + 0.10 * test_diversity

Your target is quality_score >= {quality_threshold}. Stop when you reach it or when further actions show diminishing returns.

## Rules
- You do NOT need to generate all test types. Pick only the ones likely to help for this function.
- You must run_tests after generating, fixing, or refining tests — nothing else works without test results.
- run_mutation_testing and run_coverage both require passing tests. Never call them with 0 passing tests.
- fix_tests only helps when test_results show errors or failures (max {max_fix_attempts} attempts).
- refine_tests only helps after mutation testing reveals survived mutants.
- generate_coverage_tests only helps after run_coverage reveals missing lines/branches.
- Stop if the function appears untestable (0 passing tests after 2+ run_tests attempts).
- Stop if score_history shows < 2% improvement between the last two coverage measurements.

## Important
Pick exactly ONE tool per step. In the reasoning parameter, explain your analysis of the current state and why this action is the best next step.

{memory_context}"""


def _build_supervisor_tools(test_types):
    tools = []
    for tt in test_types:
        action_name = f"generate_{tt}_tests"
        def _make_fn(name, tt_name):
            def fn(reasoning: str):
                return name
            fn.__name__ = name
            fn.__doc__ = (
                f"Generate {tt_name} tests for the function under test. "
                "reasoning: explain why you chose this action given the current state."
            )
            return fn
        tools.append(langchain_tool(_make_fn(action_name, tt)))

    @langchain_tool
    def run_tests(reasoning: str):
        """Execute all generated test files and collect pass/fail/error results. Must run after generating, fixing, or refining tests. reasoning: explain why."""
        return "run_tests"

    @langchain_tool
    def run_mutation_testing(reasoning: str):
        """Run mutation testing — generate code mutants and check which tests detect them. Produces mutation_score and identifies survived mutants. Requires passing tests. reasoning: explain why."""
        return "run_mutation_testing"

    @langchain_tool
    def run_coverage(reasoning: str):
        """Measure line and branch coverage using pytest-cov. Updates line_coverage, branch_coverage, missing_lines, missing_branches. Requires passing tests. reasoning: explain why."""
        return "run_coverage"

    @langchain_tool
    def fix_tests(reasoning: str):
        """Fix tests that have errors or failures by sending error output to a repair agent. Only useful when test_results show errors/failures. reasoning: explain why."""
        return "fix_tests"

    @langchain_tool
    def refine_tests(reasoning: str):
        """Refine all test types using survived mutant descriptions. Only useful after mutation testing reveals survived mutants. reasoning: explain why."""
        return "refine_tests"

    @langchain_tool
    def generate_coverage_tests(reasoning: str):
        """Generate additional tests targeting specific uncovered lines and branches. Only useful after run_coverage reveals missing coverage. reasoning: explain why."""
        return "generate_coverage_tests"

    @langchain_tool
    def stop(reasoning: str):
        """Stop the harness loop. Use when quality_score >= threshold, further refinement shows diminishing returns, or the function appears untestable. reasoning: explain why."""
        return "stop"

    tools.extend([run_tests, run_mutation_testing, run_coverage,
                  fix_tests, refine_tests, generate_coverage_tests, stop])
    return tools


def _serialize_state_for_llm(state):
    fn = state["function_info"]
    config = state["config"]
    parts = []

    parts.append("## Function Under Test")
    parts.append(f"Name: {fn['name']}")
    parts.append(f"File: {fn.get('file_path', 'unknown')}")
    parts.append(f"Lines: {fn.get('start_line', '?')}-{fn.get('end_line', '?')}")
    parts.append(f"Source: {len(fn['source'])} chars, {len(fn['source'].splitlines())} lines")

    parts.append(f"\n## Current State (step {state['step_count']})")

    gen = state["generated_tests"]
    if gen:
        parts.append(f"Generated tests: {', '.join(gen.keys())} ({len(gen)} types)")
    else:
        parts.append("Generated tests: none")

    if state["test_results"]:
        for tt, r in state["test_results"].items():
            p = len(r.get("passed", []))
            f = len(r.get("failed", []))
            e = len(r.get("errors", []))
            parts.append(f"  {tt}: {p} passed, {f} failed, {e} errors")
    else:
        parts.append("Test results: not yet run")

    pre = state["pregenerated_mutants"]
    if pre:
        ast_count = sum(1 for tag, _, _ in pre if tag != "llm_mutant")
        llm_count = len(pre) - ast_count
        parts.append(f"pregenerated_mutants: {len(pre)} ({ast_count} AST + {llm_count} LLM)")

    threshold = config["harness"]["quality_threshold"]
    parts.append("\n## Quality Metrics")
    parts.append(f"quality_score: {state['quality_score']:.4f} (threshold: {threshold})")
    parts.append(f"mutation_score: {state['mutation_score']:.2%} ({len(state.get('killed_mutants', []))}/{state['mutant_count']} killed)")
    parts.append(f"line_coverage: {state['line_coverage']:.2%}")
    parts.append(f"branch_coverage: {state['branch_coverage']:.2%}")
    parts.append(f"assertion_density: {state['assertion_density']:.4f}")
    parts.append(f"test_diversity: {state['test_diversity']:.4f}")
    parts.append(f"llm_mutation_score: {state['llm_mutation_score']:.2%}")

    if state["missing_lines"]:
        parts.append(f"missing_lines: {state['missing_lines'][:20]}")
    if state["missing_branches"]:
        parts.append(f"missing_branches: {state['missing_branches'][:10]}")

    if state["unique_kills"]:
        parts.append("\n## Unique Kills per Agent")
        for tt, count in state["unique_kills"].items():
            parts.append(f"  {tt}: {count}")

    if state["survived_mutants"]:
        parts.append(f"\n## Survived Mutants ({len(state['survived_mutants'])} total)")
        for m in state["survived_mutants"][:10]:
            parts.append(f"  - [{m['tag']}] {m['description']}")
        if len(state["survived_mutants"]) > 10:
            parts.append(f"  ... and {len(state['survived_mutants']) - 10} more")

    parts.append(f"\nfix_attempts: {state['fix_attempts']} / {config['harness']['max_fix_attempts']}")

    if state["score_history"]:
        parts.append(f"score_history: {[round(s, 4) for s in state['score_history']]}")

    parts.append(f"\n## Action History ({len(state['history'])} steps)")
    for h in state["history"]:
        reasoning = h.get("reasoning", "")
        reasoning_snip = f" ({reasoning[:80]}...)" if len(reasoning) > 80 else (f" ({reasoning})" if reasoning else "")
        parts.append(f"  step {h['step']}: {h['action']} -> {h['outcome']}{reasoning_snip}")

    return "\n".join(parts)


def llm_supervisor(state, memory_context=""):
    config = state["config"]
    test_types = state["planned_generates"]
    quality_threshold = config["harness"]["quality_threshold"]
    max_fix_attempts = config["harness"]["max_fix_attempts"]

    last_action = state["history"][-1]["action"] if state["history"] else None
    all_tools = _build_supervisor_tools(test_types)
    tools = [t for t in all_tools if t.name != last_action]
    valid_actions = {t.name for t in tools}

    system = SUPERVISOR_SYSTEM_PROMPT.format(
        quality_threshold=quality_threshold,
        max_fix_attempts=max_fix_attempts,
        memory_context=memory_context,
    )
    user = _serialize_state_for_llm(state)

    llm = get_supervisor_llm(config)
    llm_with_tools = llm.bind_tools(tools, tool_choice="any")

    try:
        response = llm_with_tools.invoke([
            SystemMessage(content=system),
            HumanMessage(content=user),
        ])
    except Exception as e:
        print(f"  [supervisor] LLM error: {e}")
        return None, None

    if not response.tool_calls:
        print("  [supervisor] no tool call returned")
        return None, None

    action = response.tool_calls[0]["name"]
    reasoning = response.tool_calls[0].get("args", {}).get("reasoning", "")

    if action not in valid_actions:
        print(f"  [supervisor] invalid action '{action}'")
        return None, None

    return action, reasoning


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
        "pregenerated_mutants": [],
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


def step(state, action, reasoning=""):
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
    new["pregenerated_mutants"] = state["pregenerated_mutants"]
    new["grpo_rewards"] = dict(state["grpo_rewards"])
    new["step_count"] = state["step_count"] + 1

    outcome = dispatch(new, action)
    entry = {"step": new["step_count"], "action": action, "outcome": outcome}
    if reasoning:
        entry["reasoning"] = reasoning
    new["history"].append(entry)
    return new


def _serialize_state_for_log(state):
    out = {}
    for k, v in state.items():
        if k == "agent_kills":
            out[k] = {tt: sorted(ids) for tt, ids in v.items()}
        elif k == "function_info":
            out[k] = {"name": v["name"], "file_path": v.get("file_path", ""), "language": v.get("language", "")}
        elif k in ("repo_clone_dir", "output_dir", "config", "pregenerated_mutants"):
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

    print(f"  [{fn['name']}] pre-generating mutants...")
    mutants, _ = generate_all_mutants(fn["source"], fn=fn, config=config)
    state["pregenerated_mutants"] = mutants

    memory_context = ""
    try:
        from src.memory import get_db, get_collection, retrieve_similar, get_reflections, format_memory_context
        db = get_db()
        collection = get_collection(db)
        similar = retrieve_similar(collection, fn, k=5)
        reflections = get_reflections(db, limit=10)
        memory_context = format_memory_context(similar, reflections, state["planned_generates"])
    except Exception as e:
        print(f"  [memory] retrieval failed: {e}")

    errors_in_a_row = 0
    for i in range(max_steps):
        action, reasoning = llm_supervisor(state, memory_context)
        if action is None:
            errors_in_a_row += 1
            print(f"  [{fn['name']}] step {i + 1}: supervisor error (attempt {errors_in_a_row})")
            if errors_in_a_row >= 3:
                print(f"  [{fn['name']}] 3 consecutive supervisor errors, stopping")
                break
            continue
        errors_in_a_row = 0
        reasoning_snip = f" — {reasoning[:100]}..." if len(reasoning) > 100 else (f" — {reasoning}" if reasoning else "")
        print(f"  [{fn['name']}] step {i + 1}: {action}{reasoning_snip}")
        state = step(state, action, reasoning)
        print(f"    -> {state['history'][-1]['outcome']}")
        if state["done"]:
            break

    _save_trajectory(state)
    return state
