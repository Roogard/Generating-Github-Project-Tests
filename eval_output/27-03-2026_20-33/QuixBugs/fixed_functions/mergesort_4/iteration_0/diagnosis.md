Root Cause: The base case on line 15 only returns when `len(arr) == 0`, but it fails to handle the single-element case (`len(arr) == 1`). When a single-element array is passed, `middle = 1 // 2 = 0`, so `arr[middle:]` equals the full array again, causing infinite recursion on the `right = mergesort(arr[middle:])` call.

Suggestion 1: Change the base case to also handle single-element arrays
Change the condition `if len(arr) == 0` to `if len(arr) <= 1` on line 15. This ensures that both empty arrays and single-element arrays are returned immediately without further recursion, which is the correct base case for mergesort.

Suggestion 2: Change the base case to check length less than 2
Replace `if len(arr) == 0` with `if len(arr) < 2` on line 15. This is semantically equivalent to suggestion 1 but uses a slightly different comparison, ensuring that any array with fewer than 2 elements is returned as-is without attempting to split and recurse further.