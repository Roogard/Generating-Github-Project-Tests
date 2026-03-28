Root Cause: The base case condition `if len(arr) == 0` only stops recursion for empty arrays, but not for single-element arrays. When `arr` has length 1, `middle = 1 // 2 = 0`, so `arr[middle:]` is the full array again (length 1), causing infinite recursion on the `right = mergesort(arr[middle:])` call.

Suggestion 1: Change base case to handle single-element arrays
Change the condition `if len(arr) == 0` to `if len(arr) <= 1` on line 15, so that both empty arrays and single-element arrays are returned immediately without further recursion.

Suggestion 2: Change base case to check length less than 2
Replace `if len(arr) == 0` with `if len(arr) < 2` on line 15, which equivalently stops recursion for arrays of length 0 or 1, preventing the infinite recursion when a single-element array is split into an empty left half and a length-1 right half.