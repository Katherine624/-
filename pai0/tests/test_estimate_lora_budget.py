import unittest

from scripts.estimate_lora_budget import estimate


class BudgetEstimateTests(unittest.TestCase):
    def test_projects_training_and_preserves_other_costs(self):
        result = estimate(
            budget=100, spent=10, hourly_price=5, seconds_per_step=1,
            current_step=100, target_step=3700, future_nontraining_hours=2, reserve=15,
        )
        self.assertEqual(result["remaining_steps"], 3600)
        self.assertEqual(result["training_hours"], 1)
        self.assertEqual(result["projected_total_yuan"], 40)
        self.assertTrue(result["fits_budget"])

    def test_rejects_over_budget_target(self):
        result = estimate(
            budget=100, spent=20, hourly_price=10, seconds_per_step=10,
            current_step=100, target_step=30000, future_nontraining_hours=3, reserve=15,
        )
        self.assertFalse(result["fits_budget"])
        self.assertLess(result["affordable_additional_steps"], result["remaining_steps"])

    def test_rejects_unmeasured_price_or_speed(self):
        with self.assertRaises(ValueError):
            estimate(100, 0, 0, 1, 0, 100, 1, 15)


if __name__ == "__main__":
    unittest.main()
