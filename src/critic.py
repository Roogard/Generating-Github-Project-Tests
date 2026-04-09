import re
import os
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage

PROMPTS_DIR = Path(__file__).parent / "prompts"


def call_critic_agent(fn, test_code, coverage_info, config):
    """LLM critic: evaluate existing tests against coverage data and return improved versions.

    Args:
        fn:            function dict from extractor
        test_code:     {"whitebox": str, "blackbox": str}
        coverage_info: CoverageInfo dict from coverage.measure_coverage
        config:        pipeline config dict

    Returns:
        {
            "critique":      str,
            "improved_code": {"whitebox": str, "blackbox": str},
            "error":         str | None,
        }
    """
    from src.agents import get_llm

    system = (PROMPTS_DIR / "critic.md").read_text(encoding="utf-8")
    user = _build_critic_user_message(fn, test_code, coverage_info)
    llm = get_llm(config)
    try:
        response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        critique, improved = _parse_critic_response(response.content)
        return {"critique": critique, "improved_code": improved, "error": None}
    except Exception as e:
        print(f"  [critic] error: {e}")
        return {"critique": "", "improved_code": {}, "error": str(e)}


def _build_critic_user_message(fn, test_code, coverage_info):
    parts = []

    # Function source with line numbers
    parts.append("## Function Under Test\n")
    source_lines = fn["source"].splitlines()
    start = fn.get("start_line", 1)
    numbered = "\n".join(f"{start + i:4d} | {line}" for i, line in enumerate(source_lines))
    parts.append(f"**File:** `{fn['file_path']}`\n")
    parts.append(f"```python\n{numbered}\n```\n")

    # Current test files
    parts.append("## Current Whitebox Tests\n")
    parts.append(f"```python\n{test_code.get('whitebox', '# (empty)')}\n```\n")
    parts.append("## Current Blackbox Tests\n")
    parts.append(f"```python\n{test_code.get('blackbox', '# (empty)')}\n```\n")

    # Coverage report
    pct = coverage_info.get("coverage_pct", 0.0)
    uncovered = coverage_info.get("uncovered_lines", [])
    source_lines_map = coverage_info.get("fn_source_lines", {})

    parts.append(f"## Coverage Report — {pct:.1f}% covered\n")
    if uncovered:
        parts.append("### Uncovered Lines\n")
        parts.append("| Line | Source |")
        parts.append("|------|--------|")
        for lineno in sorted(uncovered):
            src = source_lines_map.get(lineno, "").rstrip()
            parts.append(f"| {lineno} | `{src}` |")
        parts.append("")
    else:
        parts.append("All lines in the function were covered.\n")

    parts.append("Improve the tests to cover the uncovered lines. Return both files.")
    return "\n".join(parts)


def _parse_critic_response(raw):
    """Parse the structured LLM response into critique text and improved test code.

    Returns:
        (critique_text: str, {"whitebox": str, "blackbox": str})
    """
    critique = ""
    improved = {"whitebox": "", "blackbox": ""}

    if not raw:
        return critique, improved

    # Extract critique section (between "## Critique" and the next "##")
    m = re.search(r'##\s*Critique\s*\n(.*?)(?=##|\Z)', raw, re.DOTALL | re.IGNORECASE)
    if m:
        critique = m.group(1).strip()

    # Extract each code block that follows its section header
    whitebox_match = re.search(
        r'##\s*Improved Whitebox Tests.*?```(?:python)?\n(.*?)```',
        raw, re.DOTALL | re.IGNORECASE
    )
    blackbox_match = re.search(
        r'##\s*Improved Blackbox Tests.*?```(?:python)?\n(.*?)```',
        raw, re.DOTALL | re.IGNORECASE
    )

    if whitebox_match:
        improved["whitebox"] = whitebox_match.group(1).strip()
    if blackbox_match:
        improved["blackbox"] = blackbox_match.group(1).strip()

    return critique, improved
