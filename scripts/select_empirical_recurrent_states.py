"""Select stable recurrent-state candidates using empirical BOLD only."""

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import squareform, pdist

from luppi_recreation import (
    adjusted_rand_index,
    bandpass_signals,
    cluster_connectivity_states,
    load_single_subject,
    windowed_functional_connectivity,
)


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = ROOT / "upstream" / "competitive-cooperative-hopf"
DATA_DIRECTORY = UPSTREAM_ROOT / "data" / "matlab" / "single"
OUTPUT_DIRECTORY = ROOT / "results" / "empirical_recurrent_state_selection"
FIGURE_PATH = ROOT / "figures" / "empirical_recurrent_state_selection.png"

TR = 0.72
WINDOW_SIZES = (30, 50, 80)
N_STATES = tuple(range(2, 7))
SEEDS = tuple(range(42, 62))
STEP = 5


def silhouette_score(distances: np.ndarray, labels: np.ndarray) -> float:
    """Mean silhouette using a precomputed pairwise-distance matrix."""

    labels = np.asarray(labels)
    values = np.zeros(labels.size, dtype=float)
    states = np.unique(labels)
    for index in range(labels.size):
        same = labels == labels[index]
        same[index] = False
        if not np.any(same):
            values[index] = 0.0
            continue
        within = distances[index, same].mean()
        between = min(
            distances[index, labels == state].mean()
            for state in states
            if state != labels[index]
        )
        values[index] = (between - within) / max(within, between)
    return float(values.mean())


def run_lengths(labels: np.ndarray) -> np.ndarray:
    changes = np.flatnonzero(np.diff(labels) != 0) + 1
    return np.diff(np.r_[0, changes, labels.size])


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    filtered = bandpass_signals(data.bold, TR)
    records = []
    representative_files = []
    representative_sequences: dict[tuple[int, int], dict[str, np.ndarray]] = {}

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for window_size in WINDOW_SIZES:
        windowed = windowed_functional_connectivity(
            filtered, window_size=window_size, step=STEP
        )
        fisher_features = np.arctanh(np.clip(windowed.features, -0.999999, 0.999999))
        distances = squareform(pdist(fisher_features, metric="euclidean"))

        for n_states in N_STATES:
            solutions = []
            for seed in SEEDS:
                labels, centroids = cluster_connectivity_states(
                    fisher_features, n_states=n_states, seed=seed
                )
                occupancy = np.bincount(labels, minlength=n_states) / labels.size
                lengths = run_lengths(labels)
                solutions.append(
                    {
                        "seed": seed,
                        "labels": labels,
                        "centroids": centroids,
                        "silhouette": silhouette_score(distances, labels),
                        "minimum_occupancy": float(occupancy.min()),
                        "switch_rate": float(np.mean(np.diff(labels) != 0)),
                        "median_run_windows": float(np.median(lengths)),
                    }
                )

            agreement = np.eye(len(solutions))
            for first in range(len(solutions)):
                for second in range(first + 1, len(solutions)):
                    value = adjusted_rand_index(
                        solutions[first]["labels"], solutions[second]["labels"]
                    )
                    agreement[first, second] = agreement[second, first] = value
            mean_agreement = (agreement.sum(axis=1) - 1) / (len(solutions) - 1)
            representative_index = int(
                max(
                    range(len(solutions)),
                    key=lambda index: (
                        mean_agreement[index], solutions[index]["silhouette"]
                    ),
                )
            )
            representative = solutions[representative_index]
            representative_sequences[(window_size, n_states)] = {
                "labels": representative["labels"],
                "centers": windowed.centers,
            }

            output_path = OUTPUT_DIRECTORY / f"window_{window_size}_states_{n_states}.npz"
            np.savez_compressed(
                output_path,
                labels=representative["labels"],
                centroids=representative["centroids"],
                centers=windowed.centers,
                window_size=window_size,
                step=STEP,
                n_states=n_states,
                seed=representative["seed"],
            )
            representative_files.append(str(output_path.relative_to(ROOT)))
            records.append(
                {
                    "window_size": window_size,
                    "window_seconds": window_size * TR,
                    "n_states": n_states,
                    "n_windows": windowed.features.shape[0],
                    "mean_silhouette": float(np.mean([s["silhouette"] for s in solutions])),
                    "sd_silhouette": float(np.std([s["silhouette"] for s in solutions], ddof=1)),
                    "mean_seed_stability_ari": float(np.mean(agreement[np.triu_indices(len(solutions), 1)])),
                    "minimum_seed_stability_ari": float(np.min(agreement[np.triu_indices(len(solutions), 1)])),
                    "representative_seed": representative["seed"],
                    "representative_silhouette": representative["silhouette"],
                    "representative_minimum_occupancy": representative["minimum_occupancy"],
                    "representative_switch_rate": representative["switch_rate"],
                    "representative_median_run_windows": representative["median_run_windows"],
                    "representative_median_run_seconds": representative["median_run_windows"] * STEP * TR,
                }
            )

    # Compare temporal state memberships across window sizes for the same k.
    cross_window = []
    for n_states in N_STATES:
        for first_index, first_window in enumerate(WINDOW_SIZES):
            for second_window in WINDOW_SIZES[first_index + 1 :]:
                first = representative_sequences[(first_window, n_states)]
                second = representative_sequences[(second_window, n_states)]
                lower = max(first["centers"].min(), second["centers"].min())
                upper = min(first["centers"].max(), second["centers"].max())
                common_time = np.arange(np.ceil(lower), np.floor(upper) + 1)
                first_nearest = np.abs(first["centers"][:, None] - common_time).argmin(axis=0)
                second_nearest = np.abs(second["centers"][:, None] - common_time).argmin(axis=0)
                cross_window.append(
                    {
                        "n_states": n_states,
                        "first_window": first_window,
                        "second_window": second_window,
                        "temporal_membership_ari": adjusted_rand_index(
                            first["labels"][first_nearest],
                            second["labels"][second_nearest],
                        ),
                    }
                )

    with (OUTPUT_DIRECTORY / "solutions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    with (OUTPUT_DIRECTORY / "cross_window_stability.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cross_window[0]))
        writer.writeheader()
        writer.writerows(cross_window)

    by_states = {
        str(n_states): {
            "mean_cross_window_ari": float(np.mean([
                row["temporal_membership_ari"] for row in cross_window
                if row["n_states"] == n_states
            ])),
            "minimum_cross_window_ari": float(np.min([
                row["temporal_membership_ari"] for row in cross_window
                if row["n_states"] == n_states
            ])),
        }
        for n_states in N_STATES
    }
    summary = {
        "method": {
            "data": "single released empirical BOLD recording",
            "filter_hz": [0.008, 0.09],
            "repetition_time_seconds": TR,
            "window_sizes_samples": list(WINDOW_SIZES),
            "window_sizes_seconds": [window * TR for window in WINDOW_SIZES],
            "window_step_samples": STEP,
            "candidate_state_counts": list(N_STATES),
            "clustering_repetitions": len(SEEDS),
            "features": "upper-triangle windowed FC, Fisher-z transformed",
            "clustering": "k-means with k-means++ initialization",
            "model_data_used": False,
        },
        "cross_window_stability_by_state_count": by_states,
        "representative_files": representative_files,
        "selection_status": "candidate assessment only; no state definition frozen yet",
    }
    (OUTPUT_DIRECTORY / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    figure, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    colors = {30: "#2E5D7B", 50: "#A77A2D", 80: "#B23A48"}
    for window_size in WINDOW_SIZES:
        selected = [row for row in records if row["window_size"] == window_size]
        x = [row["n_states"] for row in selected]
        axes[0, 0].plot(x, [row["mean_silhouette"] for row in selected], marker="o", color=colors[window_size], label=f"{window_size} samples")
        axes[0, 1].plot(x, [row["mean_seed_stability_ari"] for row in selected], marker="o", color=colors[window_size])
        axes[1, 0].plot(x, [row["representative_minimum_occupancy"] for row in selected], marker="o", color=colors[window_size])
    axes[1, 1].plot(N_STATES, [by_states[str(k)]["mean_cross_window_ari"] for k in N_STATES], marker="o", color="#414B5A")
    axes[0, 0].set_title("Cluster separation", fontweight="bold")
    axes[0, 0].set_ylabel("Mean silhouette")
    axes[0, 0].legend(frameon=False)
    axes[0, 1].set_title("Repeatability across seeds", fontweight="bold")
    axes[0, 1].set_ylabel("Mean pairwise ARI")
    axes[1, 0].set_title("Smallest state's occupancy", fontweight="bold")
    axes[1, 0].set_ylabel("Proportion of windows")
    axes[1, 1].set_title("Agreement across window sizes", fontweight="bold")
    axes[1, 1].set_ylabel("Mean temporal-membership ARI")
    for axis in axes.flat:
        axis.set_xlabel("Number of states")
        axis.set_xticks(N_STATES)
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Empirical recurrent-state candidate assessment", fontweight="bold")
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved candidate results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
