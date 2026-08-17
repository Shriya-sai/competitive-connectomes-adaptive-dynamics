"""Validate LEiDA recovery on known noisy phase-locking states."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import (
    adjusted_rand_index,
    cluster_projective_states,
    leading_phase_eigenvectors,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "results" / "leida_state_validation"
FIGURE_PATH = ROOT / "figures" / "leida_state_validation.png"
N_REGIONS = 100
SEGMENT_LENGTH = 180
SEQUENCE = np.array([0, 1, 0, 1, 0, 1])
NOISE_LEVELS = (0.00, 0.15, 0.30, 0.50, 0.75, 1.00)
SEEDS = tuple(range(42, 52))


def synthetic_phases(noise: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    truth = np.repeat(SEQUENCE, SEGMENT_LENGTH)
    carrier = 2 * np.pi * 0.03 * np.arange(truth.size)
    phases = np.empty((N_REGIONS, truth.size))
    regions = np.arange(N_REGIONS)
    for timepoint, state in enumerate(truth):
        first_community = (
            regions < N_REGIONS // 2 if state == 0 else regions % 2 == 0
        )
        offsets = np.where(first_community, 0.0, np.pi)
        phases[:, timepoint] = (
            carrier[timepoint] + offsets + rng.normal(scale=noise, size=N_REGIONS)
        )
    return phases, truth


def aligned_accuracy(truth: np.ndarray, labels: np.ndarray) -> float:
    return float(max(np.mean(labels == truth), np.mean((1 - labels) == truth)))


def main() -> None:
    rows = []
    example = None
    for noise in NOISE_LEVELS:
        for seed in SEEDS:
            phases, truth = synthetic_phases(noise, seed)
            vectors, dominance = leading_phase_eigenvectors(phases)
            labels, _ = cluster_projective_states(vectors, n_states=2, seed=seed)
            accuracy = aligned_accuracy(truth, labels)
            ari = adjusted_rand_index(truth, labels)
            rows.append({
                "noise_radians_sd": noise,
                "seed": seed,
                "accuracy": accuracy,
                "adjusted_rand_index": ari,
                "mean_dominance": float(dominance.mean()),
            })
            if noise == 0.50 and seed == 42:
                aligned = labels if np.mean(labels == truth) >= np.mean((1 - labels) == truth) else 1 - labels
                example = (truth, aligned, vectors)

    grouped = {}
    for noise in NOISE_LEVELS:
        selected = [row for row in rows if row["noise_radians_sd"] == noise]
        grouped[str(noise)] = {
            "mean_accuracy": float(np.mean([row["accuracy"] for row in selected])),
            "minimum_accuracy": float(np.min([row["accuracy"] for row in selected])),
            "mean_adjusted_rand_index": float(np.mean([row["adjusted_rand_index"] for row in selected])),
            "mean_dominance": float(np.mean([row["mean_dominance"] for row in selected])),
        }
    gates = {
        "clean_recovery_perfect": grouped["0.0"]["minimum_accuracy"] == 1.0,
        "moderate_noise_mean_accuracy_at_least_95_percent": grouped["0.5"]["mean_accuracy"] >= 0.95,
        "heavy_noise_mean_accuracy_at_least_80_percent": grouped["1.0"]["mean_accuracy"] >= 0.80,
    }
    summary = {
        "design": {
            "regions": N_REGIONS,
            "state_sequence": SEQUENCE.tolist(),
            "segment_length": SEGMENT_LENGTH,
            "noise_levels_radians_sd": list(NOISE_LEVELS),
            "seeds": list(SEEDS),
            "state_0": "regions 1-50 versus 51-100",
            "state_1": "odd-numbered versus even-numbered regions",
        },
        "results_by_noise": grouped,
        "validation_gates": {key: bool(value) for key, value in gates.items()},
        "all_gates_passed": bool(all(gates.values())),
    }
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIRECTORY / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    figure, axes = plt.subplots(1, 3, figsize=(13, 4.2), constrained_layout=True)
    accuracies = [grouped[str(noise)]["mean_accuracy"] for noise in NOISE_LEVELS]
    ari_values = [grouped[str(noise)]["mean_adjusted_rand_index"] for noise in NOISE_LEVELS]
    axes[0].plot(NOISE_LEVELS, accuracies, marker="o", label="Accuracy", color="#2E5D7B")
    axes[0].plot(NOISE_LEVELS, ari_values, marker="o", label="Adjusted Rand", color="#B23A48")
    axes[0].set_ylim(0, 1.03)
    axes[0].set_xlabel("Phase noise (radians SD)")
    axes[0].set_ylabel("Recovery score")
    axes[0].set_title("Robustness to phase noise", fontweight="bold")
    axes[0].legend(frameon=False)

    truth, aligned, vectors = example
    shown = slice(0, SEGMENT_LENGTH * 2)
    axes[1].step(np.arange(truth.size)[shown], truth[shown], where="post", linewidth=2, label="True")
    axes[1].scatter(np.arange(truth.size)[shown], aligned[shown], s=7, alpha=0.5, color="#B23A48", label="Recovered")
    axes[1].set_yticks([0, 1], ["State A", "State B"])
    axes[1].set_xlabel("Synthetic timepoint")
    axes[1].set_title("Recovery at 0.5-radian noise", fontweight="bold")
    axes[1].legend(frameon=False)

    axes[2].imshow(vectors[: SEGMENT_LENGTH * 2].T, aspect="auto", cmap="RdBu_r", vmin=-0.15, vmax=0.15)
    axes[2].set_xlabel("Synthetic timepoint")
    axes[2].set_ylabel("Region")
    axes[2].set_title("Instantaneous LEiDA vectors", fontweight="bold")
    for axis in axes[:2]:
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Synthetic validation of LEiDA state recognition", fontweight="bold")
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    if not summary["all_gates_passed"]:
        raise RuntimeError("one or more LEiDA validation gates failed")
    print(f"Saved summary to: {OUTPUT_DIRECTORY / 'summary.json'}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
