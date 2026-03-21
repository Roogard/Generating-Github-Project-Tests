import os
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

PROMPTS_DIR = Path(__file__).parent / "prompts"


def get_llm():
    model = os.environ.get("LLM_MODEL", "deepseek-chat")
    return ChatOpenAI(
        model=model,
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )


def build_user_message(fn):
    msg = f"## Function: `{fn['name']}`\n"
    msg += f"**Language:** {fn['language']}\n"
    msg += f"**File:** `{fn['file_path']}`\n"

    if fn.get("imports"):
        msg += f"\n### Imports\n```\n{fn['imports']}\n```\n"

    msg += f"\n### Function source\n```{fn['language']}\n{fn['source']}\n```\n"
    msg += "\nGenerate tests now. Return only the test code."
    return msg


def call_agent(prompt_name, fn):
    system = (PROMPTS_DIR / f"{prompt_name}.md").read_text(encoding="utf-8")
    user = build_user_message(fn)
    llm = get_llm()
    try:
        response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return response.content
    except Exception as e:
        print(f"  [agent:{prompt_name}] error: {e}")
        return ""


def call_agent_with_context(prompt_name, fn, extra_context):
    system = (PROMPTS_DIR / f"{prompt_name}.md").read_text(encoding="utf-8")
    user = build_user_message(fn) + "\n\n" + extra_context
    llm = get_llm()
    try:
        response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return response.content
    except Exception as e:
        print(f"  [agent:{prompt_name}] error: {e}")
        return ""
