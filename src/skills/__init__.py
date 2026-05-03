"""LLM-call wrappers driven by the harness.

Each skill (Analyze, Generate, Improve, Critique) takes a `HarnessContext`
and runs one (or, for agentic skills, several) LLM invocations. Skills
mutate `ctx.analysis`, `ctx.attempts`, `ctx.last_critique`, etc.; the
harness reads them and dispatches the next step.

## Why skills are imported lazily inside `run_harness` (not at module top)

Skills depend on `HarnessContext` (defined in `src.harness.state`), and the
harness drives skills. The arrow is one-way: harness → skill. Importing
the skills at the top of `src/harness/pipeline.py` would put both modules
on each other's import path, which works in CPython today but is fragile
to package-init ordering changes (e.g., if anything else imports
`src.skills` before the harness has finished initialising).

The lazy import inside `run_harness()` keeps the dependency one-directional
without paying any meaningful cost — `run_harness` is called once per task,
not in a hot loop, so the per-call import lookup is free. **Do not move
those imports to module top-level**; the comment in `pipeline.py` exists
because someone will eventually try.
"""
