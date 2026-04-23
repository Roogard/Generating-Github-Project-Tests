# Golden examples

Hand-curated exemplar `(function, test_agent.py)` pairs the agent can load via
`view_golden_example(name)`. These are intentionally small — a handful of
high-quality references the model can study when it's stuck or needs a pattern.

Golden examples complement (not replace) the Chroma RAG memory in
`src/vectordb.py`:

- **Golden** = hand-picked canon. Always available, manually reviewed,
  ships with the code, small set (~3–5).
- **Dynamic** = learned over time via `ingest_example` during the QuixBugs
  populate phase. Retrieved via `search_similar_tests`. Grows with use.

## Adding a new example

Create a folder here with three files:

```
src/agent/examples/golden/<name>/
  function.py      the function under test (one function, no surrounding junk)
  test_agent.py    the pytest file — same format the agent should produce
  notes.md         one-paragraph note: why is this a good example?
                   what F→P pattern does it demonstrate?
```

Good candidates:
- Tests that exercise a real off-by-one boundary with Tier-2 metamorphic
  assertions (not guessed exact values).
- Tests that catch a negation-error mutation with `pytest.raises`.
- Functions where blackbox property assertions (`isinstance`, `len >= ...`)
  cleanly beat exact-value matching.

Bad candidates:
- Huge tests. The agent has a budget.
- Tests that assert implementation details (private attributes, internal state).
- Tests that mock internal helpers of the function under test.
