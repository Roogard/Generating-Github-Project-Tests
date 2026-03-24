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


def get_supervisor_llm(config):
    sup = config["supervisor"]
    if sup["provider"]:
        effective = {
            "provider": sup["provider"],
            "model": sup["model"],
            "base_url": sup["base_url"],
            "api_key_env": sup["api_key_env"],
        }
    else:
        effective = dict(config["llm"])
    from src.config import _apply_provider_defaults
    effective_config = {"llm": effective}
    _apply_provider_defaults(effective_config)
    llm = get_llm(effective_config)
    return llm


def build_user_message(fn):
    msg = f"## Function: `{fn['name']}`\n"
    msg += f"**Language:** {fn['language']}\n"
    msg += f"**File:** `{fn['file_path']}`\n"

    if fn.get("imports"):
        msg += f"\n### Imports\n```\n{fn['imports']}\n```\n"

    msg += f"\n### Function source\n```{fn['language']}\n{fn['source']}\n```\n"
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
