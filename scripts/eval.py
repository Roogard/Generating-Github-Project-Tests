"""
Evaluation script — compares 3 test-generation strategies on the same functions.

The three modes being compared:
    baseline          : all 7 agents run (no supervisor, no memory)
    supervisor_no_mem : supervisor picks 2-4 agents, no memory context
    supervisor_with_mem: supervisor picks 2-4 agents, with ChromaDB memory

Tests are generated ONCE (all 7 agents) and then filtered per mode — the LLM
is only called 7+2 times per function (7 agents + 2 supervisor calls), not 21.

Outputs (9 charts + summary.json):
    kill_rate.png           - kill rate per function per mode
    agents_used.png         - how many agents each supervisor mode picked
    efficiency.png          - kill rate / agents used
    selection_heatmap.png   - which agents each mode selected per function
    agent_frequency.png     - how often each agent is chosen per mode
    cost_quality.png        - scatter: agents used vs kill rate (Pareto view)
    kill_delta.png          - supervisor kill rate delta vs baseline
    complexity_breakdown.png- avg kill rate and efficiency by complexity tier
    scorecard.png           - headline: avg kill rate, agents used, cost savings

Usage:
    uv run python scripts/eval.py --repo https://github.com/keon/algorithms --limit 5
    uv run python scripts/eval.py --repo https://github.com/keon/algorithms --limit 10 --warmup 10
    uv run python scripts/eval.py --repos "url1,url2" --limit 15 --warmup 10
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
import matplotlib.patches as mpatches
import numpy as np

from dotenv import load_dotenv

from src.extractor import clone_repo, extract_functions
from src.agents import build_graph, TEST_TYPES
from src.supervisor import select_agents
from src.memory import (
    get_db, get_collection, get_reflections, retrieve_similar, format_memory_context,
    store_result, generate_reflections, store_reflection,
)
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
ALL_AGENTS = list(TEST_TYPES)


def parse_args():
    p = argparse.ArgumentParser(description="Evaluate 3 agent-selection strategies")
    p.add_argument("--repo", default="https://github.com/keon/algorithms", help="GitHub repo URL to evaluate on")
    p.add_argument("--repos", type=str, default=None,
                   help="Comma-separated repo URLs (overrides --repo for multi-repo eval)")
    p.add_argument("--limit", type=int, default=5, help="Number of functions to evaluate per repo")
    p.add_argument("--warmup", type=int, default=0,
                   help="Prime memory with N functions before eval (makes supervisor_with_mem meaningful)")
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


def compute_divergence(sel_a, sel_b):
    """Jaccard distance between two agent selections. 0=identical, 1=completely different."""
    a, b = set(sel_a), set(sel_b)
    if not a and not b:
        return 0.0
    return 1.0 - len(a & b) / len(a | b)


def divergence_label(dist):
    if dist == 0:
        return "same"
    elif dist < 0.5:
        return "partial"
    else:
        return "different"


def compute_redundancy(unique_kills, selected_agents):
    """Fraction of selected agents that killed zero unique mutants."""
    if not selected_agents:
        return 0.0
    zero = sum(1 for a in selected_agents if unique_kills.get(a, 0) == 0)
    return round(zero / len(selected_agents), 3)


def compute_aggregate_stats(func_names, all_results):
    """Per-mode avg kill rate, efficiency, agents used, and cost reduction vs baseline."""
    stats = {}
    for mode in MODES:
        rates = [all_results[fn][mode]["kill_rate"] for fn in func_names]
        effs = [all_results[fn][mode]["efficiency"] for fn in func_names]
        agents = [all_results[fn][mode]["agents_used"] for fn in func_names]
        avg_agents = sum(agents) / len(agents)
        stats[mode] = {
            "avg_kill_rate": round(sum(rates) / len(rates), 3),
            "avg_efficiency": round(sum(effs) / len(effs), 3),
            "avg_agents_used": round(avg_agents, 2),
            "cost_reduction_pct": round((7 - avg_agents) / 7 * 100, 1),
        }
    return stats


def compute_complexity_breakdown(func_names, all_results, complexities):
    """Group results by complexity tier, compute per-tier per-mode averages."""
    tiers = {"simple": [], "moderate": [], "complex": []}
    for fn in func_names:
        tier = complexities.get(fn, "moderate")
        tiers[tier].append(fn)

    breakdown = {}
    for tier, fns in tiers.items():
        if not fns:
            continue
        breakdown[tier] = {}
        for mode in MODES:
            rates = [all_results[fn][mode]["kill_rate"] for fn in fns]
            effs = [all_results[fn][mode]["efficiency"] for fn in fns]
            breakdown[tier][mode] = {
                "avg_kill_rate": round(sum(rates) / len(rates), 3),
                "avg_efficiency": round(sum(effs) / len(effs), 3),
                "count": len(fns),
            }
    return breakdown


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
    for tt in ALL_AGENTS:
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
        return {tt: set() for tt in ALL_AGENTS}, {tt: 0 for tt in ALL_AGENTS}, 0

    agent_kills, agent_totals, mutant_count = run_all_agents(
        func_file, test_files, repo_tmp, fn_source, original_file=original_file
    )

    for tt in ALL_AGENTS:
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
        "redundancy_rate": compute_redundancy(unique_kills, list(selected_agents)),
    }


def run_warmup(functions, collection, db, repo_tmp, output_dir):
    """Prime ChromaDB with N functions before eval so supervisor_with_mem has data."""
    warmup_dir = os.path.join(output_dir, "warmup_tests")
    batch_records = []
    warmed_names = set()

    print(f"\n  Warming up memory with {len(functions)} functions...")
    for idx, fn in enumerate(functions):
        fn_name = fn["name"]
        warmed_names.add(fn_name)
        print(f"  [warmup {idx+1}/{len(functions)}] {fn_name}...", end=" ", flush=True)

        asyncio.run(generate_all_tests(fn, warmup_dir, idx))
        all_test_files = get_test_files(fn_name, idx, warmup_dir)

        if not all_test_files:
            print("no test files, skipping")
            continue

        func_file = os.path.join(warmup_dir, "functions", f"{fn_name}_{idx}", "function.py")
        original_file = os.path.join(repo_tmp, fn["file_path"]) if fn.get("file_path") else None

        agent_kills, agent_totals, mutant_count = run_mutation_for_mode(
            "baseline", list(ALL_AGENTS), all_test_files, func_file, repo_tmp, fn["source"], original_file
        )
        unique_kills = compute_unique_kills(agent_kills)

        store_result(collection, fn, list(ALL_AGENTS), agent_kills, agent_totals, mutant_count, unique_kills)

        # build batch record for generate_reflections (matches ChromaDB metadata shape)
        rec = {
            "function_name": fn_name,
            "agents_selected": json.dumps(list(ALL_AGENTS)),
            "total_mutants": mutant_count,
        }
        overall_killed = 0
        overall_total = 0
        for agent in ALL_AGENTS:
            killed = len(agent_kills.get(agent, set()))
            total = agent_totals.get(agent, 0)
            rec[f"{agent}_killed"] = killed
            rec[f"{agent}_total"] = total
            rec[f"{agent}_unique"] = unique_kills.get(agent, 0)
            overall_killed += killed
            overall_total += total
        rec["overall_kill_rate"] = round(overall_killed / overall_total if overall_total > 0 else 0.0, 3)
        batch_records.append(rec)

        all_killed = set()
        for tt in ALL_AGENTS:
            all_killed |= agent_kills.get(tt, set())
        print(f"{len(all_killed)}/{mutant_count} killed, stored")

    if batch_records:
        print("  Generating reflections from warmup batch...")
        reflections = generate_reflections(batch_records)
        for r in reflections:
            store_reflection(db, r)
        print(f"  Stored {len(reflections)} reflections")

    return warmed_names


def print_function_summary(fn_name, results, lines, branches, divergence, redundancy_rates):
    print(f"\n  {'─'*65}")
    print(f"  Function: {fn_name}  ({lines} lines, {branches} branches, {results['baseline']['total_mutants']} mutants)")
    print(f"  Selection divergence (no-mem vs with-mem): {divergence_label(divergence)} "
          f"(Jaccard distance = {divergence:.2f})")
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
    nm_red = redundancy_rates.get("supervisor_no_mem", 0.0)
    wm_red = redundancy_rates.get("supervisor_with_mem", 0.0)
    print(f"  Redundancy (agents with 0 unique kills):  "
          f"no_mem={nm_red*100:.0f}%  with_mem={wm_red*100:.0f}%")


def print_cost_savings_headline(aggregate_stats):
    nm = aggregate_stats["supervisor_no_mem"]
    wm = aggregate_stats["supervisor_with_mem"]
    w = 62
    print(f"\n  {'╔' + '═'*w + '╗'}")
    print(f"  ║  {'COST SAVINGS vs BASELINE (fewer agent calls = lower cost)':<{w-2}}  ║")
    print(f"  ║  {'':<{w-2}}  ║")
    line1 = f"Supervisor (no mem):  saves {nm['cost_reduction_pct']:.1f}% of agent calls  (avg {nm['avg_agents_used']:.1f} agents)"
    line2 = f"Supervisor + Memory:  saves {wm['cost_reduction_pct']:.1f}% of agent calls  (avg {wm['avg_agents_used']:.1f} agents)"
    print(f"  ║  {line1:<{w-2}}  ║")
    print(f"  ║  {line2:<{w-2}}  ║")
    print(f"  {'╚' + '═'*w + '╝'}")


def print_complexity_breakdown(breakdown):
    if not breakdown:
        return
    print(f"\n  Complexity Breakdown:")
    print(f"  {'tier':10s}  {'mode':25s}  {'avg kill rate':>13s}  {'avg efficiency':>14s}  {'n':>4s}")
    print(f"  {'─'*10}  {'─'*25}  {'─'*13}  {'─'*14}  {'─'*4}")
    for tier in ["simple", "moderate", "complex"]:
        if tier not in breakdown:
            continue
        for mode in MODES:
            d = breakdown[tier][mode]
            print(f"  {tier:10s}  {MODE_LABELS[mode]:25s}  "
                  f"{d['avg_kill_rate']*100:>12.1f}%  {d['avg_efficiency']*100:>13.1f}%  "
                  f"{d['count']:>4d}")


# ── Chart 1: Kill rate grouped bars ──────────────────────────────────────────

def plot_kill_rates(func_names, all_results, output_dir):
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


# ── Chart 2: Agents used ──────────────────────────────────────────────────────

def plot_agents_used(func_names, all_results, output_dir):
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


# ── Chart 3: Efficiency line ──────────────────────────────────────────────────

def plot_efficiency(func_names, all_results, output_dir):
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


# ── Chart 4: Selection heatmap ────────────────────────────────────────────────

def plot_selection_heatmap(func_names, all_results, output_dir):
    no_mem_sels = [set(all_results[fn]["supervisor_no_mem"]["agents_selected"]) for fn in func_names]
    with_mem_sels = [set(all_results[fn]["supervisor_with_mem"]["agents_selected"]) for fn in func_names]

    n_fns = len(func_names)
    n_agents = len(ALL_AGENTS)

    color_map = {
        (True, True): "#2E8B57",
        (True, False): "#DD8452",
        (False, True): "#9467BD",
        (False, False): "#D8D8D8",
    }

    fig, ax = plt.subplots(figsize=(max(9, n_agents * 1.3), max(4, n_fns * 0.9 + 1.5)))

    for row, fn in enumerate(func_names):
        nm = no_mem_sels[row]
        wm = with_mem_sels[row]
        for col, agent in enumerate(ALL_AGENTS):
            in_nm = agent in nm
            in_wm = agent in wm
            color = color_map[(in_nm, in_wm)]
            rect = plt.Rectangle([col - 0.45, row - 0.45], 0.9, 0.9,
                                  facecolor=color, edgecolor="white", linewidth=1.5)
            ax.add_patch(rect)
            label = ""
            if in_nm and in_wm:
                label = "✓✓"
            elif in_nm:
                label = "N"
            elif in_wm:
                label = "M"
            if label:
                ax.text(col, row, label, ha="center", va="center", fontsize=8,
                        color="white", fontweight="bold")

    ax.set_xlim(-0.5, n_agents - 0.5)
    ax.set_ylim(-0.5, n_fns - 0.5)
    ax.set_xticks(range(n_agents))
    ax.set_xticklabels(ALL_AGENTS, fontsize=9)
    ax.set_yticks(range(n_fns))
    ax.set_yticklabels(func_names, fontsize=8)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlabel("Agent", fontsize=10, labelpad=8)
    ax.set_ylabel("Function", fontsize=10)
    ax.set_title("Agent Selection per Mode\n(✓✓=both supervisors, N=no-mem only, M=with-mem only, gray=neither)", fontsize=9, pad=20)

    legend_patches = [
        mpatches.Patch(color="#2E8B57", label="Both supervisors selected"),
        mpatches.Patch(color="#DD8452", label="No-mem supervisor only"),
        mpatches.Patch(color="#9467BD", label="With-mem supervisor only"),
        mpatches.Patch(color="#D8D8D8", label="Neither supervisor"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", bbox_to_anchor=(1.0, -0.15),
              ncol=2, fontsize=8, framealpha=0.9)

    plt.tight_layout()
    path = os.path.join(output_dir, "selection_heatmap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


# ── Chart 5: Agent frequency ──────────────────────────────────────────────────

def plot_agent_frequency(func_names, all_results, output_dir):
    n = len(func_names)
    no_mem_freq = {}
    with_mem_freq = {}
    for agent in ALL_AGENTS:
        no_mem_freq[agent] = sum(
            1 for fn in func_names if agent in all_results[fn]["supervisor_no_mem"]["agents_selected"]
        ) / n * 100
        with_mem_freq[agent] = sum(
            1 for fn in func_names if agent in all_results[fn]["supervisor_with_mem"]["agents_selected"]
        ) / n * 100

    y = np.arange(len(ALL_AGENTS))
    height = 0.35

    fig, ax = plt.subplots(figsize=(9, max(5, len(ALL_AGENTS) * 0.8)))
    bars_nm = ax.barh(y - height / 2, [no_mem_freq[a] for a in ALL_AGENTS], height,
                      label=MODE_LABELS["supervisor_no_mem"], color=MODE_COLORS["supervisor_no_mem"], alpha=0.85)
    bars_wm = ax.barh(y + height / 2, [with_mem_freq[a] for a in ALL_AGENTS], height,
                      label=MODE_LABELS["supervisor_with_mem"], color=MODE_COLORS["supervisor_with_mem"], alpha=0.85)

    ax.axvline(100, color=MODE_COLORS["baseline"], linestyle="--", linewidth=1.2,
               label="Baseline (always 100%)", alpha=0.8)

    for bar in bars_nm:
        w = bar.get_width()
        if w > 5:
            ax.text(w + 1, bar.get_y() + bar.get_height() / 2, f"{w:.0f}%",
                    va="center", fontsize=8)
    for bar in bars_wm:
        w = bar.get_width()
        if w > 5:
            ax.text(w + 1, bar.get_y() + bar.get_height() / 2, f"{w:.0f}%",
                    va="center", fontsize=8)

    ax.set_xlabel("% of functions where agent was selected")
    ax.set_ylabel("Agent")
    ax.set_title("Agent Selection Frequency by Mode\n(shows which agents memory teaches the supervisor to prefer)")
    ax.set_yticks(y)
    ax.set_yticklabels(ALL_AGENTS, fontsize=9)
    ax.set_xlim(0, 120)
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    path = os.path.join(output_dir, "agent_frequency.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


# ── Chart 6: Cost-quality scatter ────────────────────────────────────────────

def plot_cost_quality(func_names, all_results, output_dir):
    fig, ax = plt.subplots(figsize=(8, 6))

    for mode in MODES:
        xs = [all_results[fn][mode]["agents_used"] for fn in func_names]
        ys = [all_results[fn][mode]["kill_rate"] * 100 for fn in func_names]
        ax.scatter(xs, ys, color=MODE_COLORS[mode], label=MODE_LABELS[mode],
                   s=80, alpha=0.8, zorder=3)
        for fn, x, y in zip(func_names, xs, ys):
            short = fn[:10] + "…" if len(fn) > 10 else fn
            ax.annotate(short, (x, y), textcoords="offset points",
                        xytext=(4, 3), fontsize=6, color=MODE_COLORS[mode], alpha=0.8)

    ax.set_xlabel("Agents Used (cost proxy)")
    ax.set_ylabel("Kill Rate (%)")
    ax.set_title("Cost vs Quality per Mode\n(upper-left = efficient; upper-right = thorough)")
    ax.set_xlim(0, 8.5)
    ax.set_ylim(-5, 115)
    ax.set_xticks(range(1, 8))
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    path = os.path.join(output_dir, "cost_quality.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


# ── Chart 7: Kill rate delta vs baseline ──────────────────────────────────────

def plot_kill_delta(func_names, all_results, output_dir):
    x = np.arange(len(func_names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(max(8, len(func_names) * 2), 5))
    for i, mode in enumerate(["supervisor_no_mem", "supervisor_with_mem"]):
        deltas = [
            (all_results[fn][mode]["kill_rate"] - all_results[fn]["baseline"]["kill_rate"]) * 100
            for fn in func_names
        ]
        bars = ax.bar(x + (i - 0.5) * width, deltas, width, label=MODE_LABELS[mode],
                      color=MODE_COLORS[mode], alpha=0.85, edgecolor="white")
        for bar, delta in zip(bars, deltas):
            ypos = bar.get_height() + 0.5 if delta >= 0 else bar.get_height() - 2
            ax.text(bar.get_x() + bar.get_width() / 2, ypos,
                    f"{delta:+.0f}%", ha="center", va="bottom", fontsize=8)

    ax.axhline(0, color="black", linewidth=1.0)
    ax.set_xlabel("Function")
    ax.set_ylabel("Kill Rate Delta vs Baseline (%)")
    ax.set_title("Quality Cost of Supervisor Mode vs Baseline\n(negative = supervisor missed mutants that baseline would have caught)")
    ax.set_xticks(x)
    ax.set_xticklabels(func_names, rotation=30, ha="right", fontsize=9)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    path = os.path.join(output_dir, "kill_delta.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


# ── Chart 8: Complexity breakdown ────────────────────────────────────────────

def plot_complexity_breakdown(breakdown, output_dir):
    """1×2 subplots: avg kill rate and avg efficiency per complexity tier per mode."""
    tiers = [t for t in ["simple", "moderate", "complex"] if t in breakdown]
    if not tiers:
        return

    x = np.arange(len(tiers))
    width = 0.25

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    for i, mode in enumerate(MODES):
        rates = [breakdown[t][mode]["avg_kill_rate"] * 100 for t in tiers]
        effs = [breakdown[t][mode]["avg_efficiency"] * 100 for t in tiers]

        bars1 = ax1.bar(x + (i - 1) * width, rates, width, label=MODE_LABELS[mode],
                        color=MODE_COLORS[mode], alpha=0.85, edgecolor="white")
        bars2 = ax2.bar(x + (i - 1) * width, effs, width, label=MODE_LABELS[mode],
                        color=MODE_COLORS[mode], alpha=0.85, edgecolor="white")

        for bar, v in zip(bars1, rates):
            if v > 2:
                ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                         f"{v:.0f}%", ha="center", va="bottom", fontsize=7)
        for bar, v in zip(bars2, effs):
            if v > 2:
                ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                         f"{v:.0f}%", ha="center", va="bottom", fontsize=7)

    for ax, title, ylabel in [
        (ax1, "Avg Kill Rate by Complexity", "Avg Kill Rate (%)"),
        (ax2, "Avg Efficiency by Complexity", "Avg Efficiency (kill rate / agents × 100)"),
    ]:
        ax.set_xlabel("Complexity Tier")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(tiers)
        ax.set_ylim(0, 115)
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Performance by Complexity Tier", fontsize=12, y=1.02)
    plt.tight_layout()
    path = os.path.join(output_dir, "complexity_breakdown.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


# ── Chart 9: Scorecard ────────────────────────────────────────────────────────

def plot_scorecard(aggregate_stats, output_dir):
    """3-panel horizontal bar chart: avg kill rate, avg agents used, cost savings."""
    mode_labels = [MODE_LABELS[m] for m in MODES]
    colors = [MODE_COLORS[m] for m in MODES]
    y = np.arange(len(MODES))

    kill_rates = [aggregate_stats[m]["avg_kill_rate"] * 100 for m in MODES]
    agents_used = [aggregate_stats[m]["avg_agents_used"] for m in MODES]
    cost_savings = [aggregate_stats[m]["cost_reduction_pct"] for m in MODES]

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    panels = [
        (axes[0], kill_rates, "Avg Kill Rate (%)", 0, 110, "{:.1f}%"),
        (axes[1], agents_used, "Avg Agents Used", 0, 8.5, "{:.1f}"),
        (axes[2], cost_savings, "Cost Savings vs Baseline (%)", 0, 80, "{:.1f}%"),
    ]

    for ax, values, title, xmin, xmax, fmt in panels:
        bars = ax.barh(y, values, color=colors, alpha=0.85, edgecolor="white")
        for bar, v in zip(bars, values):
            ax.text(v + xmax * 0.01, bar.get_y() + bar.get_height() / 2,
                    fmt.format(v), va="center", fontsize=9, fontweight="bold")
        ax.set_yticks(y)
        ax.set_yticklabels(mode_labels, fontsize=9)
        ax.set_xlim(xmin, xmax)
        ax.set_title(title, fontsize=10)
        ax.grid(axis="x", alpha=0.3)
        ax.invert_yaxis()

    fig.suptitle("Eval Scorecard — 3 Headline Metrics", fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(output_dir, "scorecard.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


# ── Overall summary ───────────────────────────────────────────────────────────

def print_overall_summary(func_names, all_results, divergences, aggregate_stats, breakdown):
    avg_divergence = sum(divergences.values()) / len(divergences) if divergences else 0.0
    pct_changed = sum(1 for d in divergences.values() if d > 0) / len(divergences) * 100 if divergences else 0.0

    print(f"\n{'='*70}")
    print("  OVERALL SUMMARY")
    print(f"{'='*70}")
    print(f"  {'mode':25s}  {'avg kill rate':>13s}  {'avg agents':>10s}  {'avg efficiency':>14s}")
    print(f"  {'─'*25}  {'─'*13}  {'─'*10}  {'─'*14}")
    for mode in MODES:
        s = aggregate_stats[mode]
        print(f"  {MODE_LABELS[mode]:25s}  {s['avg_kill_rate']*100:>12.1f}%  "
              f"{s['avg_agents_used']:>10.1f}  {s['avg_efficiency']*100:>13.1f}%")

    print("\n  Selection divergence (no-mem vs with-mem):")
    print(f"    Memory changed selection in {pct_changed:.0f}% of functions  (avg Jaccard distance = {avg_divergence:.2f})")
    if avg_divergence == 0:
        print("    NOTE: memory had NO effect on agent selection — supervisor ignores memory context.")
    elif avg_divergence < 0.3:
        print("    NOTE: memory had MINOR effect — selections are mostly the same.")
    else:
        print("    NOTE: memory had MEANINGFUL effect on selection choices.")
    print(f"{'='*70}")

    print_cost_savings_headline(aggregate_stats)
    print_complexity_breakdown(breakdown)


def main():
    load_dotenv()
    config = parse_args()

    output_dir = config["output"]
    os.makedirs(output_dir, exist_ok=True)

    # Load memory (warmup may write to it; eval reads from it)
    db = get_db()
    collection = get_collection(db)
    reflections = get_reflections(db, limit=10)
    print(f"Memory: {collection.count()} records, {len(reflections)} reflections")

    # Build repo list
    if config["repos"]:
        repo_list = [r.strip() for r in config["repos"].split(",") if r.strip()]
    else:
        repo_list = [config["repo"]]

    multi_repo = len(repo_list) > 1
    limit = config["limit"]
    warmup_n = config["warmup"]

    all_results = {}
    divergences = {}
    complexities = {}
    redundancy_rates = {}

    for repo in repo_list:
        repo_name = repo.rstrip("/").split("/")[-1]
        print(f"\n{'='*70}")
        print(f"  REPO: {repo}")
        print(f"{'='*70}")

        repo_tmp = tempfile.mkdtemp()
        print(f"\nCloning {repo}...")
        clone_repo(repo, repo_tmp)

        all_fns = extract_functions(repo_tmp)
        print(f"Extracted: {len(all_fns)} functions")

        filtered = filter_functions(all_fns, config["min_lines"], config["max_lines"], config["min_branches"])
        print(f"After filters: {len(filtered)} functions")

        warmed_names = set()
        if warmup_n > 0:
            warmup_sample = _stratified_sample(filtered, warmup_n)
            warmed_names = run_warmup(warmup_sample, collection, db, repo_tmp, output_dir)
            print(f"Memory after warmup: {collection.count()} records")
            eval_pool = [f for f in filtered if f["name"] not in warmed_names]
            if len(eval_pool) < limit:
                print(f"  WARNING: only {len(eval_pool)} functions left for eval after warmup (requested {limit})")
        else:
            eval_pool = filtered

        functions = _stratified_sample(eval_pool, limit)
        print(f"Sampled: {len(functions)} functions (stratified)")

        print(f"\n{'='*70}")
        print(f"  EVALUATING {len(functions)} FUNCTIONS — 3 MODES")
        print(f"{'='*70}")

        # Refresh reflections after warmup
        reflections = get_reflections(db, limit=10)

        for idx, fn in enumerate(functions):
            fn_name = fn["name"]
            key = f"{repo_name}/{fn_name}" if multi_repo else fn_name
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

            div = compute_divergence(selected_no_mem, selected_with_mem)
            divergences[key] = div

            # Step 3: Mutation testing for each mode
            func_file = os.path.join(fn_output_dir, "functions", f"{fn_name}_{idx}", "function.py")
            original_file = os.path.join(repo_tmp, fn["file_path"]) if fn.get("file_path") else None

            fn_results = {}
            for mode, selected in [
                ("baseline", list(ALL_AGENTS)),
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

            all_results[key] = fn_results
            complexities[key] = complexity
            redundancy_rates[key] = {
                "supervisor_no_mem": fn_results["supervisor_no_mem"]["redundancy_rate"],
                "supervisor_with_mem": fn_results["supervisor_with_mem"]["redundancy_rate"],
            }

            fn_redund = {
                "supervisor_no_mem": fn_results["supervisor_no_mem"]["redundancy_rate"],
                "supervisor_with_mem": fn_results["supervisor_with_mem"]["redundancy_rate"],
            }
            print_function_summary(key, fn_results, lines, branches, div, fn_redund)

        shutil.rmtree(repo_tmp, ignore_errors=True)

    # Aggregate stats and breakdown
    func_names = list(all_results.keys())
    aggregate_stats = compute_aggregate_stats(func_names, all_results)
    breakdown = compute_complexity_breakdown(func_names, all_results, complexities)

    print_overall_summary(func_names, all_results, divergences, aggregate_stats, breakdown)

    # Save JSON results
    summary_path = os.path.join(output_dir, "summary.json")
    functions_out = {}
    for fn in func_names:
        fn_data = {"complexity": complexities[fn]}
        for mode in MODES:
            fn_data[mode] = all_results[fn][mode]
        functions_out[fn] = fn_data

    out = {
        "repo": config["repo"] if not multi_repo else None,
        "repos": repo_list if multi_repo else None,
        "warmup_count": warmup_n,
        "functions": functions_out,
        "divergences": {fn: round(d, 3) for fn, d in divergences.items()},
        "redundancy_rates": redundancy_rates,
        "aggregate": aggregate_stats,
        "complexity_breakdown": breakdown,
    }
    # drop None keys
    out = {k: v for k, v in out.items() if v is not None}

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\n  Results saved: {summary_path}")

    # Generate all 9 charts
    print("\n  Generating charts...")
    plot_kill_rates(func_names, all_results, output_dir)
    plot_agents_used(func_names, all_results, output_dir)
    plot_efficiency(func_names, all_results, output_dir)
    plot_selection_heatmap(func_names, all_results, output_dir)
    plot_agent_frequency(func_names, all_results, output_dir)
    plot_cost_quality(func_names, all_results, output_dir)
    plot_kill_delta(func_names, all_results, output_dir)
    plot_complexity_breakdown(breakdown, output_dir)
    plot_scorecard(aggregate_stats, output_dir)

    print(f"\nDone. Open {output_dir}/ to see charts.")


if __name__ == "__main__":
    main()
