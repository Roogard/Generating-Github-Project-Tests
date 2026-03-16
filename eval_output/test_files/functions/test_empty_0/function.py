def check_sum(self, nums, target):
        if sum(nums) == target:
            return (True, nums)
        else:
            return (False, nums)