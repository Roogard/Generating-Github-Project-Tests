import os
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage

PROMPTS_DIR = Path(__file__).parent / "prompts"


def get_llm(config):
    provider = config["llm"]["provider"]
    model = config["llm"]["model"]
    base_url = config["llm"]["base_url"]
    api_key_env = config["llm"]["api_key_env"]
    api_key = os.environ.get(api_key_env, "") if api_key_env else ""

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=api_key)

    from langchain_openai import ChatOpenAI
    kwargs = {"model": model}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)



def build_user_message(fn):
    msg = f"## Function: `{fn['name']}`\n"
    msg += f"**Language:** {fn['language']}\n"
    msg += f"**File:** `{fn['file_path']}`\n"

    if fn.get("imports"):
        msg += f"\n### Imports\n```\n{fn['imports']}\n```\n"

    msg += f"\n### Function source\n```{fn['language']}\n{fn['source']}\n```\n"
    import_path = fn["file_path"].replace("\\", "/").replace("/", ".").replace(".py", "")
    msg += f"\n**Import path (use exactly):** `from {import_path} import {fn['name']}`\n"
    msg += "\nGenerate tests now. Return only the test code."
    return msg


def call_agent(prompt_name, fn, config):
    system = (PROMPTS_DIR / f"{prompt_name}.md").read_text(encoding="utf-8")
    user = build_user_message(fn)
    llm = get_llm(config)
    try:
        response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return response.content
    except Exception as e:
        print(f"  [agent:{prompt_name}] error: {e}")
        return ""


def call_agent_with_context(prompt_name, fn, extra_context, config):
    system = (PROMPTS_DIR / f"{prompt_name}.md").read_text(encoding="utf-8")
    user = build_user_message(fn) + "\n\n" + extra_context
    llm = get_llm(config)
    try:
        response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return response.content
    except Exception as e:
        print(f"  [agent:{prompt_name}] error: {e}")
        return ""


def strip_code_fences(code):
    if not code:
        return code
    lines = code.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def _truncate_error(text, max_lines=30):
    if not text:
        return ""
    lines = text.strip().splitlines()
    if len(lines) <= max_lines:
        return text.strip()
    # keep first 10 and last 20 lines (the tail usually has the actual error)
    return "\n".join(lines[:10] + ["  ...truncated..."] + lines[-20:])


def _extract_error_summary(failure):
    if failure["kind"] == "failure":
        detail = failure.get("longrepr", "")
    else:
        detail = failure.get("longrepr") or failure.get("stderr") or failure.get("stdout", "")
    return _truncate_error(detail)


_MAX_FAILURES_IN_CONTEXT = 10


def _build_diagnosis_context(fn, failures_for_fn, previous_attempts=None):
    parts = []

    # cap failures to avoid LLM context overflow on functions with many failures
    shown = failures_for_fn[:_MAX_FAILURES_IN_CONTEXT]
    if len(failures_for_fn) > _MAX_FAILURES_IN_CONTEXT:
        parts.append(f"_(showing {_MAX_FAILURES_IN_CONTEXT} of {len(failures_for_fn)} failures)_\n")

    # trigger tests — full source of each failing test file (from capped set)
    test_sources = {}
    for failure in shown:
        path = failure.get("test_file_path", "")
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

    # error messages — cleaned and truncated
    parts.append("## Error Message(s)\n")
    for failure in shown:
        label = failure["kind"].upper()
        parts.append(f"### [{label}] {failure['test_name']} (type: {failure['test_type']})")
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

    # previous failed attempts — include diagnosis + code so the LLM avoids repeats
    if previous_attempts:
        parts.append("## Previous Fix Attempts (all failed — do NOT repeat)\n")
        for i, attempt in enumerate(previous_attempts):
            parts.append(f"### Attempt {i + 1}")
            if attempt.get("diagnosis"):
                parts.append(f"Diagnosis: {attempt['diagnosis'][:500]}")
            parts.append(f"```python\n{attempt['fixed_code']}\n```")
            parts.append(f"Remaining failures: {len(attempt['remaining_failures'])}")
            for f in attempt["remaining_failures"]:
                parts.append(f"- [{f['kind'].upper()}] {f['test_name']}: {f.get('assertion') or _extract_error_summary(f)[:200]}")
            parts.append("")
        parts.append("Try a DIFFERENT approach from the attempts above.\n")

    return "\n".join(parts)


def call_diagnose_agent(fn, failures_for_fn, config, previous_attempts=None):
    context = _build_diagnosis_context(fn, failures_for_fn, previous_attempts)
    system = (PROMPTS_DIR / "fix_diagnose.md").read_text(encoding="utf-8")
    user = build_user_message(fn) + "\n\n" + context
    llm = get_llm(config)
    try:
        response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return response.content
    except Exception as e:
        print(f"  [agent:fix_diagnose] error: {e}")
        return ""


def call_fix_agent(fn, failures_for_fn, config, previous_attempts=None):
    # Stage 1: diagnose root cause
    diagnosis_context = _build_diagnosis_context(fn, failures_for_fn, previous_attempts)
    diagnosis = call_diagnose_agent(fn, failures_for_fn, config, previous_attempts)
    if not diagnosis or not diagnosis.strip():
        return _FixResult("", "", diagnosis_context, "")

    # Stage 2: generate patch from diagnosis
    parts = []
    parts.append("## Root Cause Diagnosis\n")
    parts.append(diagnosis)
    parts.append("")

    # include the trigger tests so the fix agent can see what must pass
    test_sources = {}
    for failure in failures_for_fn:
        path = failure.get("test_file_path", "")
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
    fixed = call_agent_with_context("fix_function", fn, fix_context, config)

    return _FixResult(fixed or "", diagnosis, diagnosis_context, fix_context)


class _FixResult(str):
    """str subclass that carries artifacts alongside the fixed code."""
    def __new__(cls, code, diagnosis="", diagnosis_context="", fix_context=""):
        obj = str.__new__(cls, code)
        obj.diagnosis = diagnosis
        obj.diagnosis_context = diagnosis_context
        obj.fix_context = fix_context
        return obj
