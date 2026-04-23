# Why this example

The QuixBugs `bitcount` bug mutates `n &= n - 1` to `n ^= n - 1` — the xor
causes the loop to never terminate (or to produce wrong counts) on many
inputs. Most obvious guess-the-value tests pass on BOTH versions because
the buggy loop happens to hit the right count on a few inputs. That's F→F
dominance.

The tests in `test_agent.py` detect the bug by:
- Comparing against a stdlib oracle (`bin(n).count("1")`) across a wide
  range — metamorphic Tier 2. No guessed values.
- Asserting metamorphic properties of powers of two and `2**k - 1`.
- Including a cheap non-negativity property test so one assertion always
  passes on the fixed version (useful P→P anchor).

Key lesson: **prefer a small oracle derived from another function over
guessing return values.** `bin(n).count("1")` is a reliable oracle the
model already knows.
