# Oracle Revision Task

## Your Role
You are a world-leading test maintenance engineer. A function was buggy when its tests were written, so some tests encoded the buggy output as the expected value. The function has now been fixed. Your goal is to update the failing tests to assert the correct behavior.
Do not apologize when wrong. Proceed directly.

## Input Information

### Fixed Function
{fixed_function_source}

### Test File
{test_file_source}

### Failing Tests
{failing_test_details}

## Requirements

1. For each failing test, revise ONLY the expected value to match what the correct function returns
2. Keep the test input EXACTLY as-is — do not change any arguments passed to the function
3. Keep the test structure EXACTLY as-is — do not rename, reorder, or restructure tests
4. Where possible, replace exact value assertions with property assertions (e.g., `assert sorted(result) == sorted(input)` instead of `assert result == [1, 2, 3]`)
5. If a test was asserting behavior that only existed due to the bug (e.g., duplicates dropped, wrong return value), fix the assertion to check the correct behavior
6. Fix any comments that describe the buggy behavior — update them to describe the correct behavior
7. Leave all passing tests completely unchanged

## Output Format

Return ONLY the complete revised test file. Include every test — passing tests verbatim, failing tests with revised assertions only.

IMPORTANT:
- Do NOT wrap the output in markdown fences or backticks
- Do NOT add new tests
- Do NOT remove tests
- Do NOT change test inputs or function call arguments
- Do NOT change import statements
- The output must be a complete, runnable test file

Return ONLY the complete revised Python test file described above.
