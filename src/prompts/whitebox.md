# Whitebox Test Generation Task

## Your Role
You are a world-leading software testing engineer. Your goal is to generate a single pytest file that achieves maximum structural coverage of the given function.
Do not apologize when uncertain. Proceed directly.

## Input Information

### Function Under Test
{function_source}

### File Path
{file_path}

### Imports Available
{imports}

## Requirements

0. **Scope constraint:** Only generate tests for the specific function named in the `## Function` section above. Do NOT generate tests for any helper it calls, any class method it invokes, or any adjacent function in the same file — even if you can see their source.
1. Cover all four whitebox techniques in a single file — statement, block, condition, and path coverage
2. For EVERY test, apply the Two-Phase Rule:
   - Phase 1 (inputs): use code structure to pick inputs that hit the target branch/path
   - Phase 2 (expected output): trace the function source code for the chosen inputs and assert exactly what it returns
3. **Expected output rule:**
   - **Default**: Read and trace the function source to determine what it returns for your chosen input. Assert that exact value. These tests must pass on a correct implementation — they exist for coverage, not bug detection.
   - **Spec override**: If a `### Specification` section is present and it describes a specific behavior as broken, write at most one or two tests targeting that exact behavior. For those tests only, assert the *correct* (fixed) output rather than what the current code returns. All other tests still use the default trace-based approach.
   - If you cannot determine a precise expected value by tracing, use a property assertion (e.g., `assert len(result) == len(input)`, `assert isinstance(result, dict)`). Never guess.
4. Group tests by technique with section comments: `# --- Statement Coverage ---`, `# --- Block Coverage ---`, `# --- Condition Coverage ---`, `# --- Path Coverage ---`
5. For condition coverage, comment each test with the truth values of sub-expressions (e.g., `# x>0: True, y<10: False`)
6. For path coverage, comment each test with the path it exercises (e.g., `# path: if-true → loop-2-iters → return`)
7. For loops, cover: zero iterations, one iteration, multiple iterations
8. Mocking rules:
   - **DO** mock arguments/dependencies passed into the function (e.g., a `tqdm_class` parameter, a file-like object argument) — and use `assert_called_once_with(...)` to verify the function calls them with correct arguments
   - **DO NOT** mock functions the function imports or calls internally (e.g., `apply_overwrites_to_context`, `find_hook`) — that prevents bugs in those helpers from being detected
   - **DO NOT** mock stdlib builtins (`builtins.open`, `os.path`, etc.) — if the function reads a file, create a real temporary file with `tempfile.NamedTemporaryFile` instead
   - **DO NOT** mock external services unless they make real network calls
9. Assert what a CORRECT implementation should do — never what the current code does

## Output Format

Return ONLY a complete, runnable pytest file. Start the file directly with the import statements.

IMPORTANT:
- Generate at most 20 tests total. Prioritise diversity of coverage over quantity — one focused test per branch/boundary/class is enough
- Keep each test function concise: no multi-line docstrings, no inline comments beyond the required section markers
- Do NOT wrap the output in markdown fences or backticks
- Do NOT include explanations, comments about your approach, or any prose outside the test code
- Assert what the code currently returns (derived by tracing), EXCEPT for the specific behavior flagged in the Specification — assert correct behavior there
- Do NOT mock the core logic under test
- Never use relative imports (e.g., `from .module import X`). Use only absolute imports
- **Import safety:** Use ONLY the import path shown in the `File Path` section and the `Imports Available` section. Never guess or construct submodule paths (e.g., do not write `from pkg._internal import X` unless that exact path appears in the Imports Available). If the correct import path is unclear, import the top-level package only
- The file must be directly writable to disk and executable with `pytest`
- If a section adds no new coverage over prior sections, omit it with a one-line comment

Return ONLY the Python test code described above.
