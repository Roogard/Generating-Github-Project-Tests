Root Cause: The `disable=None` branch: when `disable is None` and the file is a TTY (so `not file.isatty()` is False), the condition `if disable is None and hasattr(file, "isatty") and not file.isatty()` is not entered, leaving `disable` as `None` rather than converting it to `False`. Additionally, the `last_print_n` attribute is not being set when `disable=True` (early return path) — the early-return block sets `self.n = initial` and `self.total = total` but is missing `self.last_print_n = initial`.

Suggestion 1: Set `self.last_print_n = initial` in the early-return (disable=True) block
In the `if disable:` early-return block (just after `self.n = initial`), add `self.last_print_n = initial` so the attribute exists even when `disable=True`.

Suggestion 2: Convert `disable=None` to `False` when the file is a TTY, and add `last_print_n` in the disabled path
After the `if disable is None and hasattr(file, "isatty") and not file.isatty(): disable = True` block, add an `elif disable is None: disable = False` to convert the remaining `None` case to `False`. Separately, in the `if disable:` early return block, insert `self.last_print_n = initial` before the `return` statement.