"""Agentic test-generation environment.

TestGenEnv holds per-function state (repo, target function, test file, history).
run_agent drives a tool-calling LLM against it until the agent terminates or
max_turns is hit.
"""
from src.agent.env import TestGenEnv
from src.agent.loop import run_agent

__all__ = ["TestGenEnv", "run_agent"]
