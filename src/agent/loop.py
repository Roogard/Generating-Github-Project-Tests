"""run_agent — hand-rolled tool-calling loop.

The agent gets a system prompt + an initial observation (function source +
import path). It responds with either tool calls or a final text message.
We dispatch each tool call through env.step, append ToolMessages, and loop
until the agent calls finish, stops emitting tool calls, or hits max_turns.
"""
from __future__ import annotations

from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from src.agent.env import TestGenEnv
from src.agent.tools import make_tools
from src.llm import get_llm


_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.md"
_SYSTEM_PROMPT: str | None = None


def _load_system_prompt() -> str:
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        _SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")
    return _SYSTEM_PROMPT


def run_agent(env: TestGenEnv, cfg: dict, verbose: bool = True) -> dict:
    """Drive the agent until it finishes or max_turns is hit. Returns env.summary()."""
    tools = make_tools(env)
    tool_by_name = {t.name: t for t in tools}
    llm = get_llm(cfg).bind_tools(tools)

    messages = [
        SystemMessage(content=_load_system_prompt()),
        HumanMessage(content=env.reset()),
    ]

    silent_turns = 0
    while not env.is_done():
        try:
            resp = llm.invoke(messages)
        except Exception as e:
            print(f"  [agent] LLM error: {type(e).__name__}: {e}")
            break
        messages.append(resp)

        tool_calls = getattr(resp, "tool_calls", None) or []
        if not tool_calls:
            silent_turns += 1
            if verbose:
                print(f"  [agent] turn {env.turn + 1}: no tool call (silent turn {silent_turns})")
            if silent_turns >= 2:
                break
            # nudge once with a user message
            messages.append(HumanMessage(content="You did not call a tool. Either call write_test_file / run_tests / etc., or call finish(reason) to end."))
            continue
        silent_turns = 0

        for call in tool_calls:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            args = call.get("args") if isinstance(call, dict) else getattr(call, "args", {}) or {}
            call_id = call.get("id") if isinstance(call, dict) else getattr(call, "id", "") or ""
            if verbose:
                preview = str(args)[:120]
                print(f"  [agent] turn {env.turn + 1}: {name}({preview})")

            tool_fn = tool_by_name.get(name)
            if tool_fn is None:
                observation = env.step(name or "<unknown>", args)
            else:
                observation = tool_fn.invoke(args or {})
            messages.append(ToolMessage(content=observation, tool_call_id=call_id))
            if env.is_done():
                break

    if verbose:
        print(f"  [agent] done. turns={env.turn} finish={env.finish_reason!r}")
    return env.summary()
