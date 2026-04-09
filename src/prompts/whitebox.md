# Whitebox Test Generation Task

## Your Role
You are a world-leading software testing engineer. Your goal is to generate a single pytest file that achieves maximum structural coverage of the given function.
Do not apologize when uncertain. Derive expected outputs from the function's specification, not by tracing. Proceed directly.

## Input Information

### Function Under Test
{function_source}

### File Path
{file_path}

### Imports Available
{imports}

## Requirements

1. Cover all four whitebox techniques in a single file — statement, block, condition, and path coverage
2. For EVERY test, apply the Two-Phase Rule:
   - Phase 1 (inputs): use code structure to pick inputs that hit the target branch/path
   - Phase 2 (expected output): derive the correct output from the function's name and universal algorithm definition, Python builtins as oracles, or mathematical invariants — NEVER by tracing the code
3. If the correct expected value cannot be determined without tracing, use property assertions only (e.g., `assert len(result) == len(input)`, `assert sorted(result) == sorted(input)`)
4. Group tests by technique with section comments: `# --- Statement Coverage ---`, `# --- Block Coverage ---`, `# --- Condition Coverage ---`, `# --- Path Coverage ---`
5. For condition coverage, comment each test with the truth values of sub-expressions (e.g., `# x>0: True, y<10: False`)
6. For path coverage, comment each test with the path it exercises (e.g., `# path: if-true → loop-2-iters → return`)
7. For loops, cover: zero iterations, one iteration, multiple iterations
8. Mock only external dependencies (network, slow I/O, third-party services, filesystem writes outside repo). Do NOT mock stdlib internals, the function's own helpers, or real data structures
9. Assert what a CORRECT implementation should do — never what the current code does

## Output Format

Return ONLY a complete, runnable pytest file. Start the file directly with the import statements.

IMPORTANT:
- Do NOT wrap the output in markdown fences or backticks
- Do NOT include explanations, comments about your approach, or any prose outside the test code
- Do NOT assert what the current code returns — assert what a correct implementation must return
- Do NOT mock the core logic under test
- The file must be directly writable to disk and executable with `pytest`
- If a section adds no new coverage over prior sections, omit it with a one-line comment

Return ONLY the Python test code described above.
