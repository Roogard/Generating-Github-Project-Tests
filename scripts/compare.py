import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

METRICS = [
    ("quality_score", "Avg quality score", ".3f", 1),
    ("mutation_score", "Avg mutation score", ".1%", 1),
    ("llm_mutation_score", "Avg LLM mutation", ".1%", 1),
    ("line_coverage", "Avg line coverage", ".1%", 1),
    ("branch_coverage", "Avg branch coverage", ".1%", 1),
    ("steps", "Avg steps", ".1f", -1),
]


def load_runs(base_dir):
    pattern = os.path.join(base_dir, "*", "benchmark_results.json")
    paths = sorted(glob.glob(pattern))
    runs = []
    for p in paths:
        run_name = os.path.basename(os.path.dirname(p))
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        ok = [r for r in data if r.get("status") == "ok"]
        runs.append({"name": run_name, "results": data, "ok": ok})
    return runs


def avg(results, key):
    vals = [r.get(key, 0) for r in results]
    return sum(vals) / len(vals) if vals else 0


def fmt(val, spec):
    return format(val, spec)


def compare(base_dir, last):
    runs = load_runs(base_dir)
    if not runs:
        print("No benchmark runs found in", base_dir)
        print("Run: uv run python scripts/benchmark.py --limit 5")
        return

    if last > 0:
        runs = runs[-last:]

    print("=== Benchmark Run Comparison ===\n")
    print("Runs found:")
    for i, run in enumerate(runs):
        print(f"  [{i + 1}] {run['name']}  ({len(run['ok'])} functions ok, "
              f"{len(run['results']) - len(run['ok'])} skipped/errored)")
    print()

    # aggregate summary
    print("--- Aggregate Summary ---")
    header = "  {:25s}".format("")
    for i in range(len(runs)):
        header += f"  {'Run ' + str(i + 1):>12s}"
    if len(runs) >= 2:
        header += f"  {'Delta':>12s}"
    print(header)

    for key, label, spec, direction in METRICS:
        row = f"  {label:25s}"
        avgs = []
        for run in runs:
            v = avg(run["ok"], key)
            avgs.append(v)
            row += f"  {fmt(v, spec):>12s}"
        if len(runs) >= 2:
            delta = avgs[-1] - avgs[-2]
            sign = "+" if delta >= 0 else ""
            row += f"  {sign}{fmt(delta, spec):>11s}"
        print(row)
    print()

    # per-function comparison (only if 2+ runs)
    if len(runs) >= 2:
        prev_run = runs[-2]
        curr_run = runs[-1]

        prev_by_fn = {r["function"]: r for r in prev_run["ok"]}
        curr_by_fn = {r["function"]: r for r in curr_run["ok"]}
        all_fns = sorted(set(prev_by_fn.keys()) | set(curr_by_fn.keys()))

        if all_fns:
            print("--- Per-Function Comparison (last 2 runs) ---")
            print(f"  {'Function':25s} {'Diff':10s} {'quality(-1)':>12s} {'quality(now)':>12s} {'delta':>8s}")

            improved = regressed = unchanged = 0
            for fn_name in all_fns:
                prev = prev_by_fn.get(fn_name)
                curr = curr_by_fn.get(fn_name)
                diff = (prev or curr).get("difficulty", "?")

                pq = prev["quality_score"] if prev else 0
                cq = curr["quality_score"] if curr else 0
                delta = cq - pq

                if abs(delta) < 0.005:
                    unchanged += 1
                elif delta > 0:
                    improved += 1
                else:
                    regressed += 1

                sign = "+" if delta >= 0 else ""
                print(f"  {fn_name:25s} {diff:10s} {pq:12.3f} {cq:12.3f} {sign}{delta:7.3f}")

            print(f"\n  Improved: {improved}/{len(all_fns)}, "
                  f"Regressed: {regressed}/{len(all_fns)}, "
                  f"Unchanged: {unchanged}/{len(all_fns)}")
            print()

    # single run: just show per-function detail
    if len(runs) == 1:
        run = runs[0]
        print("--- Per-Function Results ---")
        print(f"  {'Function':25s} {'Diff':10s} {'quality':>8s} {'mutation':>9s} {'line':>8s} {'branch':>8s} {'steps':>6s}")
        for r in run["ok"]:
            print(f"  {r['function']:25s} {r.get('difficulty', '?'):10s} "
                  f"{r['quality_score']:8.3f} {r['mutation_score']:8.1%} "
                  f"{r.get('line_coverage', 0):8.1%} {r.get('branch_coverage', 0):8.1%} "
                  f"{r['steps']:6d}")
        print()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Compare benchmark runs")
    p.add_argument("--dir", default="eval_output", help="Base benchmark directory")
    p.add_argument("--last", type=int, default=0, help="Compare only the last N runs (0 = all)")
    args = p.parse_args()
    compare(args.dir, args.last)
