def _union(
        duplicate_results: list[list[Any]],
    ) -> list[list[Any]]:
        results = []
        if len(duplicate_results) != 0:
            duplicate_results.sort()
            results.append(duplicate_results[0])
            for result in duplicate_results[1:]:
                if results[-1] != result:
                    results.append(result)
        return results