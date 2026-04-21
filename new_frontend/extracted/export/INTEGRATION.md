# GGPT Dashboard Redesign — Integration Guide

Two files replace existing project files as-is. The rest is a short todo list for Claude Code / yourself.

## 1. Drop-in file replacements

| File in this folder | Replace in your project |
|---|---|
| `index.css` | `webapp/src/index.css` |
| `App.jsx`   | `webapp/src/App.jsx` |

Everything keeps the same class names (`.card`, `.btn-primary`, `.stat-card`, `.badge-done`, `.chip-pass`, `.tab`, `.progress-bar-wrap`, etc.), so existing pages pick up the new look automatically. The CSS adds a few new helper classes (`.chip-bench`, `.oracle-*`, `.segmented`, `.nav-logo-dot`, `.section-label`, `.card-header`, `.toggle-label`, `.toggle-hint`) that the new components use.

## 2. Things Claude Code needs to do

Tell Claude Code:

> "I redesigned the dashboard. I've replaced `webapp/src/index.css` and `webapp/src/App.jsx` with new versions. Please do the following:

**(a) Create `webapp/src/pages/Benchmark.jsx`** — a new page for the QuixBugs benchmark. It should POST to whatever `/api/runs/` endpoint kicks off a benchmark run (pass a `mode: 'quixbugs'` or whatever your API expects). The page has:
- Phase picker (`measure` / `populate`) rendered as two clickable cards
- Inputs: populate count (number), seed (number)
- LLM settings block: Provider select (deepseek/anthropic/openai/ollama, default deepseek), Preset select, Model Override text, API Key password
- One toggle: Use RAG memory
- Submit button "Start Benchmark"

See `GGPT Dashboard v2.html` in the project root — the `BenchmarkPage` component in the inline script is the reference implementation; copy the markup/styles directly.

**(b) Update `webapp/src/pages/RunsList.jsx`**:
- Move the "New Run" form from the separate `/runs/new` route to the bottom of the list page (combined flow)
- Delete all `placeholder=""` attributes from form inputs
- Default provider should be `deepseek` (first in the list)
- Add columns: `Tests` (shows `passed / failed`) and `Outcome` (shows `S` chip + `F→P n` for benchmark runs, `—` otherwise)
- Tag benchmark runs with an amber `<span className="chip chip-bench">BENCH</span>` in the Mode column
- Wrap the table in `<div className="card" style={{ padding: 0, overflowX: 'auto' }}>` with `<table style={{ minWidth: 1040 }}>` so it scrolls on narrow viewports instead of overflowing

**(c) Update `webapp/src/pages/NewRun.jsx`** — if you keep it as a standalone route for deep-linking, just delete all `placeholder=""` attributes and switch default provider to `deepseek`. Otherwise delete the file and the `/runs/new` route (form is now inline on RunsList).

**(d) Update `webapp/src/pages/RunDetail.jsx`**:
- Show an amber `BENCH` chip next to the title when the run is a benchmark run
- For benchmark runs, add a new `<OracleMatrix>` card above the Functions list, rendering the 2×2 SWT-bench transitions (rows = buggy outcome Fail/Pass, columns = golden outcome Pass/Fail, cells = F→P, F→F, P→F, P→P). Reference markup is in `GGPT Dashboard v2.html` → `OracleMatrix` component. Uses the `.oracle-grid` / `.oracle-cell` / `.matrix-legend` classes already in the CSS.
- Drop the pending "Applicable (W)" metric — we no longer generate patches.

**(e) Update `webapp/src/pages/Analytics.jsx`**:
- Rebuild as a **two-column side-by-side layout**: Benchmark on the left (wider), User runs on the right. Use `display: grid; gridTemplateColumns: '1.2fr 1fr'; gap: 24px`.
- Benchmark column: overall stat strip (Runs / Resolved / Detected — **no Applicable**), Baseline-vs-RAG resolution rate bar chart, breakdown tables by project and by provider
- User column: summary stats + recent user runs table
- Reference: `BenchSummary` and `UserSummary` in the same HTML file.

Use the existing design tokens (CSS variables) — don't invent new colors. Replace any remaining inline hex codes like `#64748b`, `#6ee7b7`, `#fca5a5` with `var(--text-3)`, `var(--green-fg)`, `var(--red-fg)` for consistency."

## 3. Mock data reference

`GGPT Dashboard v2.html` has mock-data shapes in `MOCK_RUNS`, `MOCK_RUN_DETAIL`, and `MOCK_ANALYTICS`. Use these as the expected JSON contract for the API endpoints. If the backend response differs, adjust the component to match the real shape — don't change the frontend just to avoid touching the API.

## 4. Checklist for after the swap

- [ ] `npm run dev` — page renders with the new dark/Inter/JetBrains look
- [ ] Runs table has horizontal scroll on narrow viewports, no overflow
- [ ] No placeholder text in any form input
- [ ] Provider dropdown defaults to `deepseek`
- [ ] Clicking a benchmark run shows the 2×2 oracle matrix on the detail page
- [ ] Analytics shows bench + user columns side-by-side
- [ ] "Applicable (W)" stat is gone everywhere
