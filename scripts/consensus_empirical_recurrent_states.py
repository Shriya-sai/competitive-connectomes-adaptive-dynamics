"""Test empirical state discreteness with consensus clustering and block deletion."""

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

from luppi_recreation import (
    adjusted_rand_index,
    bandpass_signals,
    cluster_connectivity_states,
    load_single_subject,
    windowed_functional_connectivity,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = ROOT / "upstream" / "competitive-cooperative-hopf" / "data" / "matlab" / "single"
OUTPUT_DIRECTORY = ROOT / "results" / "empirical_recurrent_state_consensus"
FIGURE_PATH = ROOT / "figures" / "empirical_recurrent_state_consensus.png"
WINDOW_SIZES = (30, 50, 80)
N_STATES = tuple(range(2, 11))
SEEDS = tuple(range(100, 200))
BOOTSTRAP_SEEDS = tuple(range(12))
PCA_VARIANCE = 0.80
DELETED_FRACTION = 0.20
STEP = 5
TR = 0.72


def pca_scores(features: np.ndarray) -> tuple[np.ndarray, int, float]:
    centered = features - features.mean(axis=0, keepdims=True)
    left, singular, _ = np.linalg.svd(centered, full_matrices=False)
    variance = singular**2
    cumulative = np.cumsum(variance) / variance.sum()
    components = int(np.searchsorted(cumulative, PCA_VARIANCE) + 1)
    return left[:, :components] * singular[:components], components, float(cumulative[components - 1])


def consensus_labels(scores: np.ndarray, n_states: int) -> tuple[np.ndarray, float]:
    labelings = [
        cluster_connectivity_states(scores, n_states=n_states, seed=seed)[0]
        for seed in SEEDS
    ]
    coassignment = np.mean(
        [labels[:, None] == labels[None, :] for labels in labelings], axis=0
    )
    distance = np.clip(1 - coassignment, 0, 1)
    np.fill_diagonal(distance, 0)
    hierarchy = linkage(squareform(distance, checks=False), method="average")
    consensus = fcluster(hierarchy, t=n_states, criterion="maxclust") - 1
    within = []
    between = []
    for first in range(consensus.size):
        for second in range(first + 1, consensus.size):
            target = within if consensus[first] == consensus[second] else between
            target.append(coassignment[first, second])
    contrast = float(np.mean(within) - np.mean(between))
    return consensus, contrast


def best_multistart(scores: np.ndarray, n_states: int, seeds: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    best = None
    for seed in seeds:
        labels, centroids = cluster_connectivity_states(scores, n_states=n_states, seed=seed)
        inertia = float(np.sum((scores - centroids[labels]) ** 2))
        if best is None or inertia < best[0]:
            best = (inertia, labels, centroids)
    return best[1], best[2]


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    filtered = bandpass_signals(data.bold, TR)
    rows = []
    bootstrap_rows = []
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    for window_size in WINDOW_SIZES:
        windowed = windowed_functional_connectivity(filtered, window_size=window_size, step=STEP)
        fisher = np.arctanh(np.clip(windowed.features, -0.999999, 0.999999))
        scores, components, variance_retained = pca_scores(fisher)
        delete_size = int(round(scores.shape[0] * DELETED_FRACTION))
        deletion_starts = np.linspace(0, scores.shape[0] - delete_size, len(BOOTSTRAP_SEEDS), dtype=int)

        for n_states in N_STATES:
            consensus, contrast = consensus_labels(scores, n_states)
            occupancy = np.bincount(consensus, minlength=n_states) / consensus.size
            block_aris = []
            for bootstrap_index, start in enumerate(deletion_starts):
                retained = np.ones(scores.shape[0], dtype=bool)
                retained[start : start + delete_size] = False
                _, centroids = best_multistart(
                    scores[retained], n_states, tuple(range(300 + bootstrap_index * 20, 320 + bootstrap_index * 20))
                )
                assigned = np.argmin(
                    np.sum((scores[retained, None, :] - centroids[None, :, :]) ** 2, axis=2),
                    axis=1,
                )
                ari = adjusted_rand_index(consensus[retained], assigned)
                block_aris.append(ari)
                bootstrap_rows.append({
                    "window_size": window_size,
                    "n_states": n_states,
                    "deleted_block_index": bootstrap_index,
                    "deleted_start_window": int(start),
                    "deleted_windows": delete_size,
                    "retained_ari_vs_full_consensus": ari,
                })
            rows.append({
                "window_size": window_size,
                "window_seconds": window_size * TR,
                "n_states": n_states,
                "retained_pca_components": components,
                "variance_retained": variance_retained,
                "consensus_contrast": contrast,
                "minimum_state_occupancy": float(occupancy.min()),
                "mean_block_deletion_ari": float(np.mean(block_aris)),
                "minimum_block_deletion_ari": float(np.min(block_aris)),
                "maximum_block_deletion_ari": float(np.max(block_aris)),
            })
            np.savez_compressed(
                OUTPUT_DIRECTORY / f"window_{window_size}_states_{n_states}.npz",
                labels=consensus,
                centers=windowed.centers,
                window_size=window_size,
                n_states=n_states,
                pca_variance=PCA_VARIANCE,
            )

    with (OUTPUT_DIRECTORY / "solutions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (OUTPUT_DIRECTORY / "block_deletions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(bootstrap_rows[0]))
        writer.writeheader()
        writer.writerows(bootstrap_rows)

    robust = [
        row for row in rows
        if row["mean_block_deletion_ari"] >= 0.80
        and row["minimum_block_deletion_ari"] >= 0.60
        and row["minimum_state_occupancy"] >= 0.05
        and row["consensus_contrast"] >= 0.50
    ]
    summary = {
        "method": {
            "consensus_initializations": len(SEEDS),
            "pca_variance_target": PCA_VARIANCE,
            "contiguous_block_deletions": len(BOOTSTRAP_SEEDS),
            "fraction_deleted_each_time": DELETED_FRACTION,
            "multistarts_per_block_deletion": 20,
            "model_data_used": False,
        },
        "robustness_rule": "mean block ARI >= 0.80, minimum block ARI >= 0.60, occupancy >= 5%, consensus contrast >= 0.50",
        "robust_solutions": robust,
        "number_robust": len(robust),
        "selection_status": "no state definition frozen unless a solution passes all robustness gates",
    }
    (OUTPUT_DIRECTORY / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.3), constrained_layout=True)
    colors = {30: "#2E5D7B", 50: "#A77A2D", 80: "#B23A48"}
    for window_size in WINDOW_SIZES:
        selected = [row for row in rows if row["window_size"] == window_size]
        axes[0].plot(N_STATES, [row["mean_block_deletion_ari"] for row in selected], marker="o", color=colors[window_size], label=f"{window_size} samples")
        axes[1].plot(N_STATES, [row["consensus_contrast"] for row in selected], marker="o", color=colors[window_size])
    axes[0].axhline(0.80, linestyle="--", color="#555555", linewidth=1)
    axes[1].axhline(0.50, linestyle="--", color="#555555", linewidth=1)
    axes[0].set_title("Stability after deleting 20% time blocks", fontweight="bold")
    axes[0].set_ylabel("Mean ARI versus full consensus")
    axes[0].legend(frameon=False)
    axes[1].set_title("Consensus discreteness", fontweight="bold")
    axes[1].set_ylabel("Within-minus-between co-assignment")
    for axis in axes:
        axis.set_xlabel("Number of states")
        axis.set_xticks(N_STATES)
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Consensus and block-stability test of empirical states", fontweight="bold")
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
