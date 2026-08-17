"""Stress-test recurrent-state recovery across noise, duration and window size."""

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import (
    adjusted_rand_index,
    cluster_connectivity_states,
    windowed_functional_connectivity,
)
from validate_recurrent_states import synthetic_switching_signals


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "results" / "recurrent_state_stress_test"
FIGURE_PATH = ROOT / "figures" / "recurrent_state_stress_test.png"

NOISE_SCALES = (0.25, 0.45, 0.75, 1.00, 1.50, 2.00)
SEGMENT_LENGTHS = (80, 120, 200, 300)
WINDOW_SIZES = (30, 50, 80, 120)
SEEDS = tuple(range(42, 50))
STEP = 5


def score_condition(
    *, seed: int, noise_scale: float, segment_length: int, window_size: int
) -> dict[str, float | int]:
    signals, point_truth = synthetic_switching_signals(
        seed, segment_length=segment_length, noise_scale=noise_scale
    )
    windowed = windowed_functional_connectivity(
        signals, window_size=window_size, step=STEP
    )
    labels, _ = cluster_connectivity_states(
        windowed.features, n_states=2, seed=seed
    )
    truth = np.empty(labels.size, dtype=int)
    pure = np.ones(labels.size, dtype=bool)
    for index, start in enumerate(windowed.starts):
        contained = point_truth[start : start + window_size]
        pure[index] = np.all(contained == contained[0])
        truth[index] = contained[contained.size // 2]

    # If a window is longer than a state, there may be no unambiguous windows.
    if pure.sum() < 2 or np.unique(truth[pure]).size < 2:
        accuracy = np.nan
        ari = np.nan
    else:
        direct = np.mean(labels[pure] == truth[pure])
        flipped = np.mean((1 - labels[pure]) == truth[pure])
        accuracy = float(max(direct, flipped))
        ari = adjusted_rand_index(truth[pure], labels[pure])
    return {
        "seed": seed,
        "noise_scale": noise_scale,
        "segment_length": segment_length,
        "window_size": window_size,
        "window_to_state_ratio": window_size / segment_length,
        "total_windows": int(labels.size),
        "pure_windows": int(pure.sum()),
        "pure_window_fraction": float(pure.mean()),
        "accuracy": accuracy,
        "adjusted_rand_index": ari,
    }


def main() -> None:
    rows = []
    for segment_length in SEGMENT_LENGTHS:
        for window_size in WINDOW_SIZES:
            for noise_scale in NOISE_SCALES:
                for seed in SEEDS:
                    rows.append(
                        score_condition(
                            seed=seed,
                            noise_scale=noise_scale,
                            segment_length=segment_length,
                            window_size=window_size,
                        )
                    )

    grouped = []
    for segment_length in SEGMENT_LENGTHS:
        for window_size in WINDOW_SIZES:
            for noise_scale in NOISE_SCALES:
                selected = [
                    row for row in rows
                    if row["segment_length"] == segment_length
                    and row["window_size"] == window_size
                    and row["noise_scale"] == noise_scale
                ]
                accuracies = np.array([row["accuracy"] for row in selected], dtype=float)
                aris = np.array([row["adjusted_rand_index"] for row in selected], dtype=float)
                grouped.append(
                    {
                        "segment_length": segment_length,
                        "window_size": window_size,
                        "noise_scale": noise_scale,
                        "window_to_state_ratio": window_size / segment_length,
                        "mean_accuracy": float(np.nanmean(accuracies)) if np.any(np.isfinite(accuracies)) else None,
                        "minimum_accuracy": float(np.nanmin(accuracies)) if np.any(np.isfinite(accuracies)) else None,
                        "mean_adjusted_rand_index": float(np.nanmean(aris)) if np.any(np.isfinite(aris)) else None,
                        "mean_pure_window_fraction": float(np.mean([row["pure_window_fraction"] for row in selected])),
                        "valid_repetitions": int(np.isfinite(accuracies).sum()),
                    }
                )

    valid = [group for group in grouped if group["mean_accuracy"] is not None]
    reliable = [
        group for group in valid
        if group["mean_accuracy"] >= 0.90
        and group["mean_adjusted_rand_index"] >= 0.80
        and group["mean_pure_window_fraction"] >= 0.25
    ]
    summary = {
        "design": {
            "noise_scales": list(NOISE_SCALES),
            "segment_lengths": list(SEGMENT_LENGTHS),
            "window_sizes": list(WINDOW_SIZES),
            "seeds": list(SEEDS),
            "step": STEP,
            "conditions": len(grouped),
            "runs": len(rows),
        },
        "reliability_rule": (
            "mean accuracy >= 0.90, mean ARI >= 0.80, and at least 25% "
            "of windows do not cross a true transition"
        ),
        "reliable_conditions": len(reliable),
        "valid_conditions": len(valid),
        "grouped_results": grouped,
    }

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIRECTORY / "runs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUTPUT_DIRECTORY / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    figure, axes = plt.subplots(
        len(SEGMENT_LENGTHS), len(WINDOW_SIZES),
        figsize=(13, 10), sharex=True, sharey=True, constrained_layout=True
    )
    for row_index, segment_length in enumerate(SEGMENT_LENGTHS):
        for column_index, window_size in enumerate(WINDOW_SIZES):
            axis = axes[row_index, column_index]
            selected = [
                group for group in grouped
                if group["segment_length"] == segment_length
                and group["window_size"] == window_size
            ]
            values = [
                np.nan if group["mean_accuracy"] is None else group["mean_accuracy"]
                for group in selected
            ]
            axis.plot(NOISE_SCALES, values, marker="o", color="#2E5D7B")
            axis.axhline(0.90, color="#B23A48", linestyle="--", linewidth=1)
            axis.set_ylim(0.45, 1.02)
            axis.set_title(
                f"State duration {segment_length}; window {window_size}", fontsize=9
            )
            if row_index == len(SEGMENT_LENGTHS) - 1:
                axis.set_xlabel("Noise scale")
            if column_index == 0:
                axis.set_ylabel("Mean accuracy")
            axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle(
        "Recurrent-state recovery under noise and timescale pressure\n"
        "Dashed line = 90% accuracy criterion",
        fontweight="bold",
    )
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps({key: value for key, value in summary.items() if key != "grouped_results"}, indent=2))
    print(f"Saved run-level results to: {OUTPUT_DIRECTORY / 'runs.csv'}")
    print(f"Saved summary to: {OUTPUT_DIRECTORY / 'summary.json'}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
