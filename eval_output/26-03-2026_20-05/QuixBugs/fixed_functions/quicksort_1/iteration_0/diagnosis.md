Root Cause: The partition logic uses strict `x < pivot` for `lesser` and strict `x > pivot` for `greater`, which means elements equal to the pivot (other than the pivot itself) are excluded from both partitions and dropped entirely from the result. This causes duplicates to be lost and, in the case of already-sorted or reverse-sorted arrays with many equal-pivot scenarios, leads to infinite recursion because elements equal to the pivot are never consumed.

Suggestion 1: Include duplicates in the `lesser` partition
Change the `lesser` list comprehension from `x < pivot` to `x <= pivot` so that elements equal to the pivot are included in one of the partitions. This ensures all duplicate values are preserved in the output. The `greater` partition filter (`x > pivot`) remains unchanged.

Suggestion 2: Include duplicates in the `greater` partition
Change the `greater` list comprehension from `x > pivot` to `x >= pivot` so that elements equal to the pivot are captured in the `greater` partition instead. The `lesser` filter (`x < pivot`) remains unchanged. Either suggestion correctly preserves all duplicate elements, though Suggestion 1 is the more conventional approach.