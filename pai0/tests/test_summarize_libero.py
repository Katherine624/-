import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.summarize_libero import main, parse_log


def detailed_log(trials_per_task=2):
    lines = []
    successes = 0
    for task_index in range(10):
        task_successes = 0
        for episode_index in range(1, trials_per_task + 1):
            success = episode_index % 2 == 1
            lines += [
                "INFO:root:",
                f"Task: task {task_index}",
                f"INFO:root:Starting episode {episode_index}...",
                f"INFO:root:Success: {success}",
            ]
            task_successes += success
        successes += task_successes
        lines.append(f"INFO:root:Current task success rate: {task_successes / trials_per_task}")
    lines += [
        f"INFO:root:Total success rate: {successes / (10 * trials_per_task)}",
        f"INFO:root:Total episodes: {10 * trials_per_task}",
    ]
    return "\n".join(lines)


class ParseLiberoLogTests(unittest.TestCase):
    def test_complete_suite(self):
        lines = ["Success: True"] * 40 + ["Success: False"] * 10
        lines += ["Current task success rate: 0.8"]
        lines *= 10
        lines += ["Total success rate: 0.8", "Total episodes: 500"]
        result = parse_log("libero_spatial", "\n".join(lines))
        self.assertEqual(result["successes"], 400)
        self.assertEqual(result["episodes"], 500)
        self.assertEqual(result["success_rate"], 0.8)
        self.assertIsNone(result["task_results"][0]["task_name"])

    def test_detailed_task_and_episode_results(self):
        result = parse_log("libero_spatial", detailed_log(), trials_per_task=2)
        self.assertEqual(result["episodes"], 20)
        self.assertEqual(result["successes"], 10)
        self.assertEqual(len(result["task_results"]), 10)
        self.assertEqual(result["task_results"][3], {
            "task_index": 3,
            "task_name": "task 3",
            "episodes": 2,
            "successes": 1,
            "failures": 1,
            "success_rate": 0.5,
            "episode_results": [
                {"episode_index": 1, "success": True},
                {"episode_index": 2, "success": False},
            ],
        })

    def test_mismatched_task_name_rejected(self):
        contents = detailed_log().replace("Task: task 0\nINFO:root:Starting episode 2", "Task: wrong task\nINFO:root:Starting episode 2")
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            parse_log("libero_spatial", contents, trials_per_task=2)

    def test_mismatched_task_rate_rejected(self):
        contents = detailed_log().replace("Current task success rate: 0.5", "Current task success rate: 1.0", 1)
        with self.assertRaisesRegex(ValueError, "rate disagrees"):
            parse_log("libero_spatial", contents, trials_per_task=2)

    def test_four_suite_smoke_csv_not_formal_benchmark(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "smoke.log"
            log.write_text(detailed_log(trials_per_task=1), encoding="utf-8")
            output = root / "summary.json"
            task_csv = root / "tasks.csv"
            episode_csv = root / "episodes.csv"
            args = ["summarize_libero.py", "--trials-per-task", "1", "--source", "official-published"]
            for suite in ("libero_spatial", "libero_object", "libero_goal", "libero_10"):
                args += ["--log", f"{suite}={log}"]
            args += ["--output", str(output), "--task-csv", str(task_csv), "--episode-csv", str(episode_csv)]
            with patch("sys.argv", args), contextlib.redirect_stdout(io.StringIO()):
                main()
            summary = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(summary["trials_per_task"], 1)
            self.assertEqual(summary["result_stage"], "small_sample_smoke_test")
            self.assertFalse(summary["complete_four_suite_benchmark"])
            self.assertEqual(summary["checkpoint_source"], "official-published")
            with task_csv.open(encoding="utf-8-sig", newline="") as stream:
                tasks = list(csv.DictReader(stream))
            with episode_csv.open(encoding="utf-8-sig", newline="") as stream:
                episodes = list(csv.DictReader(stream))
            self.assertEqual(len(tasks), 40)
            self.assertEqual(len(episodes), 40)
            self.assertEqual(tasks[0]["task_name"], "task 0")
            self.assertEqual(episodes[0]["success"], "True")

    def test_incomplete_log_rejected(self):
        with self.assertRaises(ValueError):
            parse_log("libero_spatial", "Success: True\nTotal success rate: 1.0\nTotal episodes: 1")


if __name__ == "__main__":
    unittest.main()
