Root Cause: The `greater` list comprehension uses `x > pivot` (strict greater than), and the `lesser` list comprehension uses `x < pivot` (strict less than). This means elements equal to the pivot (other than the pivot itself) are excluded from both partitions and are dropped entirely, causing duplicates to be lost from the output.

Suggestion 1: Include duplicates in the `greater` partition
Change the `greater` list comprehension from `x > pivot` to `x >= pivot` so that elements equal to the pivot are included in the greater partition and recursively sorted. This ensures no elements are dropped.

Suggestion 2: Include duplicates in the `lesser` partition
Change the `lesser` list comprehension from `x < pivot` to `x <= pivot` so that elements equal to the pivot are included in the lesser partition and recursively sorted. This also ensures no elements are dropped.