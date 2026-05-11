# GGPT (Generating Github Project Tests)

Issue-driven AI agent that reads GitHub bug reports and writes regression tests reproducing the bug. Evaluated on **SWT-Bench Lite** (300 real GitHub issues) using the F→P / F→F / P→F / P→P transition oracle.

The agent is given a repo + base commit and the issue text. It localizes the relevant code itself via Claude Code-shaped tools (Glob, Grep, Read, Edit, Write), writes a pytest file, and the harness auto-runs pytest after every modification. The agent declares done by emitting a final assistant message with no tool calls.

When the task carries a `gold_patch` (SWT-Bench), the runner grades post-hoc: run tests on buggy → apply patch → run on fixed → label each test's transition. **Grading never feeds back into the agent loop** — the agent must reproduce the bug from the issue alone.

For the full pipeline diagram, file structure, REST API, metrics reference, and local-dev instructions, see [ARCHITECTURE.md](ARCHITECTURE.md). Adopter-facing setup lives in [README.md](README.md).

---

## Guiding constraints

- All runs go through webapp → API → DB. No CLI entry points.
- The harness owns side effects (subprocess, file writes, runtime preamble). Skills are LLM calls — they don't run pytest or write files. The agentic loop's auto-pytest hook (fires after Write or Edit on `ctx.test_file_path`) routes through `ctx.runtime.exec` like everything else.
- All process invocations go through `ctx.runtime.exec(...)`. Never call `subprocess.run` directly from `test_runner.py` or `oracle.py` — adding it back breaks Docker isolation. Host-side `git apply` against the mounted clone is fine (oracle uses this on Local/Docker runtimes).
- The agent gets the issue, never the gold patch and never `touched_files`. Mirroring SWE-Agent / OpenHands / Otter — the agent must localize from the issue alone for fairness.
- Pytest assertion failures are NOT improve signals. Only collection / setup / timeout failures trigger Improve. Silencing an assertion that matches the issue would silence an F→P detection.
- Real iteration happens inside Generate's agentic loop. The outer harness only invokes Improve once, and only for *infrastructure* failures (collection error, fixture failure, AttributeError on construction). Pytest assertion failures do NOT trigger Improve.
