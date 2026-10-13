#!/usr/bin/env python3
"""A CPU-only teaching simulation of pi0's conditional action flow matching.

This trains a tiny MLP on GENERATED numeric data. It does not load pi0, its
pretrained weights, LIBERO demonstrations, images, or a robot simulator. Its
outputs must never be reported as pi0 training or LIBERO evaluation results.
"""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time

import torch
from torch import nn
from torch.nn import functional as F


HORIZON = 50
ACTION_DIM = 7
STATE_DIM = 8
VISUAL_FEATURE_DIM = 8
TASK_COUNT = 4
CONDITION_DIM = STATE_DIM + VISUAL_FEATURE_DIM + TASK_COUNT
ACTION_SIZE = HORIZON * ACTION_DIM


class TinyFlowPolicy(nn.Module):
    def __init__(self, hidden_dim=192):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(CONDITION_DIM + ACTION_SIZE + 1, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, ACTION_SIZE),
        )

    def forward(self, condition, noisy_actions, t):
        batch_size = condition.shape[0]
        features = torch.cat((condition, noisy_actions.reshape(batch_size, -1), t.reshape(batch_size, 1)), dim=1)
        return self.net(features).reshape(batch_size, HORIZON, ACTION_DIM)


class SyntheticDemonstrations:
    """Deterministic teacher: stand-in features -> a 50x7 action chunk."""

    def __init__(self):
        generator = torch.Generator(device="cpu").manual_seed(2609)
        scale = 1 / math.sqrt(CONDITION_DIM)
        self.base = torch.randn(CONDITION_DIM, ACTION_DIM, generator=generator) * scale
        self.trend = torch.randn(CONDITION_DIM, ACTION_DIM, generator=generator) * scale
        self.wave = torch.randn(CONDITION_DIM, ACTION_DIM, generator=generator) * scale

    def sample(self, count, generator):
        state = 2 * torch.rand(count, STATE_DIM, generator=generator) - 1
        visual_features = 2 * torch.rand(count, VISUAL_FEATURE_DIM, generator=generator) - 1
        task_ids = torch.randint(TASK_COUNT, (count,), generator=generator)
        task_instruction = F.one_hot(task_ids, num_classes=TASK_COUNT).float()
        condition = torch.cat((state, visual_features, task_instruction), dim=1)
        phase = torch.linspace(0, 1, HORIZON).reshape(1, HORIZON, 1)
        actions = (
            0.7 * (condition @ self.base)[:, None, :]
            + 0.5 * (condition @ self.trend)[:, None, :] * (phase - 0.5)
            + 0.3 * (condition @ self.wave)[:, None, :] * torch.sin(2 * math.pi * phase)
        )
        return condition, actions


def flow_loss(policy, condition, actions, noise, t):
    # The pinned OpenPI implementation uses x_t=t*noise+(1-t)*actions,
    # target velocity=noise-actions, and an MSE on the predicted velocity.
    x_t = t[:, None, None] * noise + (1 - t[:, None, None]) * actions
    target_velocity = noise - actions
    predicted_velocity = policy(condition, x_t, t)
    return F.mse_loss(predicted_velocity, target_velocity)


@torch.no_grad()
def sample_actions(policy, condition, initial_noise, integration_steps=10):
    actions = initial_noise.clone()
    dt = -1.0 / integration_steps
    for step in range(integration_steps):
        t = torch.full((condition.shape[0],), 1.0 - step / integration_steps)
        actions = actions + dt * policy(condition, actions, t)
    return actions


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.steps < 1 or args.batch_size < 1:
        parser.error("--steps and --batch-size must be positive")

    torch.set_num_threads(2)
    torch.manual_seed(args.seed)
    train_generator = torch.Generator(device="cpu").manual_seed(args.seed + 1)
    validation_generator = torch.Generator(device="cpu").manual_seed(args.seed + 2)
    demonstrations = SyntheticDemonstrations()
    policy = TinyFlowPolicy().cpu()
    optimizer = torch.optim.AdamW(policy.parameters(), lr=0.001)
    parameter_count = sum(parameter.numel() for parameter in policy.parameters())

    validation_condition, validation_actions = demonstrations.sample(128, validation_generator)
    validation_noise = torch.randn(validation_actions.shape, generator=validation_generator)
    validation_t = torch.linspace(0.05, 0.99, validation_condition.shape[0])
    with torch.no_grad():
        initial_flow_mse = float(flow_loss(policy, validation_condition, validation_actions,
                                           validation_noise, validation_t))
        initial_prediction = sample_actions(policy, validation_condition, validation_noise)
        initial_action_mse = float(F.mse_loss(initial_prediction, validation_actions))

    trace = [{"step": 0, "train_flow_mse": None, "validation_flow_mse": initial_flow_mse}]
    print("TEACHING SIMULATION ONLY: synthetic data, tiny model, no pi0/LIBERO training", flush=True)
    print(f"steps={args.steps} batch={args.batch_size} parameters={parameter_count}", flush=True)
    started = time.monotonic()
    for step in range(1, args.steps + 1):
        condition, actions = demonstrations.sample(args.batch_size, train_generator)
        noise = torch.randn(actions.shape, generator=train_generator)
        t = torch.distributions.Beta(1.5, 1.0).sample((args.batch_size,)) * 0.999 + 0.001
        optimizer.zero_grad(set_to_none=True)
        loss = flow_loss(policy, condition, actions, noise, t)
        loss.backward()
        optimizer.step()
        if step == 1 or step % 25 == 0 or step == args.steps:
            with torch.no_grad():
                validation_loss = float(flow_loss(policy, validation_condition, validation_actions,
                                                  validation_noise, validation_t))
            trace.append({"step": step, "train_flow_mse": float(loss),
                          "validation_flow_mse": validation_loss})
            print(f"step={step:4d} train_flow_mse={float(loss):.4f} "
                  f"validation_flow_mse={validation_loss:.4f}", flush=True)

    elapsed_seconds = time.monotonic() - started
    policy.eval()
    with torch.no_grad():
        final_flow_mse = float(flow_loss(policy, validation_condition, validation_actions,
                                         validation_noise, validation_t))
        final_prediction = sample_actions(policy, validation_condition, validation_noise)
        final_action_mse = float(F.mse_loss(final_prediction, validation_actions))

    root = Path(__file__).resolve().parents[2]
    output_dir = args.output_dir or (root / "examples" / "toy-flow" / "runs"
                                     / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    output_dir.mkdir(parents=True, exist_ok=False)
    trace_path = output_dir / "loss_trace.csv"
    with trace_path.open("x", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=("step", "train_flow_mse", "validation_flow_mse"))
        writer.writeheader()
        writer.writerows(trace)

    checkpoint_path = output_dir / "tiny_flow_checkpoint.pt"
    torch.save({"model_state_dict": policy.state_dict(), "seed": args.seed,
                "steps": args.steps, "action_horizon": HORIZON, "action_dim": ACTION_DIM}, checkpoint_path)
    restored = TinyFlowPolicy().cpu()
    restored.load_state_dict(torch.load(checkpoint_path, map_location="cpu", weights_only=True)["model_state_dict"])
    restored.eval()
    with torch.no_grad():
        restored_prediction = sample_actions(restored, validation_condition, validation_noise)
    if not torch.allclose(final_prediction, restored_prediction, atol=1e-6):
        raise RuntimeError("Saved checkpoint failed the reload consistency check")

    action_path = output_dir / "example_actions.csv"
    with action_path.open("x", newline="", encoding="utf-8") as target:
        columns = ["time_step"] + [f"true_a{i}" for i in range(ACTION_DIM)] + [
            f"before_a{i}" for i in range(ACTION_DIM)] + [f"after_a{i}" for i in range(ACTION_DIM)]
        writer = csv.writer(target)
        writer.writerow(columns)
        for step in range(HORIZON):
            writer.writerow([step, *validation_actions[0, step].tolist(),
                             *initial_prediction[0, step].tolist(), *final_prediction[0, step].tolist()])

    report = {
        "provenance": "TOY_EDUCATIONAL_SIMULATION_NOT_PI0_NOT_LIBERO",
        "data": "generated numeric visual features, task one-hot vectors, state, and 50x7 action chunks",
        "model": "tiny conditional MLP, not PaliGemma or the pi0 action expert",
        "device": "CPU",
        "seed": args.seed,
        "steps": args.steps,
        "batch_size": args.batch_size,
        "trainable_parameters": parameter_count,
        "flow_target": "x_t=t*noise+(1-t)*actions; velocity=noise-actions; MSE",
        "initial_validation_flow_mse": initial_flow_mse,
        "final_validation_flow_mse": final_flow_mse,
        "initial_generated_action_mse": initial_action_mse,
        "final_generated_action_mse": final_action_mse,
        "elapsed_seconds": elapsed_seconds,
        "checkpoint_sha256": sha256(checkpoint_path),
        "checkpoint_reload_verified": True,
        "not_a_libero_success_rate": True,
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"output={output_dir}")
    print(f"validation_flow_mse: {initial_flow_mse:.4f} -> {final_flow_mse:.4f}")
    print(f"generated_action_mse: {initial_action_mse:.4f} -> {final_action_mse:.4f}")
    print("checkpoint_reload_verified=True; no cloud expense; not a LIBERO success rate")


if __name__ == "__main__":
    main()
