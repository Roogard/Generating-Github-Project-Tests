import os
from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

PROMPTS_DIR = Path(__file__).parent / "prompts"

TEST_TYPES = ["statement", "block", "condition", "path", "bva", "ecp", "mutation"]


class AgentState(TypedDict):
    function_info: dict
    statement_tests: str
    block_tests: str
    condition_tests: str
    path_tests: str
    bva_tests: str
    ecp_tests: str
    mutation_tests: str


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
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    return response.content


def make_node(test_type):
    def node(state):
        return {f"{test_type}_tests": call_agent(test_type, state["function_info"])}
    return node


def build_graph(selected_agents=None):
    builder = StateGraph(AgentState)

    for tt in (selected_agents or TEST_TYPES):
        builder.add_node(tt, make_node(tt))
        builder.add_edge(START, tt)
        builder.add_edge(tt, END)

    return builder.compile()
