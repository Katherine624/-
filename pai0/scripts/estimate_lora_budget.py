#!/usr/bin/env python3
"""Estimate whether a measured LoRA run fits a user-supplied rental budget.

This is a planning aid, not a billing limit or an automatic shutdown mechanism.
Use the actual price and steady-state seconds per step from the paid pilot.
"""

import argparse
import math


def estimate(budget, spent, hourly_price, seconds_per_step, current_step, target_step,
             future_nontraining_hours, reserve):
    if any(value < 0 for value in (budget, spent, hourly_price, seconds_per_step,
                                    current_step, target_step, future_nontraining_hours, reserve)):
        raise ValueError("Inputs cannot be negative")
    if hourly_price == 0 or seconds_per_step == 0:
        raise ValueError("Hourly price and seconds per step must be positive measured values")
    if target_step < current_step:
        raise ValueError("Target step must not be below the current step")
    remaining_steps = target_step - current_step
    training_hours = remaining_steps * seconds_per_step / 3600
    future_nontraining_cost = future_nontraining_hours * hourly_price
    projected_total = spent + training_hours * hourly_price + future_nontraining_cost + reserve
    affordable_yuan = budget - spent - future_nontraining_cost - reserve
    affordable_steps = max(0, math.floor(affordable_yuan / hourly_price * 3600 / seconds_per_step))
    return {
        "remaining_steps": remaining_steps,
        "training_hours": training_hours,
        "projected_total_yuan": projected_total,
        "affordable_additional_steps": affordable_steps,
        "fits_budget": projected_total <= budget,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget-yuan", type=float, default=100)
    parser.add_argument("--already-spent-yuan", type=float, required=True)
    parser.add_argument("--hourly-yuan", type=float, required=True)
    parser.add_argument("--seconds-per-step", type=float, required=True)
    parser.add_argument("--current-step", type=int, required=True)
    parser.add_argument("--target-step", type=int, default=30000)
    parser.add_argument("--future-nontraining-hours", type=float, required=True,
                        help="Estimated evaluation, transfer, and shutdown time on the same billed instance")
    parser.add_argument("--reserve-yuan", type=float, default=15,
                        help="Extra safety allowance beyond estimated nontraining time")
    args = parser.parse_args()
    result = estimate(args.budget_yuan, args.already_spent_yuan, args.hourly_yuan,
                      args.seconds_per_step, args.current_step, args.target_step,
                      args.future_nontraining_hours, args.reserve_yuan)
    for key, value in result.items():
        print(f"{key}={value}")
    print("WARNING: estimate only. Include storage/network charges, use the provider's own shutdown timer, "
          "and verify the live bill before continuing.")
    return 0 if result["fits_budget"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
