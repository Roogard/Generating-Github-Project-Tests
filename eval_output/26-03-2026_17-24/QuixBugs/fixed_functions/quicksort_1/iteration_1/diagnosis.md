Looking at the test failures, the tests expect duplicates to be **deduplicated** — e.g., `quicksort([1, 1]) == [1]` and `quicksort([3, 1, 2, 3, 1]) == [1, 2, 3]`.

The current `equal` line is `equal = [x for x in arr if x == pivot]`, which collects **all** occurrences of the pivot from the entire array, preserving duplicates. The tests expect only one instance of each value to appear in the result.

Root Cause: The `equal` list comprehension `[x for x in arr if x == pivot]` collects all occurrences of the pivot value in the entire array, resulting in duplicates being preserved. However, the tests expect the sort to deduplicate elements, so `equal` should contain only a single instance of the pivot.

Suggestion 1: Replace `equal` with a single-element list containing just the pivot
Change `equal = [x for x in arr if x == pivot]` to `equal = [pivot]`. This ensures exactly one copy of the pivot appears in the output regardless of how many duplicates exist in the input, which matches what the tests expect.

Suggestion 2: Use a set-based deduplication on the `equal` list
Change `equal = [x for x in arr if x == pivot]` to `equal = list(set(x for x in arr if x == pivot))`. Since all elements in that comprehension are equal to `pivot`, the set will collapse them to a single value, producing `[pivot]` — matching the expected deduplicated output.