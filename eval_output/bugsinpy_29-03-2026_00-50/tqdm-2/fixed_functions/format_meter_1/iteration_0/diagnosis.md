Root Cause: In the `elif bar_format:` branch (no total), after constructing the `Bar` and formatting `res`, the function calls `if ncols: return disp_trim(res, ncols)` but has no `return res` for when `ncols` is falsy (None or 0). This means the function falls through and implicitly returns `None` when `bar_format` is provided, `total` is None, `{bar}` is present in `bar_format`, and `ncols` is falsy.

Suggestion 1: Add a bare `return res` after the `if ncols:` block in the `elif bar_format:` branch
After the line `if ncols: return disp_trim(res, ncols)` in the `elif bar_format:` branch, add `return res` so that when `ncols` is falsy, the formatted result is still returned instead of falling through to `None`.

Suggestion 2: Change the conditional return to return unconditionally with optional trimming
Replace the two-line sequence `if ncols: return disp_trim(res, ncols)` in the `elif bar_format:` branch with `return disp_trim(res, ncols) if ncols else res`, mirroring the correct pattern that should exist (similar to how the `if total:` branch handles it, noting that branch also lacks a final `return res` — but the primary failing bug is in the `elif` branch).