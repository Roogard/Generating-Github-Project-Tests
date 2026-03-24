def _two_sum(nums: list[Any], target: Any) -> list[list[Any]]:
        nums.sort()
        left = 0
        right = len(nums) - 1
        results = []
        while left < right:
            current_sum = sum_closure(nums[left], nums[right])
            flag = compare_closure(current_sum, target)
            if flag == -1:
                left += 1
            elif flag == 1:
                right -= 1
            else:
                results.append(sorted([nums[left], nums[right]]))
                left += 1
                right -= 1
                while left < len(nums) and same_closure(nums[left - 1], nums[left]):
                    left += 1
                while right >= 0 and same_closure(nums[right], nums[right + 1]):
                    right -= 1
        return results