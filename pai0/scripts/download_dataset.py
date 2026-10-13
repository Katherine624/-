#!/usr/bin/env python3
"""Download the pinned public LIBERO dataset, with a conservative disk guard."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(os.environ.get("PI0_EXPERIMENT_MANIFEST", ROOT / "config/experiment.json"))
DATA = json.loads(MANIFEST.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    from lerobot.common.datasets.lerobot_dataset import HF_LEROBOT_HOME

    target = Path(HF_LEROBOT_HOME) / DATA["dataset_repo_id"]
    print(f"dataset={DATA['dataset_repo_id']} revision={DATA['dataset_revision']}")
    print(f"target={target}")
    if not args.execute:
        print("DRY RUN: add --execute to download the pinned dataset.")
        return
    if target.exists():
        raise RuntimeError(f"Refusing to mix existing data with a pinned snapshot: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    disk_path = target.parent
    # WSL's ext4.vhdx is sparse and df on / can overstate Windows host capacity.
    if os.environ.get("WSL_DISTRO_NAME") and str(target).startswith("/home/") and Path("/mnt/d").exists():
        disk_path = Path("/mnt/d")
    free_gib = shutil.disk_usage(disk_path).free / (1024 ** 3)
    needed_gib = DATA["dataset_published_size_gb"] * 2
    if free_gib < needed_gib:
        raise RuntimeError(
            f"Insufficient free space on {disk_path}: {free_gib:.1f} GiB; "
            f"require >= {needed_gib:.1f} GiB for dataset and temporary files. "
            "Choose a larger storage volume before running this stage."
        )
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=DATA["dataset_repo_id"],
        repo_type="dataset",
        revision=DATA["dataset_revision"],
        local_dir=target,
        max_workers=4,
    )
    if not (target / "meta/info.json").is_file():
        raise RuntimeError("Dataset download returned without meta/info.json")
    print("Dataset snapshot downloaded. Now run normalization; do not edit this snapshot.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
