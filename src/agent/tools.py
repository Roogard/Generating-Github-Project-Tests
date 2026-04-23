"""LangChain tool bindings for a TestGenEnv instance.

Each tool is a thin wrapper that delegates to env.step(name, args). Using
LangChain's @tool decorator gives us Pydantic-validated argument schemas and
the provider-agnostic `bind_tools()` surface.
"""
from __future__ import annotations

from langchain_core.tools import tool

from src.agent.env import TestGenEnv


def make_tools(env: TestGenEnv) -> list:
    """Return the list of tools for the given env. Omits oracle-stability outside benchmark mode."""

    @tool
    def view_function() -> str:
        """Show the target function source with line numbers and any internal helpers."""
        return env.step("view_function", {})

    @tool
    def view_coverage() -> str:
        """Run your current test file under coverage and return percent + uncovered lines of the target function."""
        return env.step("view_coverage", {})

    @tool
    def run_tests() -> str:
        """Run pytest on your current test file and return a compact pass/fail summary with tracebacks."""
        return env.step("run_tests", {})

    @tool
    def check_oracle_stability() -> str:
        """Benchmark mode only. Run your tests against both the buggy and the reference versions and label each test as F->P (detection), F->F (spurious), P->P (neutral), or P->F (regression). Call this before finish() to catch spurious tests."""
        return env.step("check_oracle_stability", {})

    @tool
    def search_similar_tests(query: str, k: int = 3) -> str:
        """Search the long-term memory for tests written for similar functions. Use a natural-language query like 'raise ValueError on empty input' or paste a function signature."""
        return env.step("search_similar_tests", {"query": query, "k": k})

    @tool
    def view_golden_example(name: str = "") -> str:
        """Read a curated exemplar test file. Call with no args to list available example names, then call again with a specific name."""
        return env.step("view_golden_example", {"name": name})

    @tool
    def write_test_file(code: str) -> str:
        """Overwrite your test file with the given pytest code. Pass the complete runnable file starting with imports — no markdown fences."""
        return env.step("write_test_file", {"code": code})

    @tool
    def finish(reason: str = "") -> str:
        """End the session. Call this when your tests are adequate and (in benchmark mode) check_oracle_stability showed no F->F or P->F."""
        return env.step("finish", {"reason": reason})

    tools = [
        view_function,
        view_coverage,
        run_tests,
        search_similar_tests,
        view_golden_example,
        write_test_file,
        finish,
    ]
    if env.benchmark_context:
        tools.insert(3, check_oracle_stability)  # put next to run_tests for discoverability
    return tools
