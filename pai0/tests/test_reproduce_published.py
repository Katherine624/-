import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import reproduce
from scripts.reproduce import commands, load_manifest


class PublishedCheckpointCommandsTests(unittest.TestCase):
    def test_official_pi0_checkpoint_is_explicit(self):
        data = load_manifest()
        command = commands(data, "serve-published")
        self.assertEqual(command[-4:], [
            "--policy.config", "pi0_libero", "--policy.dir",
            "gs://openpi-assets/checkpoints/pi0_libero",
        ])
        self.assertNotIn("pi05_libero", command)

    def test_eval_reuses_fixed_benchmark_settings(self):
        data = load_manifest()
        command = commands(data, "eval-published", suite="libero_spatial")
        self.assertEqual(command[command.index("--args.num-trials-per-task") + 1], "50")
        self.assertEqual(command[command.index("--args.replan-steps") + 1], "5")
        self.assertEqual(command[command.index("--args.seed") + 1], "7")

    def test_unknown_suite_rejected(self):
        with self.assertRaises(ValueError):
            commands(load_manifest(), "eval-published", suite="libero_90")

    def test_cloud_manifest_uses_local_published_checkpoint(self):
        cloud_manifest = reproduce.ROOT / "config" / "experiment.cloud.json"
        with patch.object(reproduce, "MANIFEST", cloud_manifest):
            data = load_manifest()
        self.assertEqual(data["openpi_repo"], "/root/autodl-tmp/openpi")
        self.assertEqual(data["openpi_venv"], "/root/autodl-tmp/openpi-venv311")
        self.assertEqual(
            commands(data, "serve-published")[-1],
            "/root/autodl-tmp/openpi-assets/checkpoints/pi0_libero",
        )

    def test_status_recognizes_local_published_checkpoint(self):
        with TemporaryDirectory() as temp_dir:
            checkpoint = Path(temp_dir) / "pi0_libero"
            metadata = checkpoint / "params" / "_METADATA"
            norm_stats = checkpoint / "assets" / "physical-intelligence" / "libero" / "norm_stats.json"
            metadata.parent.mkdir(parents=True)
            norm_stats.parent.mkdir(parents=True)
            metadata.touch()
            norm_stats.touch()
            data = load_manifest() | {
                "openpi_repo": str(Path(temp_dir) / "openpi"),
                "openpi_data_home": str(Path(temp_dir) / "unused-cache"),
                "published_libero_checkpoint": str(checkpoint),
            }
            with patch.object(reproduce, "gpu_memory_gib", return_value=None):
                checks, _ = reproduce.status(data)
            self.assertTrue(checks["published_libero_checkpoint_cached"])

    def test_status_recognizes_external_project_environment(self):
        with TemporaryDirectory() as temp_dir:
            environment = Path(temp_dir) / "openpi-venv"
            python = environment / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.touch()
            data = load_manifest() | {
                "openpi_repo": str(Path(temp_dir) / "openpi"),
                "openpi_venv": str(environment),
            }
            with patch.object(reproduce, "gpu_memory_gib", return_value=None):
                checks, _ = reproduce.status(data)
            self.assertTrue(checks["python_environment"])

    def test_cloud_manifest_env_applies_to_remote_dry_runs(self):
        cloud_manifest = reproduce.ROOT / "config" / "experiment.cloud.json"
        env = os.environ | {"PI0_EXPERIMENT_MANIFEST": str(cloud_manifest)}
        for script, args, expected in (
            (
                "reproduce.py", ["serve-published"],
                "/root/autodl-tmp/openpi-assets/checkpoints/pi0_libero",
            ),
            (
                "setup_libero_sim.py", [],
                str(Path("/root/autodl-tmp/openpi") / "examples/libero/.venv"),
            ),
        ):
            with self.subTest(script=script):
                process = subprocess.run(
                    [sys.executable, str(reproduce.ROOT / "scripts" / script), *args],
                    env=env, capture_output=True, text=True, check=True,
                )
                self.assertIn(expected, process.stdout)


if __name__ == "__main__":
    unittest.main()
