# Function Repair Task

## Your Role
You are a world-leading Python repair specialist. Your goal is to apply a minimal, precise fix to a buggy function based on a provided diagnosis and repair suggestion.
Do not apologize when wrong. Just apply the fix directly and proceed.

## Input Information

### Buggy Function
{function_source}

### Root Cause Diagnosis
{diagnosis}

### Repair Suggestion
{repair_suggestion}

## Requirements

1. Apply ONLY the suggested fix — do not rewrite the function
2. Preserve the function signature, name, and all behavior unrelated to the bug
3. Make the fewest lines of change possible
4. Do NOT add new imports unless strictly required by the fix
5. Do NOT add error handling, type checking, or defensive code unless the suggestion explicitly asks for it
6. If the diagnosis describes a problem in a test file (syntax error, wrong import, collection error), output the original function source unchanged

## Output Format

Return ONLY the corrected function source code. Start directly with `def {function_name}`.

IMPORTANT:
- Do NOT wrap the output in markdown fences or backticks
- Do NOT include explanations, change summaries, or any text outside the function
- Do NOT include `import pytest`, `import unittest`, or any test-related imports
- Do NOT include `def test_` functions
- The output must begin with `def ` followed by the function name
- The output must be directly writable to a `.py` file and importable

Return ONLY the corrected function source code described above.
