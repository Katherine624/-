#!/usr/bin/env python3
"""Validate official LIBERO log files and write a machine-readable summary.

Example: python scripts/summarize_libero.py --log libero_spatial=path/to/log
"""

import argparse
import csv
import json
from pathlib import Path
import re
import sys


SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
EVENT_PATTERNS = (
    ("task", re.compile(r"^Task: (.+)$")),
    ("start", re.compile(r"^Starting episode (\d+)\.\.\.$")),
    ("success", re.compile(r"^Success: (True|False)$")),
    ("task_rate", re.compile(r"^Current task success rate: ([0-9.]+)$")),
    ("total_rate", re.compile(r"^Total success rate: ([0-9.]+)$")),
    ("total_episodes", re.compile(r"^Total episodes: (\d+)$")),
)


def _events(contents: str):
    """Yield only LIBERO's structured log messages, ignoring tqdm/ANSI noise."""
    for line in contents.splitlines():
        line = ANSI_RE.sub("", line).strip()
        if "INFO:root:" in line:
            line = line.rsplit("INFO:root:", 1)[1].strip()
        for kind, pattern in EVENT_PATTERNS:
            match = pattern.fullmatch(line)
            if match:
                yield kind, match.group(1)
                break


def _new_task(index: int, name):
    return {
        "task_index": index,
        "task_name": name,
        "episodes": 0,
        "successes": 0,
        "failures": 0,
        "success_rate": 0.0,
        "episode_results": [],
    }


def parse_log(suite: str, contents: str, trials_per_task: int = 50) -> dict:
    if suite not in SUITES:
        raise ValueError(f"Unknown suite: {suite}")
    if trials_per_task < 1:
        raise ValueError("trials_per_task must be positive")
    events = list(_events(contents))
    has_task_names = any(kind == "task" for kind, _ in events)
    has_starts = any(kind == "start" for kind, _ in events)
    if has_task_names != has_starts:
        raise ValueError(f"{suite}: incomplete task/episode markers")
    detailed = has_task_names
    tasks = []
    current = None
    pending_episode = None
    task_marker_ready = False
    total_rates = []
    total_counts = []
    for kind, value in events:
        if kind == "task":
            if current is None:
                current = _new_task(len(tasks), value)
            elif current["task_name"] != value or task_marker_ready or pending_episode is not None:
                raise ValueError(f"{suite}: inconsistent or repeated task marker")
            task_marker_ready = True
        elif kind == "start":
            if current is None or not task_marker_ready or pending_episode is not None:
                raise ValueError(f"{suite}: episode start without matching task marker")
            pending_episode = int(value)
            if pending_episode != len(current["episode_results"]) + 1:
                raise ValueError(f"{suite}: unexpected episode number {pending_episode}")
            task_marker_ready = False
        elif kind == "success":
            if detailed and (current is None or pending_episode is None):
                raise ValueError(f"{suite}: success without episode start")
            if current is None:
                current = _new_task(len(tasks), None)
            episode_index = pending_episode or len(current["episode_results"]) + 1
            succeeded = value == "True"
            current["episode_results"].append({"episode_index": episode_index, "success": succeeded})
            pending_episode = None
        elif kind == "task_rate":
            if current is None or pending_episode is not None or task_marker_ready:
                raise ValueError(f"{suite}: task rate without completed episodes")
            outcomes = current["episode_results"]
            if len(outcomes) != trials_per_task:
                raise ValueError(f"{suite}: task {len(tasks)} has {len(outcomes)} episodes, expected {trials_per_task}")
            current["episodes"] = len(outcomes)
            current["successes"] = sum(row["success"] for row in outcomes)
            current["failures"] = current["episodes"] - current["successes"]
            current["success_rate"] = current["successes"] / current["episodes"]
            if abs(current["success_rate"] - float(value)) > 1e-6:
                raise ValueError(f"{suite}: task {len(tasks)} rate disagrees with episode outcomes")
            tasks.append(current)
            current = None
        elif kind == "total_rate":
            total_rates.append(float(value))
        elif kind == "total_episodes":
            total_counts.append(int(value))
    if current is not None or pending_episode is not None:
        raise ValueError(f"{suite}: unfinished task or episode")
    if len(total_rates) != 1 or len(total_counts) != 1:
        raise ValueError(f"{suite}: missing or repeated final totals")
    episodes = sum(task["episodes"] for task in tasks)
    successes = sum(task["successes"] for task in tasks)
    if total_counts[0] != episodes:
        raise ValueError(f"{suite}: total episodes {total_counts[0]} != logged outcomes {episodes}")
    if episodes != 10 * trials_per_task or len(tasks) != 10:
        raise ValueError(f"{suite}: expected 10 tasks × {trials_per_task} episodes")
    rate = successes / episodes
    if abs(rate - total_rates[0]) > 1e-6:
        raise ValueError(f"{suite}: final rate disagrees with episode outcomes")
    task_rates = [task["success_rate"] for task in tasks]
    if abs(rate - sum(task_rates) / 10) > 1e-6:
        raise ValueError(f"{suite}: task rates disagree with episode outcomes")
    return {
        "suite": suite,
        "episodes": episodes,
        "successes": successes,
        "success_rate": rate,
        "task_success_rates": task_rates,
        "task_results": tasks,
    }


def _write_csv(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", action="append", required=True, metavar="SUITE=PATH")
    parser.add_argument("--trials-per-task", type=int, default=50)
    parser.add_argument(
        "--source", choices=("local-training", "official-published"),
        default="local-training", help="Checkpoint provenance for the output JSON",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path; stdout is always printed")
    parser.add_argument("--task-csv", type=Path, help="Optional per-task CSV output path")
    parser.add_argument("--episode-csv", type=Path, help="Optional per-episode CSV output path")
    args = parser.parse_args()
    results = []
    seen = set()
    for item in args.log:
        suite, separator, name = item.partition("=")
        if not separator or suite in seen:
            raise ValueError("Each --log must be a distinct SUITE=PATH")
        seen.add(suite)
        path = Path(name)
        result = parse_log(suite, path.read_text(encoding="utf-8"), args.trials_per_task)
        result["log_file"] = str(path.resolve())
        results.append(result)
    output = {
        "model": "pi0_libero",
        "trials_per_task": args.trials_per_task,
        "result_stage": "full_50_trial_evaluation" if args.trials_per_task == 50 else "small_sample_smoke_test",
        "checkpoint_source": args.source,
        "checkpoint_uri": (
            "gs://openpi-assets/checkpoints/pi0_libero"
            if args.source == "official-published" else None
        ),
        "training_performed_by_this_project": False if args.source == "official-published" else None,
        "experiment_type": "public_LIBERO_proxy_not_paper_original_experiment",
        "suites": results,
        "macro_average_success_rate": sum(x["success_rate"] for x in results) / len(results),
        "complete_four_suite_benchmark": set(seen) == set(SUITES) and args.trials_per_task == 50,
    }
    serialized = json.dumps(output, ensure_ascii=False, indent=2)
    print(serialized)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    if args.task_csv:
        fields = ("suite", "task_index", "task_name", "episodes", "successes", "failures", "success_rate", "log_file")
        rows = (
            {field: result["suite"] if field == "suite" else result["log_file"] if field == "log_file" else task[field]
             for field in fields}
            for result in results for task in result["task_results"]
        )
        _write_csv(args.task_csv, fields, rows)
    if args.episode_csv:
        fields = ("suite", "task_index", "task_name", "episode_index", "success", "log_file")
        rows = (
            {"suite": result["suite"], "task_index": task["task_index"], "task_name": task["task_name"],
             "episode_index": episode["episode_index"], "success": episode["success"], "log_file": result["log_file"]}
            for result in results for task in result["task_results"] for episode in task["episode_results"]
        )
        _write_csv(args.episode_csv, fields, rows)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
