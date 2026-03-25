Task Description:

You are helping generate automated tests for functions in a GitHub repository. The goal is to produce high-quality tests that maximize coverage of potential bugs while minimizing redundant tests and unnecessary computation. You will operate within a multi-agent framework where different specialized agents generate different types of tests (e.g., boundary tests, exception tests, fuzz tests, CFG/path tests).

We are adopting a machine learning-guided strategy selection approach:

Dataset Generation (Offline, One-Time Expensive Stage)

For each function in the repo, extract structural features using TreeSitter: AST structure, parameters, branches, loops, exception handling, string operations, cyclomatic complexity, etc.

Run each agent to generate candidate tests for each function.

Execute the tests in a sandboxed environment, capturing mutation testing results to determine which mutants each test kills.

Aggregate results to compute unique contribution per agent/strategy, deduplicating overlapping or redundant tests.

Store the results in a dataset mapping:

function features → strategy effectiveness (unique mutants killed per agent)

Machine Learning-Guided Test Strategy (Guided Generation Stage)

Train a model (supervised learning) to predict which test strategies/agents are likely to be effective for a given function based on its structural features.

At inference time, for a new repo or function, use the model to select a small subset of agents most likely to produce useful tests.

Run only the selected agents to generate tests, then filter redundant tests using mutation coverage vectors.

Evaluation Phase

Perform mutation testing to measure the effectiveness of generated tests.

Collect coverage and redundancy metrics.

Optionally perform experiments with test set minimization (greedy selection) to find the smallest test suite that still achieves high coverage.

Key Guidelines for Test Generation Agents:

Tests must run successfully in the sandbox environment; handle imports, initialization, and dependencies where possible.

Avoid unnecessary duplication: tests that kill the same mutants as previous tests do not add value.

Account for runtime behaviors that static AST features cannot capture (e.g., division by zero, string parsing edge cases).

Tests may require mocking or stubbing external dependencies (databases, file IO, network calls).

Include meaningful assertions that actually test function behavior. Avoid trivial asserts (assert True).

Follow structural hints from the ML-guided model: the model predicts which strategies are likely to succeed for each function.

Known Challenges / Failure Modes to Consider:

Runtime execution failures: missing imports, global state, class/object initialization.

Function dependencies: calls to other functions, modules, or external libraries.

Redundant tests: overlapping tests within an agent that do not add unique coverage.

Explosion of candidate tests: generating too many tests can make evaluation and storage expensive.

Mutation testing limitations: some mutants may be trivial, equivalent, or crash tests.

Dynamic behaviors not captured by AST: some errors only appear at runtime.

Side effects: avoid tests that write to files, databases, or send network requests outside the sandbox.

Variability in coding styles: different repos may have async functions, coroutines, generators, or unusual patterns.

Output Requirements:

Generate tests as executable code snippets for each function.

Clearly indicate which agent generated each test.

Annotate test purpose where possible (e.g., “Boundary test for parameter x”, “Exception handling test”).

Output in a format compatible with mutation evaluation and later ML dataset aggregation.

Objective:

Maximize the unique bug/mutant coverage for each function using as few tests as possible, while ensuring tests are executable and meaningful. Use ML-guided strategy selection to reduce the number of agents run per function and avoid unnecessary duplication.