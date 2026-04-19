"""LLM calls: config and test generation."""
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage

PROMPTS_DIR = Path(__file__).parent / "prompts"

_PROVIDERS = {
    "deepseek":  {"base_url": "https://api.deepseek.com",       "api_key_env": "DEEPSEEK_API_KEY"},
    "openai":    {"base_url": "https://api.openai.com/v1",       "api_key_env": "OPENAI_API_KEY"},
    "anthropic": {"base_url": "",                                 "api_key_env": "ANTHROPIC_API_KEY"},
    "ollama":    {"base_url": "http://localhost:11434/v1",        "api_key_env": ""},
}
_DEFAULT_MODELS = {
    "deepseek": "deepseek-chat", "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-6", "ollama": "llama3.2",
}
_PROMPT_CACHE: dict[str, str] = {}


def _load_prompt(name: str) -> str:
    if name not in _PROMPT_CACHE:
        _PROMPT_CACHE[name] = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    return _PROMPT_CACHE[name]


def build_config(provider: str, model: str | None = None, api_key: str | None = None) -> dict:
    p = _PROVIDERS.get(provider, _PROVIDERS["deepseek"])
    return {
        "provider": provider,
        "model": model or _DEFAULT_MODELS.get(provider, "deepseek-chat"),
        "base_url": os.environ.get("LLM_BASE_URL", p["base_url"]),
        "api_key": api_key or (os.environ.get(p["api_key_env"], "") if p["api_key_env"] else ""),
    }


_LLM_TIMEOUT = 120  # seconds — prevents LLM API calls from hanging indefinitely


def get_llm(cfg: dict):
    if cfg["provider"] == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=cfg["model"], api_key=cfg["api_key"], timeout=_LLM_TIMEOUT)
    from langchain_openai import ChatOpenAI
    kwargs: dict = {"model": cfg["model"], "timeout": _LLM_TIMEOUT}
    if cfg["api_key"]:
        kwargs["api_key"] = cfg["api_key"]
    if cfg["base_url"]:
        kwargs["base_url"] = cfg["base_url"]
    return ChatOpenAI(**kwargs)


def build_user_message(fns: list[dict]) -> str:
    """Format a list of functions (+ shared spec) into a single LLM user message."""
    spec = fns[0].get("spec", "") if fns else ""
    msg = ""
    if spec:
        msg += f"### Specification\n{spec}\n\n"
    for fn in fns:
        msg += f"## Function: `{fn['name']}`\n**Language:** {fn['language']}\n**File:** `{fn['file_path']}`\n"
        if fn.get("description"):
            msg += f"\n### Description\n{fn['description']}\n"
        if fn.get("imports"):
            msg += f"\n### Imports\n```\n{fn['imports']}\n```\n"
        if fn.get("callees"):
            msg += "\n### Internal helpers (read-only context — do not test these directly)\n"
            for callee in fn["callees"]:
                msg += f"```python\n{callee['source']}\n```\n"
        if fn.get("test_examples"):
            msg += "\n### Example usages from repo test suite (use these call patterns exactly)\n"
            for example in fn["test_examples"]:
                msg += f"```python\n{example}\n```\n"
        msg += f"\n### Function source\n```{fn['language']}\n{fn['source']}\n```\n"
        if fn.get("uncovered_hint"):
            msg += f"\n### Uncovered lines — add tests targeting these (coverage < 80%)\n{fn['uncovered_hint']}\n"
        import_path = fn["file_path"].replace("\\", "/").replace("/", ".").replace(".py", "")
        if fn.get("class_name"):
            msg += f"\n**Import path:** `from {import_path} import {fn['class_name']}`\n"
            msg += f"**Note:** `{fn['name']}` is a method on `{fn['class_name']}`.\n"
        else:
            msg += f"\n**Import path (use exactly):** `from {import_path} import {fn['name']}`\n"
        msg += "\n"
    msg += "Generate tests now. Return only the test code."
    return msg


def _extract_code(text: str) -> str:
    if not text:
        return text
    m = re.search(r'```(?:python)?\n(.*?)```', text.strip(), re.DOTALL)
    if m:
        return m.group(1).strip()
    starters = ("import ", "from ", "def ", "class ", "async def ", "@", "#", "pytest")
    lines = text.strip().splitlines()
    for i, line in enumerate(lines):
        if line.strip() and any(line.strip().startswith(p) for p in starters):
            return "\n".join(lines[i:]).strip()
    return text.strip()


def _strip_relative_imports(code: str) -> str:
    return "\n".join(
        line for line in code.splitlines()
        if not re.match(r'^\s*(from\s+\.|\bimport\s+\.)', line)
    )


def _build_rag_prefix(examples: list[dict]) -> str:
    if not examples:
        return ""
    lines = ["## Similar functions from past runs — use as style and structure references\n"]
    for i, ex in enumerate(examples, 1):
        cov = f" (coverage {ex['coverage_pct']:.0f}%)" if ex.get("coverage_pct") is not None else ""
        lines.append(f"### Example {i}: `{ex['fn_name']}`{cov}")
        lines.append(f"```python\n{ex['fn_source']}\n```")
        lines.append(f"Generated tests:\n```python\n{ex['test_code']}\n```\n")
    return "\n".join(lines) + "\n---\n\n"


def _call_agent(prompt_name: str, fns: list[dict], cfg: dict, examples: list[dict] = ()) -> str:
    llm = get_llm(cfg)
    user_msg = build_user_message(fns)
    if examples:
        user_msg = _build_rag_prefix(list(examples)) + user_msg
    try:
        resp = llm.invoke([SystemMessage(content=_load_prompt(prompt_name)), HumanMessage(content=user_msg)])
        return _strip_relative_imports(_extract_code(resp.content))
    except Exception as e:
        print(f"  [{prompt_name}] error: {e}")
        return ""


_REPAIR_SYSTEM = """\
You are fixing structurally broken tests. The listed tests fail due to errors in the test code itself — wrong imports, wrong attribute access, wrong data structure assumptions (KeyError, AttributeError, NameError, ImportError). These are bugs in the tests, not bugs in the code under test.

Rules:
- Fix ONLY the structural error for each listed test: wrong import path, wrong key/attribute access, wrong argument type, undefined variable, or wrong data structure assumption.
- Do NOT change, weaken, or remove any assertion that is a clean AssertionError — those may be genuine bug detections.
- Do NOT add new test functions.
- If a test accesses a key that does not exist (KeyError), look at the function's return type and fix the access pattern.
- If a test uses a wrong attribute (AttributeError), fix it to use the correct API.
- Return the full, corrected test file. Return only the test code, no markdown fences.
"""


def repair_tests(test_code: str, error_failures: list[dict], fns: list[dict], cfg: dict) -> str:
    """Ask the LLM to fix tests that errored during collection/execution on the buggy code.

    error_failures: list of {name, longrepr} for tests with setup/import errors.
    Returns the corrected test file, or the original code if the call fails.
    """
    if not error_failures or not test_code.strip():
        return test_code

    failure_block = "\n".join(
        f"### {f['name']}\n{f.get('longrepr', '(no traceback)')}"
        for f in error_failures
    )
    fn_context = build_user_message(fns)
    user_msg = (
        f"The following tests raised errors. Fix only their setup issues.\n\n"
        f"## Broken tests\n{failure_block}\n\n"
        f"## Function context\n{fn_context}\n\n"
        f"## Current test file\n```python\n{test_code}\n```"
    )
    llm = get_llm(cfg)
    try:
        resp = llm.invoke([SystemMessage(content=_REPAIR_SYSTEM), HumanMessage(content=user_msg)])
        repaired = _strip_relative_imports(_extract_code(resp.content))
        return repaired if repaired.strip() else test_code
    except Exception as e:
        print(f"  [repair] error: {e}")
        return test_code


def generate_tests(fns: list[dict], cfg: dict, use_rag: bool = True) -> dict:
    """Generate whitebox + blackbox tests concurrently for all functions. Returns {whitebox, blackbox}."""
    rag_wb: list[dict] = []
    rag_bb: list[dict] = []
    if use_rag and fns and fns[0].get("source"):
        try:
            from src.vectordb import retrieve_examples
            rag_wb = retrieve_examples(fns[0]["source"], "whitebox", n_results=3)
            rag_bb = retrieve_examples(fns[0]["source"], "blackbox", n_results=3)
            if rag_wb or rag_bb:
                print(f"  [rag] retrieved {len(rag_wb)} whitebox + {len(rag_bb)} blackbox examples")
        except Exception:
            pass
    with ThreadPoolExecutor(max_workers=2) as ex:
        wb = ex.submit(_call_agent, "whitebox", fns, cfg, rag_wb)
        bb = ex.submit(_call_agent, "blackbox", fns, cfg, rag_bb)
        whitebox, blackbox = wb.result(), bb.result()
    print(f"  whitebox: {len(whitebox)} chars  blackbox: {len(blackbox)} chars")
    return {"whitebox": whitebox, "blackbox": blackbox}


# ── Fix / oracle agents ───────────────────────────────────────────────────────

def _build_single_fn_message(fn: dict) -> str:
    """Build a user message for a single function (used by fix/oracle agents)."""
    msg = f"## Function: `{fn['name']}`\n"
    msg += f"**Language:** {fn['language']}\n"
    msg += f"**File:** `{fn['file_path']}`\n"
    if fn.get("imports"):
        msg += f"\n### Imports\n```\n{fn['imports']}\n```\n"
    msg += f"\n### Function source\n```{fn['language']}\n{fn['source']}\n```\n"
    import_path = fn["file_path"].replace("\\", "/").replace("/", ".").replace(".py", "")
    if fn.get("class_name"):
        msg += f"\n**Import path (use exactly):** `from {import_path} import {fn['class_name']}`\n"
        msg += f"**Note:** `{fn['name']}` is a method on `{fn['class_name']}`.\n"
    else:
        msg += f"\n**Import path (use exactly):** `from {import_path} import {fn['name']}`\n"
    msg += "\nGenerate tests now. Return only the test code."
    return msg


def _call_agent_with_context(prompt_name: str, fn: dict, extra_context: str, cfg: dict) -> str:
    """Generic LLM call for fix/oracle agents that take a single fn + extra context."""
    system = _load_prompt(prompt_name)
    user = _build_single_fn_message(fn) + "\n\n" + extra_context
    llm = get_llm(cfg)
    try:
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return resp.content
    except Exception as e:
        print(f"  [{prompt_name}] error: {e}")
        return ""


def _truncate_error(text: str, max_lines: int = 30) -> str:
    if not text:
        return ""
    lines = text.strip().splitlines()
    if len(lines) <= max_lines:
        return text.strip()
    return "\n".join(lines[:10] + ["  ...truncated..."] + lines[-20:])


def _extract_error_summary(failure: dict) -> str:
    if failure.get("kind") == "failure":
        detail = failure.get("longrepr", "")
    else:
        detail = failure.get("longrepr") or failure.get("stderr") or failure.get("stdout", "")
    return _truncate_error(detail)


_MAX_FAILURES_IN_CONTEXT = 10


def _build_diagnosis_context(fn: dict, failures: list[dict], previous_attempts: list | None = None) -> str:
    parts = []

    shown = failures[:_MAX_FAILURES_IN_CONTEXT]
    if len(failures) > _MAX_FAILURES_IN_CONTEXT:
        parts.append(f"_(showing {_MAX_FAILURES_IN_CONTEXT} of {len(failures)} failures)_\n")

    # Trigger test sources
    test_sources: dict = {}
    for failure in shown:
        path = failure.get("test_file_path") or failure.get("path", "")
        if path and path not in test_sources:
            try:
                with open(path, encoding="utf-8") as f:
                    test_sources[path] = f.read()
            except OSError:
                pass

    if test_sources:
        parts.append("## Trigger Test(s)\n")
        for path, src in test_sources.items():
            parts.append(f"```python\n# {os.path.basename(path)}\n{src}\n```\n")

    # Error messages
    parts.append("## Error Message(s)\n")
    for failure in shown:
        label = failure.get("kind", "failure").upper()
        parts.append(f"### [{label}] {failure['name']}")
        if failure.get("assertion"):
            parts.append(f"Assertion: {failure['assertion']}")
        if failure.get("expected"):
            parts.append(f"Expected: {failure['expected']}")
        if failure.get("actual"):
            parts.append(f"Actual:   {failure['actual']}")
        summary = _extract_error_summary(failure)
        if summary:
            parts.append(f"```\n{summary}\n```")
        parts.append("")

    # Previous failed attempts
    if previous_attempts:
        parts.append("## Previous Fix Attempts (all failed — do NOT repeat)\n")
        for i, attempt in enumerate(previous_attempts):
            parts.append(f"### Attempt {i + 1}")
            if attempt.get("diagnosis"):
                parts.append(f"Diagnosis: {attempt['diagnosis'][:500]}")
            parts.append(f"```python\n{attempt['fixed_code']}\n```")
            parts.append(f"Remaining failures: {len(attempt.get('remaining_failures', []))}")
            for f in attempt.get("remaining_failures", []):
                parts.append(f"- [{f.get('kind','failure').upper()}] {f['name']}: {f.get('assertion') or _extract_error_summary(f)[:200]}")
            parts.append("")
        parts.append("Try a DIFFERENT approach from the attempts above.\n")

    return "\n".join(parts)


def call_diagnose_agent(fn: dict, failures: list[dict], cfg: dict, previous_attempts: list | None = None) -> str:
    """Stage 1: generate a natural-language root-cause diagnosis (no code)."""
    context = _build_diagnosis_context(fn, failures, previous_attempts)
    system = _load_prompt("fix_diagnose")
    user = _build_single_fn_message(fn) + "\n\n" + context
    llm = get_llm(cfg)
    try:
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return resp.content
    except Exception as e:
        print(f"  [fix_diagnose] error: {e}")
        return ""


def call_fix_agent(fn: dict, failures: list[dict], cfg: dict, previous_attempts: list | None = None) -> dict:
    """2-stage fix: diagnose → patch. Returns {code, diagnosis, diagnosis_context, fix_context}."""
    diagnosis_context = _build_diagnosis_context(fn, failures, previous_attempts)
    diagnosis = call_diagnose_agent(fn, failures, cfg, previous_attempts)
    if not diagnosis or not diagnosis.strip():
        return {"code": "", "diagnosis": "", "diagnosis_context": diagnosis_context, "fix_context": ""}

    # Stage 2: generate patch from diagnosis + trigger tests
    parts = ["## Root Cause Diagnosis\n", diagnosis, ""]

    test_sources: dict = {}
    for failure in failures:
        path = failure.get("test_file_path") or failure.get("path", "")
        if path and path not in test_sources:
            try:
                with open(path, encoding="utf-8") as f:
                    test_sources[path] = f.read()
            except OSError:
                pass
    if test_sources:
        parts.append("## Trigger Test(s)\n")
        for path, src in test_sources.items():
            parts.append(f"```python\n# {os.path.basename(path)}\n{src}\n```\n")

    fix_context = "\n".join(parts)
    fixed = _call_agent_with_context("fix_function", fn, fix_context, cfg)
    return {"code": fixed or "", "diagnosis": diagnosis, "diagnosis_context": diagnosis_context, "fix_context": fix_context}


def call_oracle_revision_agent(fn: dict, test_code: str, failures: list[dict], cfg: dict) -> str:
    """Revise test expected values in a test file after the function has been fixed."""
    parts = ["## Fixed Function\n", f"```python\n{fn['source']}\n```\n",
             "## Test File\n", f"```python\n{test_code}\n```\n",
             "## Failing Tests\n"]
    for f in failures:
        parts.append(f"- {f['name']}")
        if f.get("expected"):
            parts.append(f"  Expected: {f['expected']}")
        if f.get("actual"):
            parts.append(f"  Actual: {f['actual']}")
        summary = _extract_error_summary(f)
        if summary:
            parts.append(f"  ```\n{summary}\n  ```")

    system = _load_prompt("fix_oracle")
    user = "\n".join(parts)
    llm = get_llm(cfg)
    try:
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return resp.content
    except Exception as e:
        print(f"  [fix_oracle] error: {e}")
        return ""
