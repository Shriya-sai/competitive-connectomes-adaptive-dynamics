"""Validate the released reversal task using neutral computational controls."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation.reversal_task import (
    aligned_strategy_curve,
    load_released_schedule,
    simulate_q_learner,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_FILE = ROOT / "data/public_reversal_behavior/Sub04_RL_Go_NoGo_results_all.txt"
HUMAN_RESULTS = ROOT / "results/public_reversal_behavior/summary.json"
OUTPUT = ROOT / "results/reversal_task_validation"
FIGURE = ROOT / "figures/reversal_task_validation.png"


def mean_q_curve(schedule, learning_rate: float, inverse_temperature: float,
                 seeds: range) -> np.ndarray:
    curves = [
        simulate_q_learner(schedule, learning_rate, inverse_temperature, seed)["aligned_curve"]
        for seed in seeds
    ]
    return np.mean(curves, axis=0)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    schedule = load_released_schedule(SCHEDULE_FILE)
    human = json.loads(HUMAN_RESULTS.read_text())
    human_curve = np.asarray(human["group_mean_curve"])

    search_seeds = range(200, 300)
    learning_rates = np.linspace(0.05, 1.00, 20)
    inverse_temperatures = np.linspace(0.5, 8.0, 16)
    records = []
    best = None
    for learning_rate in learning_rates:
        for inverse_temperature in inverse_temperatures:
            curve = mean_q_curve(
                schedule, float(learning_rate), float(inverse_temperature), search_seeds
            )
            rmse = float(np.sqrt(np.mean((curve - human_curve) ** 2)))
            record = {
                "learning_rate": float(learning_rate),
                "inverse_temperature": float(inverse_temperature),
                "human_curve_rmse": rmse,
            }
            records.append(record)
            if best is None or rmse < best[0]:
                best = (rmse, float(learning_rate), float(inverse_temperature))

    assert best is not None
    _, best_alpha, best_beta = best
    confirmation_seeds = range(1000, 1500)
    q_curves = np.asarray([
        simulate_q_learner(schedule, best_alpha, best_beta, seed)["aligned_curve"]
        for seed in confirmation_seeds
    ])
    q_mean = q_curves.mean(axis=0)
    q_sem = q_curves.std(axis=0, ddof=1) / np.sqrt(len(q_curves))

    random_curves = []
    for seed in confirmation_seeds:
        rng = np.random.default_rng(seed)
        actions = rng.integers(0, 2, schedule.n_trials)
        correct = (actions == schedule.correct_strategy_action).astype(float)
        random_curves.append(aligned_strategy_curve(correct, schedule))
    random_mean = np.mean(random_curves, axis=0)

    metrics = {
        "best_learning_rate": best_alpha,
        "best_inverse_temperature": best_beta,
        "search_seed_count": len(search_seeds),
        "independent_confirmation_seed_count": len(confirmation_seeds),
        "human_curve_rmse_confirmation": float(np.sqrt(np.mean((q_mean - human_curve) ** 2))),
        "random_mean_accuracy": float(random_mean.mean()),
        "q_pre_reversal_last_10": float(q_mean[10:20].mean()),
        "q_immediate_post_first_2": float(q_mean[20:22].mean()),
        "q_late_post_last_10": float(q_mean[30:40].mean()),
        "human_pre_reversal_last_10": float(human_curve[10:20].mean()),
        "human_immediate_post_first_2": float(human_curve[20:22].mean()),
        "human_late_post_last_10": float(human_curve[30:40].mean()),
    }
    gates = {
        "random_is_chance": abs(metrics["random_mean_accuracy"] - 0.5) < 0.02,
        "q_learns_before_reversal": metrics["q_pre_reversal_last_10"] > 0.65,
        "q_declines_immediately": metrics["q_immediate_post_first_2"] < 0.50,
        "q_recovers_after_reversal": (
            metrics["q_late_post_last_10"] > metrics["q_immediate_post_first_2"] + 0.20
        ),
    }

    with (OUTPUT / "parameter_search.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    summary = {
        "design": {
            "task_schedule": "released Sub04 experimental schedule; identical across participants",
            "model": "two-cue, two-action model-free Q learner",
            "parameter_selection": "RMSE to the frozen 40-point human group curve",
            "selection_and_confirmation_seeds_disjoint": True,
        },
        "metrics": metrics,
        "validation_gates": gates,
        "all_gates_passed": all(gates.values()),
        "scope": "Task and neutral-baseline validation; no Hopf network used.",
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    x = np.r_[np.arange(-20, 0), np.arange(1, 21)]
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    ax.plot(x, human_curve, color="#2E5D7B", linewidth=2.7, label="Humans (n=32)")
    ax.plot(x, q_mean, color="#B85252", linewidth=2.3, label="Neutral Q learner")
    ax.fill_between(x, q_mean - q_sem, q_mean + q_sem,
                    color="#B85252", alpha=0.18, linewidth=0)
    ax.plot(x, random_mean, color="#8A929A", linewidth=1.5, label="Random control")
    ax.axvline(0, color="#A77A2D", linestyle="--", linewidth=1.7)
    ax.axhline(0.5, color="#68717A", linestyle=":", linewidth=1.2)
    ax.set(xlabel="Trials relative to reversal", ylabel="Probability of correct strategy",
           ylim=(0, 1.02), title="Exact released task: neutral-model validation")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=180)
    plt.close(fig)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to {OUTPUT}")
    print(f"Saved figure to {FIGURE}")
    if not summary["all_gates_passed"]:
        raise RuntimeError("One or more task-validation gates failed")


if __name__ == "__main__":
    main()
