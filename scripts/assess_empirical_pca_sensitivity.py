"""Test whether PCA improves empirical recurrent-state reproducibility."""

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import (
    adjusted_rand_index,
    bandpass_signals,
    cluster_connectivity_states,
    load_single_subject,
    windowed_functional_connectivity,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = ROOT / "upstream" / "competitive-cooperative-hopf" / "data" / "matlab" / "single"
OUTPUT_DIRECTORY = ROOT / "results" / "empirical_recurrent_state_pca_sensitivity"
FIGURE_PATH = ROOT / "figures" / "empirical_recurrent_state_pca_sensitivity.png"
WINDOW_SIZES = (30, 50, 80)
N_STATES = tuple(range(2, 7))
VARIANCE_THRESHOLDS = (0.50, 0.70, 0.80, 0.90)
SEEDS = tuple(range(42, 62))
STEP = 5
TR = 0.72


def pca_scores(features: np.ndarray, threshold: float) -> tuple[np.ndarray, int, float]:
    centered = features - features.mean(axis=0, keepdims=True)
    left, singular, _ = np.linalg.svd(centered, full_matrices=False)
    variance = singular**2
    cumulative = np.cumsum(variance) / variance.sum()
    components = int(np.searchsorted(cumulative, threshold) + 1)
    return left[:, :components] * singular[:components], components, float(cumulative[components - 1])


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    filtered = bandpass_signals(data.bold, TR)
    rows = []
    for window_size in WINDOW_SIZES:
        windowed = windowed_functional_connectivity(filtered, window_size=window_size, step=STEP)
        fisher = np.arctanh(np.clip(windowed.features, -0.999999, 0.999999))
        for threshold in VARIANCE_THRESHOLDS:
            scores, components, retained = pca_scores(fisher, threshold)
            for n_states in N_STATES:
                labelings = [
                    cluster_connectivity_states(scores, n_states=n_states, seed=seed)[0]
                    for seed in SEEDS
                ]
                agreements = [
                    adjusted_rand_index(labelings[first], labelings[second])
                    for first in range(len(labelings))
                    for second in range(first + 1, len(labelings))
                ]
                occupancies = [
                    np.bincount(labels, minlength=n_states).min() / labels.size
                    for labels in labelings
                ]
                rows.append({
                    "window_size": window_size,
                    "window_seconds": window_size * TR,
                    "variance_threshold": threshold,
                    "retained_components": components,
                    "actual_variance_retained": retained,
                    "n_states": n_states,
                    "mean_seed_stability_ari": float(np.mean(agreements)),
                    "minimum_seed_stability_ari": float(np.min(agreements)),
                    "mean_minimum_occupancy": float(np.mean(occupancies)),
                })

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIRECTORY / "solutions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    best = sorted(rows, key=lambda row: row["mean_seed_stability_ari"], reverse=True)[:10]
    summary = {
        "method": {
            "variance_thresholds": list(VARIANCE_THRESHOLDS),
            "window_sizes": list(WINDOW_SIZES),
            "state_counts": list(N_STATES),
            "seeds": list(SEEDS),
            "model_data_used": False,
        },
        "best_ten_by_mean_seed_stability": best,
        "selection_status": "sensitivity assessment; no PCA threshold or state definition frozen",
    }
    (OUTPUT_DIRECTORY / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    figure, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True, constrained_layout=True)
    colors = {0.50: "#2E5D7B", 0.70: "#4F8A70", 0.80: "#A77A2D", 0.90: "#B23A48"}
    for axis, window_size in zip(axes, WINDOW_SIZES, strict=True):
        for threshold in VARIANCE_THRESHOLDS:
            selected = [row for row in rows if row["window_size"] == window_size and row["variance_threshold"] == threshold]
            axis.plot(N_STATES, [row["mean_seed_stability_ari"] for row in selected], marker="o", color=colors[threshold], label=f"{int(threshold * 100)}% variance")
        axis.set_title(f"Window {window_size} ({window_size * TR:.1f} s)", fontweight="bold")
        axis.set_xlabel("Number of states")
        axis.set_xticks(N_STATES)
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Mean pairwise seed ARI")
    axes[-1].legend(frameon=False, fontsize=8)
    figure.suptitle("PCA sensitivity of empirical clustering stability", fontweight="bold")
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
