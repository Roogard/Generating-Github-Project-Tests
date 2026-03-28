Root Cause: The base case on line 15 checks `if len(arr) == 0` and returns, but arrays of length 1 fall through to the else branch. For a single-element array, `middle = 0`, so `arr[middle:]` is the entire array again, causing infinite recursion on the `right = mergesort(arr[middle:])` call.

Suggestion 1: Change base case to handle length <= 1
Change `if len(arr) == 0` to `if len(arr) <= 1` on line 15, so that single-element arrays are also returned immediately without recursing further.

Suggestion 2: Change base case to check length less than 2
Replace the condition `if len(arr) == 0` with `if len(arr) < 2` on line 15, which equivalently handles both empty arrays and single-element arrays as base cases, preventing the infinite recursion when `middle` computes to 0.