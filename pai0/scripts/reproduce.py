#!/usr/bin/env python3
"""Read-only planning by default; explicit --execute for costly reproduction stages.

Run this with the openpi Python environment inside WSL. No stage silently starts
training, downloads a dataset, overwrites a checkpoint, or launches a simulator.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(os.environ.get("PI0_EXPERIMENT_MANIFEST", ROOT / "config" / "experiment.json"))
TRAINING_MODES = {
    "pi0_libero": "full",
    "pi0_libero_low_mem_finetune": "lora",
}


def load_manifest():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    required = (
        "openpi_commit", "openpi_repo", "openpi_data_home", "uv", "train_config",
        "dataset_repo_id", "base_checkpoint", "published_libero_checkpoint",
        "experiment_name", "eval_suites",
    )
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise ValueError(f"Missing manifest settings: {missing}")
    training_mode(data)
    return data


def training_mode(data):
    expected = TRAINING_MODES.get(data["train_config"])
    if expected is None:
        raise ValueError(f"Unsupported training config: {data['train_config']}")
    mode = data.get("training_mode", expected)
    if mode != expected:
        raise ValueError(f"Training mode {mode!r} does not match {data['train_config']!r}")
    return mode


def gpu_memory_gib():
    if not shutil.which("nvidia-smi"):
        return None
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, check=False,
    )
    try:
        return max(int(line.strip()) for line in result.stdout.splitlines()) / 1024
    except ValueError:
        return None


def paths(data):
    repo = Path(data["openpi_repo"])
    lerobot_home = Path(os.environ.get("HF_LEROBOT_HOME", Path.home() / ".cache/huggingface/lerobot"))
    dataset = lerobot_home / data["dataset_repo_id"]
    stats = repo / "assets" / data["train_config"] / data["dataset_repo_id"] / "norm_stats.json"
    run = repo / "checkpoints" / data["train_config"] / data["experiment_name"]
    return repo, dataset, stats, run


def status(data):
    repo, dataset, stats, run = paths(data)
    project_environment = Path(data.get("openpi_venv", os.environ.get("UV_PROJECT_ENVIRONMENT", repo / ".venv")))
    published = urlparse(data["published_libero_checkpoint"])
    cached_published = (
        Path(data["openpi_data_home"]) / published.netloc / published.path.lstrip("/")
        if published.scheme else Path(data["published_libero_checkpoint"])
    )
    commit = None
    if (repo / ".git").exists():
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True)
        if result.returncode == 0:
            commit = result.stdout.strip()
    memory = gpu_memory_gib()
    checks = {
        "pinned_code": commit == data["openpi_commit"],
        "python_environment": (project_environment / "bin/python").is_file(),
        "base_checkpoint": (Path(data["base_checkpoint"]) / "params/_METADATA").is_file(),
        "published_libero_checkpoint_cached": (
            (cached_published / "params/_METADATA").is_file()
            and (cached_published / "assets/physical-intelligence/libero/norm_stats.json").is_file()
        ),
        "public_dataset_metadata_local": (dataset / "meta/info.json").is_file(),
        "normalization_stats": stats.is_file(),
        "training_checkpoint": run.is_dir() and any(p.is_dir() and p.name.isdigit() for p in run.iterdir()),
        "libero_simulator_python": (repo / "examples/libero/.venv/bin/python").is_file(),
    }
    print(f"experiment={data['experiment_id']}")
    print(f"training_mode={training_mode(data)} config={data['train_config']}")
    print(f"commit={commit or 'unavailable'} expected={data['openpi_commit']}")
    print(f"gpu_memory_gib={memory if memory is not None else 'unavailable'}")
    for key, ok in checks.items():
        print(f"{key}={'READY' if ok else 'PENDING'}")
    return checks, memory


def commands(data, stage, checkpoint=None, suite=None, train_steps=None, resume=False):
    repo, _, _, run = paths(data)
    uv = data["uv"]
    config = data["train_config"]
    if stage == "dataset":
        return [uv, "run", str(ROOT / "scripts/download_dataset.py"), "--execute"]
    if stage == "norm":
        return [uv, "run", "scripts/compute_norm_stats.py", "--config-name", config]
    if stage == "train":
        steps = data["train_steps"] if train_steps is None else train_steps
        if not isinstance(steps, int) or steps < 1:
            raise ValueError("Training target steps must be a positive integer")
        command = [
            uv, "run", "scripts/train.py", config,
            "--exp-name", data["experiment_name"],
            "--seed", str(data["seed"]),
            "--num-train-steps", str(steps),
            "--no-wandb-enabled",
        ]
        if resume:
            command.append("--resume")
        return command
    if stage == "serve":
        if not checkpoint:
            raise ValueError("serve requires --checkpoint <trained step directory>")
        return [
            uv, "run", "scripts/serve_policy.py", "--env", "LIBERO",
            "policy:checkpoint", "--policy.config", config, "--policy.dir", checkpoint,
        ]
    if stage == "serve-published":
        return [
            uv, "run", "scripts/serve_policy.py", "--env", "LIBERO",
            "policy:checkpoint", "--policy.config", data.get("published_train_config", "pi0_libero"),
            "--policy.dir", data["published_libero_checkpoint"],
        ]
    if stage in ("eval", "eval-published"):
        if suite not in data["eval_suites"]:
            raise ValueError(f"suite must be one of {data['eval_suites']}")
        return [
            str(repo / "examples/libero/.venv/bin/python"), "examples/libero/main.py",
            "--args.task-suite-name", suite,
            "--args.num-trials-per-task", str(data["eval_trials_per_task"]),
            "--args.replan-steps", str(data["eval_replan_steps"]),
            "--args.seed", str(data["eval_seed"]),
            "--args.video-out-path", str(ROOT / "reports" / "libero-videos" / suite),
        ]
    raise ValueError(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stage",
        choices=("status", "dataset", "norm", "train", "serve", "eval", "serve-published", "eval-published"),
    )
    parser.add_argument("--execute", action="store_true", help="Actually run this stage; otherwise print its command")
    parser.add_argument("--checkpoint", help="Trained checkpoint step directory, for serve")
    parser.add_argument("--suite", help="LIBERO suite, for eval")
    parser.add_argument("--train-steps", type=int, help="Total target training steps; use a small target for a pilot")
    parser.add_argument("--resume", action="store_true", help="Resume the same training run from its latest checkpoint")
    args = parser.parse_args()
    data = load_manifest()
    repo, _, stats, run = paths(data)
    if args.stage == "status":
        status(data)
        return 0
    if args.stage != "train" and (args.train_steps is not None or args.resume):
        raise ValueError("--train-steps and --resume are only valid for the train stage")
    command = commands(data, args.stage, args.checkpoint, args.suite, args.train_steps, args.resume)
    env = os.environ.copy()
    env["OPENPI_DATA_HOME"] = data["openpi_data_home"]
    if data.get("openpi_venv"):
        env["UV_PROJECT_ENVIRONMENT"] = data["openpi_venv"]
    if args.stage == "train":
        # Match the upstream training recommendation on a suitably large GPU.
        env.setdefault("XLA_PYTHON_CLIENT_MEM_FRACTION", "0.9")
    else:
        env.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
    if args.stage in ("eval", "eval-published"):
        env["PYTHONPATH"] = os.pathsep.join(
            [str(repo / "third_party/libero"), str(repo / "packages/openpi-client/src"), env.get("PYTHONPATH", "")]
        )
        env["LIBERO_CONFIG_PATH"] = str(ROOT / "config" / "libero-runtime")
        env.setdefault("MUJOCO_GL", "egl")
    print("cwd:", repo, flush=True)
    print("command:", " ".join(command), flush=True)
    if args.stage in ("serve-published", "eval-published"):
        print("provenance: official published pi0_libero checkpoint; no local training", flush=True)
    if args.stage == "eval-published":
        print("Verify the running policy server was started with serve-published; the client cannot identify it.", flush=True)
    if not args.execute:
        print("DRY RUN: add --execute only on a suitably provisioned machine.")
        return 0
    checks, memory = status(data)
    if not checks["pinned_code"] or not checks["python_environment"]:
        raise RuntimeError("Official code or Python environment is not ready")
    if args.stage == "train":
        if not checks["public_dataset_metadata_local"] or not stats.is_file():
            raise RuntimeError("Dataset and normalization statistics must be ready before training")
        if not checks["base_checkpoint"]:
            raise RuntimeError("The official pi0_base checkpoint must be present before paid training")
        mode = training_mode(data)
        minimum_key = "minimum_lora_finetune_vram_gib" if mode == "lora" else "minimum_full_finetune_vram_gib"
        minimum_gib = data.get(minimum_key, 22.5 if mode == "lora" else 70)
        if memory is None or memory <= minimum_gib:
            raise RuntimeError(f"{mode} fine-tuning requires >{minimum_gib} GiB VRAM; this host is not eligible")
        if args.resume:
            if not checks["training_checkpoint"]:
                raise RuntimeError(f"No training checkpoint to resume in: {run}")
            latest_saved_step = max(int(p.name) for p in run.iterdir() if p.is_dir() and p.name.isdigit())
            target_steps = data["train_steps"] if args.train_steps is None else args.train_steps
            if target_steps <= latest_saved_step:
                raise RuntimeError(f"Target steps {target_steps} must exceed saved step {latest_saved_step}")
        elif run.exists():
            raise RuntimeError(f"Refusing to overwrite existing run: {run}; use --resume only for its own checkpoint")
    elif args.stage == "serve":
        if memory is None or memory <= data["minimum_inference_vram_gib"]:
            raise RuntimeError("Policy serving requires >8 GiB VRAM")
        checkpoint = Path(args.checkpoint).resolve()
        if not (checkpoint / "params").is_dir() or not (checkpoint / "assets").is_dir():
            raise RuntimeError("Checkpoint must contain params/ and assets/")
    elif args.stage == "serve-published":
        if memory is None or memory <= data["minimum_inference_vram_gib"]:
            raise RuntimeError("Policy serving requires >8 GiB VRAM; this host is not eligible")
    elif args.stage in ("eval", "eval-published"):
        if not checks["libero_simulator_python"]:
            raise RuntimeError("LIBERO Python 3.8 simulator environment is not installed")
        if not shutil.which("nvidia-smi"):
            raise RuntimeError("LIBERO EGL evaluation requires an NVIDIA GPU")
    if args.stage == "dataset" and checks["public_dataset_metadata_local"]:
        raise RuntimeError("Dataset metadata already exists; inspect its revision before downloading again")
    if args.stage == "norm" and stats.exists():
        raise RuntimeError(f"Stats already exist; refusing to overwrite: {stats}")
    if args.stage in ("eval", "eval-published"):
        log_dir = ROOT / "reports" / "libero-logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        prefix = "published-pi0-" if args.stage == "eval-published" else ""
        log_path = log_dir / f"{prefix}{args.suite}-{stamp}.log"
        print(f"log: {log_path}", flush=True)
        with log_path.open("x", encoding="utf-8") as log:
            with subprocess.Popen(
                command, cwd=repo, env=env, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1,
            ) as process:
                assert process.stdout is not None
                for line in process.stdout:
                    print(line, end="")
                    log.write(line)
                return process.wait()
    if args.stage == "train":
        log_dir = ROOT / "reports" / "train-logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        log_path = log_dir / f"{data['experiment_name']}-{stamp}.log"
        print(f"log: {log_path}", flush=True)
        with log_path.open("x", encoding="utf-8") as log:
            with subprocess.Popen(command, cwd=repo, env=env, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1) as process:
                assert process.stdout is not None
                for line in process.stdout:
                    print(line, end="")
                    log.write(line)
                return process.wait()
    return subprocess.call(command, cwd=repo, env=env)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
