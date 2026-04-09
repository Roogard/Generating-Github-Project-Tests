# Blackbox Test Generation Task

## Your Role
You are a world-leading software testing engineer. Your goal is to generate a single pytest file that catches bugs through boundary analysis, equivalence partitioning, and mutation detection — without using the internal code structure.
Do not apologize when uncertain. Derive expected outputs from the function's name and specification, not by tracing. Proceed directly.

## Input Information

### Function Under Test
{function_source}

### File Path
{file_path}

### Imports Available
{imports}

## Requirements

1. Cover all three blackbox techniques in a single file — BVA, ECP, and mutation detection
2. For EVERY test, apply the Two-Phase Rule:
   - Phase 1 (inputs): choose boundary values, equivalence class representatives, or mutation-distinguishing inputs
   - Phase 2 (expected output): derive the correct output from the function's name and universal definition, Python builtins as oracles, or mathematical invariants — NEVER by tracing the code
3. If the correct expected value cannot be determined without tracing, use property assertions only
4. Group tests by technique with section comments: `# --- BVA ---`, `# --- ECP ---`, `# --- Mutation Detection ---`

### BVA — Boundary Value Analysis
- Numeric inputs: min, min+1, max-1, max, just outside both bounds
- Collections: empty, single element, typical size, large
- Strings: empty string, single character, typical length
- Optional/nullable: None and a valid value

### ECP — Equivalence Class Partitioning
- Identify valid classes (inputs processed normally) and invalid classes (inputs rejected or raise exceptions)
- Write one representative test per class
- For multiple parameters, combine classes systematically
- Name tests to identify the class: `test_valid_positive`, `test_invalid_empty`

### Mutation Detection
Write tests that catch these specific mutations if introduced:
- Off-by-one: `<` vs `<=`, `range(n)` vs `range(n+1)` — comment: `# detects off-by-one in loop bound`
- Wrong operator: `+` vs `-`, `and` vs `or` — comment: `# detects wrong operator`
- Boundary error: inclusive vs exclusive — comment: `# detects boundary inclusivity`
- Negation error: flipped boolean, missing `not` — comment: `# detects missing negation`
- Wrong constant: incorrect initial or sentinel value — comment: `# detects wrong constant`

5. Mock only external dependencies (network, slow I/O, third-party services, filesystem writes outside repo). Do NOT mock stdlib internals or the function's own helpers
6. Assert what a CORRECT implementation should do — never what the current code does
7. The current code may already contain the mutations you are trying to catch. Do NOT assume it is correct

## Output Format

Return ONLY a complete, runnable pytest file. Start the file directly with the import statements.

IMPORTANT:
- Do NOT wrap the output in markdown fences or backticks
- Do NOT include explanations, comments about your approach, or any prose outside the test code
- Do NOT assert what the current code returns — assert what a correct implementation must return
- The file must be directly writable to disk and executable with `pytest`
- If a section adds no new tests over prior sections, omit it with a one-line comment

Return ONLY the Python test code described above.
