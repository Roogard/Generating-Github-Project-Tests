Root Cause: The `lesser` and `greater` list comprehensions use strict `<` and `>` comparisons, which means elements equal to the pivot (duplicates) are excluded from both partitions. Since only `[pivot]` (a single element) is placed in the result, all duplicate occurrences of the pivot beyond the first are silently dropped.

Suggestion 1: Include duplicates in the `lesser` partition using `<=`
Change the `lesser` list comprehension from `x < pivot` to `x <= pivot`. This way, elements equal to the pivot are included in the lesser partition and will be recursively sorted, preserving all duplicates. The `greater` partition remains `x > pivot` to avoid double-counting.

Suggestion 2: Include duplicates via the pivot placeholder using a list with all equal elements
Instead of `[pivot]`, collect all elements equal to the pivot into a list (e.g., `[x for x in arr if x == pivot]`) and place it between `lesser` and `greater`. This explicitly preserves every occurrence of the pivot value while keeping the `lesser` and `greater` filters strictly `< pivot` and `> pivot`.