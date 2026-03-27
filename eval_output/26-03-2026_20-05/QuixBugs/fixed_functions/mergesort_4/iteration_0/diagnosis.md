Root Cause: The base case `if len(arr) == 0` only handles empty arrays, but when `arr` has length 1, `middle = 1 // 2 = 0`, so `arr[:middle]` is `[]` (handled fine) but `arr[middle:]` is the full array `arr[0:]` — the same single-element array — causing infinite recursion on the `right = mergesort(arr[middle:])` call.

Suggestion 1: Change base case to handle arrays of length 0 or 1
Change the condition `if len(arr) == 0` to `if len(arr) <= 1` so that single-element arrays are also returned immediately without attempting to split and recurse further.

Suggestion 2: Change middle calculation to ensure strictly smaller subproblems
Keep the base case as `len(arr) == 0` but change `middle = len(arr) // 2` to `middle = len(arr) // 2 if len(arr) // 2 > 0 else 1`, ensuring that for a single-element array the split always produces a smaller subproblem. However, this is more convoluted — the cleaner fix remains changing the base case to `len(arr) <= 1`.