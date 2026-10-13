#!/usr/bin/env python3
"""Audit copied LIBERO rollouts and render a provenance-aware Chinese report.

Example (after all four archives have been copied and extracted)::

    python scripts/render_official_libero_report.py \
      --root reports/libero-runs/2026-09-29-official-50 \
      --output reports/libero-runs/2026-09-29-official-50/EVALUATION_REPORT.md

The default is deliberately strict: incomplete suites, mismatched videos, or bad
archive hashes fail without writing a final report. --allow-partial is for a
clearly labelled progress draft, never a full-benchmark claim.
"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys


SUITES = ("libero_10", "libero_spatial", "libero_object", "libero_goal")
VIDEO_RE = re.compile(r"^rollout_task(\d{2})_trial(\d{3})_.+_(success|failure)\.mp4$")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def link(path, report_dir):
    try:
        return Path(os.path.relpath(path, report_dir)).as_posix()
    except ValueError:  # A draft report may live on a different Windows drive.
        return path.as_posix()


def audit_suite(root, name, report_dir):
    suite_dir = root / name
    summary_path = suite_dir / "summary.json"
    log_path = suite_dir / "evaluation.log"
    task_csv = suite_dir / "task_results.csv"
    episode_csv = suite_dir / "episode_results.csv"
    archive = root / f"{name}.tar.gz"
    checksum = root / f"{name}.sha256"
    for path in (summary_path, log_path, task_csv, episode_csv, archive, checksum):
        require(path.is_file(), f"{name}: missing {path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    require(summary.get("checkpoint_source") == "official-published", f"{name}: checkpoint source")
    require(summary.get("training_performed_by_this_project") is False, f"{name}: training provenance")
    require(summary.get("trials_per_task") == 50, f"{name}: trials per task")
    require(len(summary.get("suites", [])) == 1, f"{name}: expected single-suite summary")
    result = summary["suites"][0]
    require(result.get("suite") == name, f"{name}: suite name")
    tasks = result.get("task_results", [])
    require(len(tasks) == 10, f"{name}: expected 10 tasks")

    all_episodes = {}
    successes = 0
    for index, task in enumerate(tasks):
        require(task.get("task_index") == index, f"{name}: task index {index}")
        rows = task.get("episode_results", [])
        require(len(rows) == task.get("episodes") == 50, f"{name}: task {index} episode count")
        task_successes = 0
        for trial, row in enumerate(rows, 1):
            require(row.get("episode_index") == trial, f"{name}: task {index} trial index")
            require(type(row.get("success")) is bool, f"{name}: task {index} trial {trial} outcome")
            all_episodes[(index, trial)] = row["success"]
            task_successes += row["success"]
        require(task.get("successes") == task_successes, f"{name}: task {index} successes")
        require(task.get("failures") == 50 - task_successes, f"{name}: task {index} failures")
        require(abs(task.get("success_rate", -1) - task_successes / 50) < 1e-9,
                f"{name}: task {index} rate")
        successes += task_successes
    require(result.get("episodes") == 500, f"{name}: total episodes")
    require(result.get("successes") == successes, f"{name}: total successes")
    require(abs(result.get("success_rate", -1) - successes / 500) < 1e-9,
            f"{name}: total rate")

    log = log_path.read_text(encoding="utf-8", errors="replace")
    require(re.search(r"(?m)^RUN_EXIT=0\s*$", log) is not None, f"{name}: run exit not zero")
    require(len(re.findall(r"INFO:root:Success: (?:True|False)", log)) == 500,
            f"{name}: raw log must contain 500 outcomes")

    videos = list((suite_dir / "videos").glob("*.mp4"))
    require(len(videos) == 500, f"{name}: found {len(videos)} videos, expected 500")
    observed = {}
    for video in videos:
        match = VIDEO_RE.fullmatch(video.name)
        require(match is not None, f"{name}: unrecognized video name {video.name}")
        key = (int(match.group(1)), int(match.group(2)))
        require(key not in observed, f"{name}: duplicate video for {key}")
        observed[key] = match.group(3) == "success"
        require(video.stat().st_size > 0, f"{name}: empty video {video.name}")
    require(observed == all_episodes, f"{name}: video outcomes disagree with episode records")

    with task_csv.open(encoding="utf-8-sig", newline="") as stream:
        require(len(list(csv.DictReader(stream))) == 10, f"{name}: task CSV row count")
    with episode_csv.open(encoding="utf-8-sig", newline="") as stream:
        require(len(list(csv.DictReader(stream))) == 500, f"{name}: episode CSV row count")

    expected = checksum.read_text(encoding="utf-8").split()[0].lower()
    require(re.fullmatch(r"[0-9a-f]{64}", expected) is not None, f"{name}: invalid SHA256")
    actual = sha256(archive)
    require(actual == expected, f"{name}: archive SHA256 mismatch")

    warning_counts = {
        "EGL_NOT_INITIALIZED": log.count("EGL_NOT_INITIALIZED"),
        "Traceback": log.count("Traceback (most recent call last)"),
    }
    return {
        "name": name, "successes": successes, "tasks": tasks, "warnings": warning_counts,
        "summary": link(summary_path, report_dir), "log": link(log_path, report_dir),
        "task_csv": link(task_csv, report_dir), "episode_csv": link(episode_csv, report_dir),
        "videos": link(suite_dir / "videos", report_dir), "archive": link(archive, report_dir),
        "checksum": actual,
    }


def render(results, root, report_dir, complete):
    total_successes = sum(item["successes"] for item in results)
    total_episodes = 500 * len(results)
    lines = [
        "# π₀ 官方预训练权重：LIBERO 免训练评估报告",
        "",
        "**状态：{}。**".format("四套件完整评测，已通过本地一致性检查" if complete else
                                  "仅已回传套件的阶段性结果，不能作为四套件最终结论"),
        "",
        "本次直接使用官方发布的 `pi0_libero` 检查点（`gs://openpi-assets/checkpoints/pi0_libero`）进行仿真推理；"
        "**本项目没有训练或微调该模型**。这是公开 LIBERO 仿真基准评估，**不是**论文中私有机器人数据或真实机器人实验的复现。",
        "",
        "## 总览",
        "",
        "| 套件 | 成功 / 试验 | 成功率 | 逐次视频 |",
        "|---|---:|---:|---:|",
    ]
    for item in results:
        lines.append(f"| {item['name']} | {item['successes']} / 500 | "
                     f"{item['successes'] / 5:.1f}% | 500 |")
    lines += [
        f"| {'四套合计' if complete else '已完成部分合计'} | {total_successes} / {total_episodes} | "
        f"{100 * total_successes / total_episodes:.2f}% | {total_episodes} |",
        "",
        "每个套件 10 项任务，每项 50 次试验；成功率按 `成功次数 ÷ 实际试验次数` 计算。"
        "本次各项样本量相同，合计成功率与已完成套件成功率的等权平均相同。",
        "",
        "## 逐任务结果",
        "",
        "| 套件 | 编号 | 任务（原始英文描述） | 成功 / 50 | 成功率 |",
        "|---|---:|---|---:|---:|",
    ]
    for item in results:
        for task in item["tasks"]:
            name = str(task["task_name"]).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {item['name']} | {task['task_index']:02d} | {name} | "
                         f"{task['successes']} / 50 | {task['successes'] * 2:.1f}% |")
    lines += ["", "## 原始证据与核验", ""]
    for item in results:
        lines.append(f"- `{item['name']}`：[原始日志]({item['log']}) · "
                     f"[逐任务 CSV]({item['task_csv']}) · [逐次 CSV]({item['episode_csv']}) · "
                     f"[机器结果 JSON]({item['summary']}) · [500 段视频]({item['videos']}) · "
                     f"[原始归档]({item['archive']})；归档 SHA-256 `{item['checksum']}`。")
    manifest = root / "run-manifest.txt"
    progress = root / "progress.tsv"
    if manifest.is_file():
        lines.append(f"- [运行清单]({link(manifest, report_dir)})。")
    if progress.is_file():
        lines.append(f"- [逐套进度与退出状态]({link(progress, report_dir)})。")
    for label, relative in (
        ("四套汇总 JSON", "summary.json"),
        ("40 项任务 CSV", "task_results.csv"),
        ("2000 次试验 CSV", "episode_results.csv"),
        ("云端服务日志", "reports/pi0-server-direct2-s7ryb4fgkw.log"),
        ("评测运行脚本", "scripts/run_official_libero_overnight.sh"),
        ("逐次视频评测脚本", "scripts/libero_eval_preserve_videos.py"),
        ("原始元数据归档", "run-metadata.tar.gz"),
    ):
        path = root / relative
        if path.is_file():
            lines.append(f"- [{label}]({link(path, report_dir)})。")
    lines += [
        "",
        "核验范围：每套运行退出码为 0；原始日志含 500 条成败记录；JSON 内 10×50 次结果、"
        "CSV 行数、500 个非空 MP4 文件及文件名标记的成败互相一致；本地归档 SHA-256 与 `.sha256` 文件一致。"
        "这证明文件和计数的一致性，不等同于独立重做仿真。",
        "",
        "## 警告与解释边界",
        "",
    ]
    for item in results:
        warnings = item["warnings"]
        if any(warnings.values()):
            lines.append(f"- `{item['name']}` 日志中出现 `EGL_NOT_INITIALIZED` "
                         f"{warnings['EGL_NOT_INITIALIZED']} 次、Python traceback "
                         f"{warnings['Traceback']} 次；该套运行退出码仍为 0 且 500 次结果齐全。"
                         "需结合日志判断其发生在清理阶段，不能仅凭警告文字认定评估失败。")
    lines += [
        "- 成功率来自 LIBERO 仿真器对 rollout 的成功判定；不是分类模型的验证集准确率，也不能推断真实机器人成功率。",
        "- 这是单个模型检查点、单次配置与固定随机种子（运行脚本使用 seed 7）的结果；"
        "没有多种子重复、真实机器人外部验证或与论文所有训练条件的同条件对照。",
        "- 本报告的数字由本地原始日志和视频重新核对。若需将结果写入论文，"
        "还应保存环境版本、检查点校验记录与运行命令，并说明与原文实验的差异。",
        "",
    ]
    if not complete:
        missing = ", ".join(name for name in SUITES if name not in {item["name"] for item in results})
        lines += [f"**尚缺套件：** `{missing}`。不应把上述阶段性合计称为 2000 次完整评测。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Extracted run directory")
    parser.add_argument("--output", type=Path, required=True, help="Markdown report to write")
    parser.add_argument("--allow-partial", action="store_true", help="Permit an explicitly partial progress draft")
    args = parser.parse_args()
    root = args.root.resolve()
    report_dir = args.output.resolve().parent
    require(root.is_dir(), f"missing run directory: {root}")
    present = [name for name in SUITES if (root / name / "summary.json").is_file()]
    require(present, "no suite summaries found")
    complete = len(present) == 4
    require(complete or args.allow_partial, "four complete suites required (or use --allow-partial for a draft)")
    results = [audit_suite(root, name, report_dir) for name in present]
    report = render(results, root, report_dir, complete)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote {'complete' if complete else 'partial'} report: {args.output}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
