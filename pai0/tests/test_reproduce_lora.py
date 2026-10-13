import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import reproduce


class LoraPlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(reproduce, "MANIFEST", reproduce.ROOT / "config" / "experiment.lora.json"):
            cls.data = reproduce.load_manifest()

    def test_lora_manifest_is_distinct_from_full_finetuning(self):
        self.assertEqual(reproduce.training_mode(self.data), "lora")
        self.assertEqual(self.data["train_config"], "pi0_libero_low_mem_finetune")
        self.assertNotEqual(self.data["experiment_name"], reproduce.load_manifest()["experiment_name"])

    def test_pilot_has_a_small_total_step_target(self):
        command = reproduce.commands(self.data, "train", train_steps=100)
        self.assertEqual(command[command.index("--num-train-steps") + 1], "100")
        self.assertNotIn("--resume", command)
        self.assertIn("pi0_libero_low_mem_finetune", command)

    def test_resume_targets_the_same_run(self):
        pilot = reproduce.commands(self.data, "train", train_steps=100)
        resumed = reproduce.commands(self.data, "train", train_steps=500, resume=True)
        self.assertEqual(pilot[pilot.index("--exp-name") + 1], resumed[resumed.index("--exp-name") + 1])
        self.assertEqual(resumed[-1], "--resume")
        self.assertEqual(resumed[resumed.index("--num-train-steps") + 1], "500")

    def test_official_reference_still_uses_non_lora_policy_config(self):
        command = reproduce.commands(self.data, "serve-published")
        self.assertEqual(command[command.index("--policy.config") + 1], "pi0_libero")

    def test_inconsistent_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            reproduce.training_mode(self.data | {"training_mode": "full"})

    def test_checkpoint_status_requires_numeric_step_directory(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            data = self.data | {
                "openpi_repo": str(root / "openpi"),
                "base_checkpoint": str(root / "base"),
            }
            _, _, _, run = reproduce.paths(data)
            (run / "assets").mkdir(parents=True)
            with patch.object(reproduce, "gpu_memory_gib", return_value=None):
                checks, _ = reproduce.status(data)
            self.assertFalse(checks["training_checkpoint"])
            (run / "99").mkdir()
            with patch.object(reproduce, "gpu_memory_gib", return_value=None):
                checks, _ = reproduce.status(data)
            self.assertTrue(checks["training_checkpoint"])


if __name__ == "__main__":
    unittest.main()
