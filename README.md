uvicorn api.app:app --reload

# GitHub Project Test Generator

An agentic pipeline that clones a GitHub repo, extracts Python functions, generates unit tests using an LLM, runs them, and attempts to automatically fix any bugs it finds. Evaluated on BugsInPy with Claude Sonnet: **68% bug detection rate, 100% fix rate** on detected bugs. The main challenge was that the LLM sometimes wrote tests around the buggy behavior — tests that passed on broken code but failed once the fix was applied — requiring an oracle revision step after each fix.

---

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and fill in your API key
cp .env.example .env

# Run on any public GitHub repo
uv run python main.py

# Or point it at a specific repo by editing REPOS in main.py
```

Configure what to run by editing the settings block at the top of [main.py](main.py):

```python
REPOS = ["https://github.com/user/repo"]   # regular repos
BUGSINPY_PROJECTS = ["black", "tqdm"]       # BugsInPy benchmark projects
```

Set your LLM provider and key in `.env`:

```
ANTHROPIC_API_KEY=...
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
```

---

## Results

Evaluated on 20 bugs across 4 BugsInPy projects (black, tqdm, cookiecutter, tornado):

| Metric | Result |
|---|---|
| Bug detection rate | **68%** |
| Fix rate (on detected bugs) | **100%** |

"Detected" means the generated tests caught at least one failure on the buggy function. "Fixed" means the LLM's patch made all failures converge — including revising any test oracles that were written for the broken behavior.
