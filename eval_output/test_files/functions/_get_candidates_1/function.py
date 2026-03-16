def _backtrack(
        constructed_so_far: list[int] | None = None,
        result: list[list[int]] | None = None,
    ) -> None:
        if constructed_so_far is None:
            constructed_so_far = []
        if result is None:
            result = []
        should_stop, reached_target = _is_complete(constructed_so_far)
        if should_stop:
            if reached_target:
                result.append(constructed_so_far)
            return
        candidates = _get_candidates(constructed_so_far)
        for candidate in candidates:
            constructed_so_far.append(candidate)
            _backtrack(constructed_so_far[:], result)
            constructed_so_far.pop()