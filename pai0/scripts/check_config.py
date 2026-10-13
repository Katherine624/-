#!/usr/bin/env python3
"""Validate the selected official openpi configuration without constructing a model."""

import json
import os
from pathlib import Path
import sys

from openpi.training import config as openpi_config
from openpi.training import weight_loaders


ROOT = Path(__file__).resolve().parent.parent
manifest = Path(os.environ.get("PI0_EXPERIMENT_MANIFEST", ROOT / "config/experiment.json"))
DATA = json.loads(manifest.read_text(encoding="utf-8"))
config = openpi_config.get_config(DATA["train_config"])

checks = {
    "original_pi0_not_pi05": config.model.pi05 is False,
    "action_horizon_50": config.model.action_horizon == 50,
    "action_dim_32": config.model.action_dim == 32,
    "public_libero_dataset": config.data.repo_id == DATA["dataset_repo_id"],
    "libero_delta_compatibility": config.data.extra_delta_transform is True,
    "base_pi0_weights": isinstance(config.weight_loader, weight_loaders.CheckpointWeightLoader)
    and config.weight_loader.params_path == "gs://openpi-assets/checkpoints/pi0_base/params",
    "training_steps": config.num_train_steps == DATA["train_steps"],
    "seed": config.seed == DATA["seed"],
    "batch_size_32": config.batch_size == 32,
}
if DATA["train_config"] == "pi0_libero_low_mem_finetune":
    checks.update({
        "lora_mode": DATA.get("training_mode") == "lora",
        "paligemma_lora": config.model.paligemma_variant == "gemma_2b_lora",
        "action_expert_lora": config.model.action_expert_variant == "gemma_300m_lora",
        "frozen_base_parameters": config.freeze_filter is not None,
        "ema_disabled_for_lora": config.ema_decay is None,
    })
else:
    checks["ema_099"] = config.ema_decay == 0.99
for name, passed in checks.items():
    print(f"{name}={'PASS' if passed else 'FAIL'}")
if not all(checks.values()):
    sys.exit(1)
print(f"PASS: {manifest} agrees with the pinned official training configuration.")
