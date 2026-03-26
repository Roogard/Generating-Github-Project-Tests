import os
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

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


def call_fix_agent(fn, failures_for_fn, config, previous_attempts=None):
    parts = []

    # include the source of each unique failing test file so the LLM can see
    # exactly what is being imported and asserted
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
        parts.append("## Failing Test Files\n")
        for path, src in test_sources.items():
            parts.append(f"```python\n# {os.path.basename(path)}\n{src}\n```\n")

    if previous_attempts:
        parts.append("## Previous Fix Attempts\n")
        for i, attempt in enumerate(previous_attempts):
            parts.append(f"### Attempt {i + 1}")
            parts.append(f"```python\n{attempt['fixed_code']}\n```\n")
            parts.append(f"### Remaining failures after attempt {i + 1}")
            for f in attempt["remaining_failures"]:
                parts.append(f"- [{f['kind'].upper()}] {f['test_name']}: {f['assertion']}")
            parts.append("")
        parts.append("Do NOT repeat these fixes. They did not work. Try a different approach.\n")

    parts.append("## Current Test Failures\n")
    for failure in failures_for_fn:
        parts.append(f"### [{failure['kind'].upper()}] {failure['test_name']} (type: {failure['test_type']})")
        parts.append(f"- Assertion: {failure['assertion']}")
        parts.append(f"- Expected:  {failure['expected']}")
        parts.append(f"- Actual:    {failure['actual']}")
        parts.append(f"- Location:  {failure['file']}:{failure['line']}")
        if failure["kind"] == "failure":
            detail = failure["longrepr"]
        else:
            detail = failure.get("longrepr") or failure.get("stderr") or failure.get("stdout", "")
        parts.append(f"- Detail:\n{detail}\n")

    extra_context = "\n".join(parts)
    return call_agent_with_context("fix_function", fn, extra_context, config)
