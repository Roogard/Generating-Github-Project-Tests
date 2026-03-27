Root Cause: The base case on line 15 only returns early when `len(arr) == 0`, but it should also return when `len(arr) == 1`. For a single-element array, `middle = 0`, so `arr[middle:]` equals the full array, causing `mergesort(arr[middle:])` to recurse infinitely on the same input.

Suggestion 1: Change the base case condition to include single-element arrays
Change `if len(arr) == 0:` to `if len(arr) <= 1:` so that both empty arrays and single-element arrays are returned immediately without further recursion.

Suggestion 2: Change the base case condition using a length-1 check separately
Change `if len(arr) == 0:` to `if len(arr) < 2:` which equivalently covers both the empty array and the single-element array cases, preventing the infinite recursion when `middle` would be 0 and `arr[middle:]` would equal the original array.