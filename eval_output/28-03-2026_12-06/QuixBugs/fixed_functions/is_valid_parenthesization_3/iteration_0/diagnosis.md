Root Cause: The function only checks if `depth` ever goes negative (unmatched closing parens), but never verifies that `depth == 0` at the end of the loop. As a result, strings with unmatched opening parentheses (where `depth > 0` at the end) incorrectly return `True` instead of `False`.

Suggestion 1: Change the final `return True` to `return depth == 0`
Replace the last line `return True` with `return depth == 0`. This ensures that after processing all characters, the function only returns `True` when all opening parentheses have been matched (i.e., depth is exactly zero).

Suggestion 2: Add an explicit check before the final return
Before the final `return True`, add a conditional: if `depth != 0`, return `False`, otherwise return `True`. This is logically equivalent to suggestion 1 but makes the intent more explicit by separately handling the unmatched-open-paren case.