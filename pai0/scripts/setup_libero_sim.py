#!/usr/bin/env python3
"""Prepare the separate LIBERO Python 3.8 simulator environment; dry-run by default."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(os.environ.get("PI0_EXPERIMENT_MANIFEST", ROOT / "config/experiment.json"))
DATA = json.loads(MANIFEST.read_text(encoding="utf-8"))
REPO = Path(DATA["openpi_repo"])
VENV = REPO / "examples/libero/.venv"
CONFIG_DIR = ROOT / "config/libero-runtime"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    uv = DATA["uv"]
    commands = [
        [uv, "venv", "--python", "3.8", str(VENV)],
        [
            uv, "pip", "sync", "examples/libero/requirements.txt",
            "third_party/libero/requirements.txt", "--python", str(VENV / "bin/python"),
            "--extra-index-url", "https://download.pytorch.org/whl/cu113",
            "--index-strategy=unsafe-best-match",
        ],
        [uv, "pip", "install", "-e", "packages/openpi-client", "-e", "third_party/libero",
         "--python", str(VENV / "bin/python")],
    ]
    for command in commands:
        print(" ".join(command), flush=True)
    print(f"LIBERO_CONFIG_PATH={CONFIG_DIR}", flush=True)
    if not args.execute:
        print("DRY RUN: add --execute to install the simulator dependencies.")
        return
    if VENV.exists():
        raise RuntimeError(f"Refusing to alter existing simulator venv: {VENV}")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    if commit != DATA["openpi_commit"]:
        raise RuntimeError(f"Openpi commit mismatch: {commit}")
    for command in commands:
        subprocess.run(command, cwd=REPO, check=True)
    benchmark_root = REPO / "third_party/libero/libero/libero"
    settings = {
        "benchmark_root": str(benchmark_root),
        "bddl_files": str(benchmark_root / "bddl_files"),
        "init_states": str(benchmark_root / "init_files"),
        "datasets": str(benchmark_root.parent / "datasets"),
        "assets": str(benchmark_root / "assets"),
    }
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "config.yaml").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print("Simulator environment prepared; GPU/EGL runtime still requires separate verification.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
