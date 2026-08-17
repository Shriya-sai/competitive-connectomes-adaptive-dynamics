"""Assess empirical LEiDA states with consensus and block stability."""

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
    cluster_projective_states,
    leading_phase_eigenvectors,
    load_single_subject,
    instantaneous_phase,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = ROOT / "upstream" / "competitive-cooperative-hopf" / "data" / "matlab" / "single"
OUTPUT_DIRECTORY = ROOT / "results" / "empirical_leida_state_selection"
FIGURE_PATH = ROOT / "figures" / "empirical_leida_state_selection.png"
N_STATES = tuple(range(2, 11))
CONSENSUS_SEEDS = tuple(range(100, 200))
TRIMS = (0, 20, 50, 100)
BLOCK_DELETIONS = 12
DELETED_FRACTION = 0.20
TR = 0.72


def consensus_labels(vectors: np.ndarray, n_states: int) -> tuple[np.ndarray, float]:
    labelings = [
        cluster_projective_states(vectors, n_states=n_states, seed=seed)[0]
        for seed in CONSENSUS_SEEDS
    ]
    coassignment = np.mean(
        [labels[:, None] == labels[None, :] for labels in labelings], axis=0
    )
    distance = np.clip(1 - coassignment, 0, 1)
    np.fill_diagonal(distance, 0)
    hierarchy = linkage(squareform(distance, checks=False), method="average")
    consensus = fcluster(hierarchy, t=n_states, criterion="maxclust") - 1
    same = consensus[:, None] == consensus[None, :]
    upper = np.triu_indices(consensus.size, k=1)
    within = coassignment[upper][same[upper]]
    between = coassignment[upper][~same[upper]]
    return consensus, float(within.mean() - between.mean())


def best_projective_multistart(
    vectors: np.ndarray, n_states: int, seed_start: int
) -> np.ndarray:
    best = None
    for seed in range(seed_start, seed_start + 20):
        labels, centroids = cluster_projective_states(
            vectors, n_states=n_states, seed=seed
        )
        objective = float(
            np.sum(1 - np.abs(np.sum(vectors * centroids[labels], axis=1)))
        )
        if best is None or objective < best[0]:
            best = (objective, centroids)
    return best[1]


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    filtered = bandpass_signals(data.bold, TR)
    phases = instantaneous_phase(filtered)
    all_vectors, dominance = leading_phase_eigenvectors(phases)
    solutions = {}
    rows = []
    deletion_rows = []
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    for trim in TRIMS:
        vectors = all_vectors[trim:-trim] if trim else all_vectors
        trimmed_dominance = dominance[trim:-trim] if trim else dominance
        delete_size = int(round(vectors.shape[0] * DELETED_FRACTION))
        starts = np.linspace(0, vectors.shape[0] - delete_size, BLOCK_DELETIONS, dtype=int)
        for n_states in N_STATES:
            consensus, contrast = consensus_labels(vectors, n_states)
            solutions[(trim, n_states)] = consensus
            occupancy = np.bincount(consensus, minlength=n_states) / consensus.size
            block_aris = []
            for deletion_index, start in enumerate(starts):
                retained = np.ones(vectors.shape[0], dtype=bool)
                retained[start : start + delete_size] = False
                centroids = best_projective_multistart(
                    vectors[retained], n_states, 1000 + deletion_index * 20
                )
                assigned = np.argmax(
                    np.abs(vectors[retained] @ centroids.T), axis=1
                )
                ari = adjusted_rand_index(consensus[retained], assigned)
                block_aris.append(ari)
                deletion_rows.append({
                    "trim": trim,
                    "n_states": n_states,
                    "deletion_index": deletion_index,
                    "deleted_start": int(start),
                    "deleted_timepoints": delete_size,
                    "ari_vs_consensus": ari,
                })
            rows.append({
                "trim": trim,
                "n_states": n_states,
                "timepoints": vectors.shape[0],
                "mean_leading_eigenvalue_dominance": float(trimmed_dominance.mean()),
                "consensus_contrast": contrast,
                "minimum_state_occupancy": float(occupancy.min()),
                "mean_block_deletion_ari": float(np.mean(block_aris)),
                "minimum_block_deletion_ari": float(np.min(block_aris)),
                "maximum_block_deletion_ari": float(np.max(block_aris)),
            })
            np.savez_compressed(
                OUTPUT_DIRECTORY / f"trim_{trim}_states_{n_states}.npz",
                labels=consensus,
                trim=trim,
                n_states=n_states,
                dominance=trimmed_dominance,
            )

    trim_sensitivity = []
    for n_states in N_STATES:
        primary = solutions[(0, n_states)]
        for trim in TRIMS[1:]:
            trim_sensitivity.append({
                "n_states": n_states,
                "trim": trim,
                "ari_primary_subset_vs_trimmed_solution": adjusted_rand_index(
                    primary[trim:-trim], solutions[(trim, n_states)]
                ),
            })

    with (OUTPUT_DIRECTORY / "solutions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (OUTPUT_DIRECTORY / "block_deletions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(deletion_rows[0]))
        writer.writeheader()
        writer.writerows(deletion_rows)
    with (OUTPUT_DIRECTORY / "trim_sensitivity.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(trim_sensitivity[0]))
        writer.writeheader()
        writer.writerows(trim_sensitivity)

    primary_rows = [row for row in rows if row["trim"] == 0]
    robust = [
        row for row in primary_rows
        if row["mean_block_deletion_ari"] >= 0.80
        and row["minimum_block_deletion_ari"] >= 0.60
        and row["minimum_state_occupancy"] >= 0.05
        and row["consensus_contrast"] >= 0.50
        and min(
            item["ari_primary_subset_vs_trimmed_solution"]
            for item in trim_sensitivity
            if item["n_states"] == row["n_states"]
        ) >= 0.60
    ]
    summary = {
        "method": {
            "representation": "instantaneous leading eigenvector of phase-locking matrix",
            "distance_geometry": "projective; v and -v treated as identical",
            "consensus_initializations": len(CONSENSUS_SEEDS),
            "block_deletions": BLOCK_DELETIONS,
            "deleted_fraction": DELETED_FRACTION,
            "trims_tested": list(TRIMS),
            "model_data_used": False,
        },
        "robustness_rule": "mean block ARI >= .80, minimum block ARI >= .60, occupancy >= 5%, contrast >= .50, every trim ARI >= .60",
        "robust_primary_solutions": robust,
        "number_robust": len(robust),
        "selection_status": "no state definition frozen until candidate multiplicity is interpreted",
    }
    (OUTPUT_DIRECTORY / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    figure, axes = plt.subplots(1, 3, figsize=(13, 4.2), constrained_layout=True)
    axes[0].plot(N_STATES, [row["mean_block_deletion_ari"] for row in primary_rows], marker="o", color="#2E5D7B")
    axes[0].axhline(0.80, linestyle="--", color="#555555", linewidth=1)
    axes[0].set_title("Block-deletion stability", fontweight="bold")
    axes[0].set_ylabel("Mean ARI")
    axes[1].plot(N_STATES, [row["consensus_contrast"] for row in primary_rows], marker="o", color="#B23A48")
    axes[1].axhline(0.50, linestyle="--", color="#555555", linewidth=1)
    axes[1].set_title("Consensus discreteness", fontweight="bold")
    axes[1].set_ylabel("Within-minus-between co-assignment")
    for trim in TRIMS[1:]:
        selected = [row for row in trim_sensitivity if row["trim"] == trim]
        axes[2].plot(N_STATES, [row["ari_primary_subset_vs_trimmed_solution"] for row in selected], marker="o", label=f"Trim {trim}")
    axes[2].axhline(0.60, linestyle="--", color="#555555", linewidth=1)
    axes[2].set_title("Hilbert-boundary sensitivity", fontweight="bold")
    axes[2].set_ylabel("ARI versus primary solution")
    axes[2].legend(frameon=False, fontsize=8)
    for axis in axes:
        axis.set_xlabel("Number of LEiDA states")
        axis.set_xticks(N_STATES)
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Empirical LEiDA state robustness", fontweight="bold")
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
