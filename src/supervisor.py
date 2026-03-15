"""
Supervisor agent.

Uses the LLM to analyze a function and pick 2-4 of the 7 test agents whose
strengths best match that function's characteristics (e.g. lots of branches →
condition/path; numeric inputs → bva; complex logic → mutation).

In test mode, the supervisor also receives memory context: a few similar past
functions with their agent kill-rate scores, plus high-level reflexion summaries.
This lets the supervisor improve its selections over time without retraining.

select_agents(fn, memory_context=None) — returns a list of 2-4 agent names.
"""
import json
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage

from src.agents import get_llm, build_user_message, TEST_TYPES

PROMPTS_DIR = Path(__file__).parent / "prompts"


def select_agents(fn, memory_context=None):
    system = (PROMPTS_DIR / "supervisor.md").read_text(encoding="utf-8")
    if memory_context:
        system = system + "\n\n" + memory_context

    msg = build_user_message(fn)
    msg = msg.replace(
        "Generate tests now. Return only the test code.",
        "Analyze this function and select the best agents. Return only a JSON array.",
    )

    llm = get_llm()
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=msg)])

    text = response.content.strip()
    # strip markdown fences
    text = text.replace("```json", "").replace("```", "").strip()

    selected = None

    # try parsing the whole response
    try:
        selected = json.loads(text)
    except json.JSONDecodeError:
        pass

    # fallback: find [...] in the text
    if selected is None:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                selected = json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

    if selected and isinstance(selected, list):
        valid = [a for a in selected if a in TEST_TYPES]
        if 2 <= len(valid) <= 4:
            return valid
        if len(valid) > 4:
            return valid[:4]
        if len(valid) == 1:
            return valid + [a for a in TEST_TYPES if a not in valid][:1]

    print("  Warning: supervisor could not parse response, using all agents")
    return list(TEST_TYPES)
