"""
Evaluation script — compares 3 test-generation strategies on the same functions.

The three modes being compared:
    baseline          : all 7 agents run (no supervisor, no memory)
    supervisor_no_mem : supervisor picks 2-4 agents, no memory context
    supervisor_with_mem: supervisor picks 2-4 agents, with ChromaDB memory

Tests are generated ONCE (all 7 agents) and then filtered per mode — the LLM
is only called 7+2 times per function (7 agents + 2 supervisor calls), not 21.

Usage:
    uv run python scripts/eval.py --repo https://github.com/keon/algorithms --limit 5
    uv run python scripts/eval.py --repo https://github.com/keon/algorithms --limit 5 --output ./my_eval
"""
import argparse
import asyncio
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")  # non-interactive backend (no GUI required)
import matplotlib.pyplot as plt
import numpy as np

from dotenv import load_dotenv

from src.extractor import clone_repo, extract_functions
from src.agents import build_graph, TEST_TYPES
from src.supervisor import select_agents
from src.memory import get_db, get_collection, get_reflections, retrieve_similar, format_memory_context
from src.mutator import run_all_agents, compute_unique_kills
from src.writer import write_function, write_tests
from src.main import _fn_complexity, _classify_complexity, _stratified_sample


MODES = ["baseline", "supervisor_no_mem", "supervisor_with_mem"]
MODE_LABELS = {
    "baseline": "Baseline (all 7)",
    "supervisor_no_mem": "Supervisor (no memory)",
    "supervisor_with_mem": "Supervisor + Memory",
}
MODE_COLORS = {
    "baseline": "#4C72B0",
    "supervisor_no_mem": "#DD8452",
    "supervisor_with_mem": "#55A868",
}


def parse_args():
    p = argparse.ArgumentParser(description="Evaluate 3 agent-selection strategies")
    p.add_argument("--repo", default="https://github.com/keon/algorithms", help="GitHub repo URL to evaluate on")
    p.add_argument("--limit", type=int, default=5, help="Number of functions to evaluate")
    p.add_argument("--output", default="./eval_output", help="Output directory for results and charts")
    p.add_argument("--min-lines", type=int, default=5, dest="min_lines")
    p.add_argument("--max-lines", type=int, default=80, dest="max_lines")
    p.add_argument("--min-branches", type=int, default=1, dest="min_branches")
    return vars(p.parse_args())


def filter_functions(functions, min_lines, max_lines, min_branches):
    fns = [f for f in functions if min_lines <= len(f["source"].strip().splitlines()) <= max_lines]
    if min_branches > 0:
        fns = [f for f in fns if _fn_complexity(f["source"])[1] >= min_branches]
    return fns


async def generate_all_tests(fn, output_dir, index):
    """Generate tests with all 7 agents for a single function."""
    graph = build_graph()  # all 7 agents
    state = {
        "function_info": fn,
        "statement_tests": "", "block_tests": "", "condition_tests": "",
        "path_tests": "", "bva_tests": "", "ecp_tests": "", "mutation_tests": "",
    }
    result = await graph.ainvoke(state)
    write_function(fn, output_dir, index)
    write_tests(fn, result, output_dir, index)
    return result


def get_test_files(fn_name, index, output_dir):
    """Return a dict of {test_type: file_path} for all generated test files."""
    test_dir = os.path.join(output_dir, "test_cases", f"{fn_name}_{index}")
    files = {}
    for tt in TEST_TYPES:
        path = os.path.join(test_dir, f"test_{tt}.py")
        if os.path.exists(path):
            files[tt] = path
    return files


def run_mutation_for_mode(mode_name, selected_agents, all_test_files, func_file, repo_tmp, fn_source, original_file):
    """Run mutation testing using only the test files for the selected agents."""
    if mode_name == "baseline":
        test_files = all_test_files  # all 7
    else:
        test_files = {tt: path for tt, path in all_test_files.items() if tt in selected_agents}

    if not test_files:
        return {tt: set() for tt in TEST_TYPES}, {tt: 0 for tt in TEST_TYPES}, 0

    agent_kills, agent_totals, mutant_count = run_all_agents(
        func_file, test_files, repo_tmp, fn_source, original_file=original_file
    )

    # Fill zeros for agents not in this mode
    for tt in TEST_TYPES:
        if tt not in agent_kills:
            agent_kills[tt] = set()
            agent_totals[tt] = 0

    return agent_kills, agent_totals, mutant_count


def compute_summary(agent_kills, agent_totals, mutant_count, selected_agents):
    """Compute kill rate and per-agent stats for one mode's results."""
    all_killed = set()
    for tt in selected_agents:
        all_killed |= agent_kills.get(tt, set())

    unique_kills = compute_unique_kills({tt: agent_kills.get(tt, set()) for tt in selected_agents})

    kill_rate = len(all_killed) / mutant_count if mutant_count > 0 else 0.0
    return {
        "kill_rate": round(kill_rate, 3),
        "killed": len(all_killed),
        "total_mutants": mutant_count,
        "agents_used": len(selected_agents),
        "agents_selected": list(selected_agents),
        "efficiency": round(kill_rate / len(selected_agents), 3) if selected_agents else 0.0,
        "unique_kills": {tt: unique_kills.get(tt, 0) for tt in selected_agents},
    }


def print_function_summary(fn_name, results, lines, branches):
    print(f"\n  {'─'*60}")
    print(f"  Function: {fn_name}  ({lines} lines, {branches} branches, {results['baseline']['total_mutants']} mutants)")
    print(f"  {'mode':25s}  {'agents':>6s}  {'killed':>8s}  {'rate':>7s}  {'efficiency':>10s}")
    print(f"  {'─'*25}  {'─'*6}  {'─'*8}  {'─'*7}  {'─'*10}")
    for mode in MODES:
        r = results[mode]
        bar_len = int(r["kill_rate"] * 20)
        bar = "#" * bar_len + "." * (20 - bar_len)
        print(f"  {MODE_LABELS[mode]:25s}  {r['agents_used']:>6d}  "
              f"{r['killed']:>3d}/{r['total_mutants']:<3d}  {r['kill_rate']*100:>5.1f}%  "
              f"{r['efficiency']*100:>8.1f}%  [{bar}]")
        if mode != "baseline":
            print(f"    {'agents':25s}: {r['agents_selected']}")


def plot_kill_rates(func_names, all_results, output_dir):
    """Grouped bar chart: kill rate per function per mode."""
    x = np.arange(len(func_names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(max(8, len(func_names) * 2), 6))
    for i, mode in enumerate(MODES):
        rates = [all_results[fn][mode]["kill_rate"] * 100 for fn in func_names]
        bars = ax.bar(x + (i - 1) * width, rates, width, label=MODE_LABELS[mode],
                      color=MODE_COLORS[mode], alpha=0.85, edgecolor="white")
        for bar, rate in zip(bars, rates):
            if rate > 5:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                        f"{rate:.0f}%", ha="center", va="bottom", fontsize=7)

    ax.set_xlabel("Function")
    ax.set_ylabel("Mutant Kill Rate (%)")
    ax.set_title("Kill Rate by Mode (higher = better test quality)")
    ax.set_xticks(x)
    ax.set_xticklabels(func_names, rotation=30, ha="right", fontsize=9)
    ax.set_ylim(0, 115)
    ax.axhline(100, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    path = os.path.join(output_dir, "kill_rate.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def plot_agents_used(func_names, all_results, output_dir):
    """Bar chart: agents used per mode (baseline=7 as reference line)."""
    x = np.arange(len(func_names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(max(8, len(func_names) * 2), 5))
    for i, mode in enumerate(["supervisor_no_mem", "supervisor_with_mem"]):
        counts = [all_results[fn][mode]["agents_used"] for fn in func_names]
        bars = ax.bar(x + (i - 0.5) * width, counts, width, label=MODE_LABELS[mode],
                      color=MODE_COLORS[mode], alpha=0.85, edgecolor="white")
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    str(count), ha="center", va="bottom", fontsize=9)

    ax.axhline(7, color=MODE_COLORS["baseline"], linestyle="--", linewidth=1.5,
               label="Baseline (all 7)", alpha=0.8)
    ax.set_xlabel("Function")
    ax.set_ylabel("Agents Used")
    ax.set_title("Agent Count per Mode (fewer = more efficient)")
    ax.set_xticks(x)
    ax.set_xticklabels(func_names, rotation=30, ha="right", fontsize=9)
    ax.set_ylim(0, 9)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    path = os.path.join(output_dir, "agents_used.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def plot_efficiency(func_names, all_results, output_dir):
    """Line chart: kill_rate / agents_used per mode (higher = better efficiency)."""
    fig, ax = plt.subplots(figsize=(max(8, len(func_names) * 2), 5))
    x = np.arange(len(func_names))

    for mode in MODES:
        efficiencies = [all_results[fn][mode]["efficiency"] * 100 for fn in func_names]
        ax.plot(x, efficiencies, marker="o", label=MODE_LABELS[mode],
                color=MODE_COLORS[mode], linewidth=2, markersize=7)
        for xi, eff in zip(x, efficiencies):
            ax.annotate(f"{eff:.1f}%", (xi, eff), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=8)

    ax.set_xlabel("Function")
    ax.set_ylabel("Coverage Efficiency (kill rate / agents used × 100)")
    ax.set_title("Efficiency per Mode (kill quality per agent used)")
    ax.set_xticks(x)
    ax.set_xticklabels(func_names, rotation=30, ha="right", fontsize=9)
    ax.legend(loc="upper right")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    path = os.path.join(output_dir, "efficiency.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def print_overall_summary(func_names, all_results):
    print(f"\n{'='*70}")
    print("  OVERALL SUMMARY")
    print(f"{'='*70}")
    print(f"  {'mode':25s}  {'avg kill rate':>13s}  {'avg agents':>10s}  {'avg efficiency':>14s}")
    print(f"  {'─'*25}  {'─'*13}  {'─'*10}  {'─'*14}")
    for mode in MODES:
        rates = [all_results[fn][mode]["kill_rate"] for fn in func_names]
        agents = [all_results[fn][mode]["agents_used"] for fn in func_names]
        effs = [all_results[fn][mode]["efficiency"] for fn in func_names]
        avg_rate = sum(rates) / len(rates) * 100
        avg_agents = sum(agents) / len(agents)
        avg_eff = sum(effs) / len(effs) * 100
        print(f"  {MODE_LABELS[mode]:25s}  {avg_rate:>12.1f}%  {avg_agents:>10.1f}  {avg_eff:>13.1f}%")
    print(f"{'='*70}")


def main():
    load_dotenv()
    config = parse_args()

    repo = config["repo"]
    limit = config["limit"]
    output_dir = config["output"]

    os.makedirs(output_dir, exist_ok=True)

    # Load memory (read-only — eval does NOT store results)
    db = get_db()
    collection = get_collection(db)
    reflections = get_reflections(db, limit=10)
    print(f"Memory: {collection.count()} records, {len(reflections)} reflections")

    # Clone repo and extract functions
    repo_tmp = tempfile.mkdtemp()
    print(f"\nCloning {repo}...")
    clone_repo(repo, repo_tmp)

    all_fns = extract_functions(repo_tmp)
    print(f"Extracted: {len(all_fns)} functions")

    filtered = filter_functions(all_fns, config["min_lines"], config["max_lines"], config["min_branches"])
    print(f"After filters: {len(filtered)} functions")

    functions = _stratified_sample(filtered, limit)
    print(f"Sampled: {len(functions)} functions (stratified)")

    print(f"\n{'='*70}")
    print(f"  EVALUATING {len(functions)} FUNCTIONS — 3 MODES")
    print(f"{'='*70}")

    all_results = {}  # func_name -> {mode -> summary}

    for idx, fn in enumerate(functions):
        fn_name = fn["name"]
        lines, branches = _fn_complexity(fn["source"])
        complexity = _classify_complexity(fn["source"])
        print(f"\n[{idx+1}/{len(functions)}] {fn_name}  ({lines} lines, {branches} branches, {complexity})")

        fn_output_dir = os.path.join(output_dir, "test_files")

        # Step 1: Generate tests with all 7 agents
        print("  Generating tests (all 7 agents)...")
        asyncio.run(generate_all_tests(fn, fn_output_dir, idx))

        all_test_files = get_test_files(fn_name, idx, fn_output_dir)
        print(f"  Generated: {len(all_test_files)} test files ({list(all_test_files.keys())})")

        # Step 2: Supervisor selections
        print("  Supervisor (no memory)...", end=" ", flush=True)
        selected_no_mem = select_agents(fn)
        print(selected_no_mem)

        print("  Supervisor (with memory)...", end=" ", flush=True)
        similar = retrieve_similar(collection, fn, k=5)
        ctx = format_memory_context(similar, reflections)
        selected_with_mem = select_agents(fn, memory_context=ctx if ctx else None)
        print(selected_with_mem)

        # Step 3: Mutation testing for each mode
        func_file = os.path.join(fn_output_dir, "functions", f"{fn_name}_{idx}", "function.py")
        original_file = os.path.join(repo_tmp, fn["file_path"]) if fn.get("file_path") else None

        fn_results = {}

        for mode, selected in [
            ("baseline", list(TEST_TYPES)),
            ("supervisor_no_mem", selected_no_mem),
            ("supervisor_with_mem", selected_with_mem),
        ]:
            print(f"  Mutation testing [{mode}]...", end=" ", flush=True)
            agent_kills, agent_totals, mutant_count = run_mutation_for_mode(
                mode, selected, all_test_files, func_file, repo_tmp, fn["source"], original_file
            )
            summary = compute_summary(agent_kills, agent_totals, mutant_count, selected)
            fn_results[mode] = summary
            print(f"{summary['killed']}/{summary['total_mutants']} killed ({summary['kill_rate']*100:.1f}%)")

        all_results[fn_name] = fn_results
        print_function_summary(fn_name, fn_results, lines, branches)

    # Overall summary
    func_names = list(all_results.keys())
    print_overall_summary(func_names, all_results)

    # Save JSON results
    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"repo": repo, "functions": all_results}, f, indent=2)
    print(f"\n  Results saved: {summary_path}")

    # Generate charts
    print("\n  Generating charts...")
    plot_kill_rates(func_names, all_results, output_dir)
    plot_agents_used(func_names, all_results, output_dir)
    plot_efficiency(func_names, all_results, output_dir)

    shutil.rmtree(repo_tmp, ignore_errors=True)
    print(f"\nDone. Open {output_dir}/ to see charts.")


if __name__ == "__main__":
    main()
