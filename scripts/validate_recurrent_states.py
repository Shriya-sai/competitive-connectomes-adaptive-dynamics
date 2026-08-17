"""Validate recurrent-state recovery using synthetic signals with known switches."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import lfilter

from luppi_recreation import (
    adjusted_rand_index,
    cluster_connectivity_states,
    windowed_functional_connectivity,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "results" / "recurrent_state_validation"
FIGURE_PATH = ROOT / "figures" / "recurrent_state_validation.png"
N_REGIONS = 20
SEGMENT_LENGTH = 300
TRUE_SEQUENCE = np.array([0, 1, 0, 1, 0, 1])
WINDOW_SIZE = 80
STEP = 5


def _smooth_noise(rng: np.random.Generator, length: int) -> np.ndarray:
    return lfilter([1.0], [1.0, -0.85], rng.normal(size=length))


def synthetic_switching_signals(
    seed: int = 42,
    *,
    segment_length: int = SEGMENT_LENGTH,
    noise_scale: float = 0.45,
    sequence: np.ndarray = TRUE_SEQUENCE,
) -> tuple[np.ndarray, np.ndarray]:
    """Create two FC states defined by different anatomical partitions."""

    rng = np.random.default_rng(seed)
    sequence = np.asarray(sequence, dtype=int)
    if segment_length < 3 or noise_scale < 0:
        raise ValueError("segment_length must be at least 3 and noise_scale non-negative")
    signals = np.empty((N_REGIONS, segment_length * sequence.size))
    truth = np.repeat(sequence, segment_length)
    for segment_index, state in enumerate(sequence):
        start = segment_index * segment_length
        stop = start + segment_length
        latent_a = _smooth_noise(rng, segment_length)
        latent_b = _smooth_noise(rng, segment_length)
        if state == 0:
            group_a = np.arange(N_REGIONS) < N_REGIONS // 2
        else:
            group_a = np.arange(N_REGIONS) % 2 == 0
        for region in range(N_REGIONS):
            latent = latent_a if group_a[region] else latent_b
            noise = _smooth_noise(rng, segment_length)
            signals[region, start:stop] = latent + noise_scale * noise
    signals -= signals.mean(axis=1, keepdims=True)
    signals /= signals.std(axis=1, keepdims=True)
    return signals, truth


def main() -> None:
    signals, point_truth = synthetic_switching_signals()
    windowed = windowed_functional_connectivity(
        signals, window_size=WINDOW_SIZE, step=STEP
    )
    labels, centroids = cluster_connectivity_states(
        windowed.features, n_states=2, seed=42
    )

    # Windows spanning a true transition have no single correct state.
    window_truth = np.empty(labels.size, dtype=int)
    pure = np.ones(labels.size, dtype=bool)
    for index, start in enumerate(windowed.starts):
        contained = point_truth[start : start + WINDOW_SIZE]
        pure[index] = np.all(contained == contained[0])
        window_truth[index] = contained[contained.size // 2]
    ari = adjusted_rand_index(window_truth[pure], labels[pure])

    # Align arbitrary cluster numbers to the known 0/1 names for readable plots.
    direct_accuracy = np.mean(labels[pure] == window_truth[pure])
    flipped_accuracy = np.mean((1 - labels[pure]) == window_truth[pure])
    aligned = labels if direct_accuracy >= flipped_accuracy else 1 - labels
    accuracy = float(np.mean(aligned[pure] == window_truth[pure]))

    state_templates = []
    upper = np.triu_indices(N_REGIONS, k=1)
    for state in (0, 1):
        template = np.corrcoef(signals[:, point_truth == state])
        state_templates.append(template)
    template_separation = float(
        np.linalg.norm((state_templates[0] - state_templates[1])[upper])
    )

    gates = {
        "pure_window_accuracy_at_least_95_percent": accuracy >= 0.95,
        "adjusted_rand_index_at_least_0_90": ari >= 0.90,
        "both_states_recovered": np.unique(aligned[pure]).size == 2,
    }
    summary = {
        "design": {
            "regions": N_REGIONS,
            "timepoints": signals.shape[1],
            "true_state_sequence": TRUE_SEQUENCE.tolist(),
            "segment_length": SEGMENT_LENGTH,
            "window_size": WINDOW_SIZE,
            "step": STEP,
            "state_0_partition": "regions 1-10 versus 11-20",
            "state_1_partition": "odd-numbered versus even-numbered regions",
        },
        "recovery": {
            "total_windows": int(labels.size),
            "pure_windows_scored": int(pure.sum()),
            "transition_crossing_windows_excluded": int((~pure).sum()),
            "pure_window_accuracy": accuracy,
            "adjusted_rand_index": ari,
            "template_separation_l2": template_separation,
        },
        "validation_gates": {key: bool(value) for key, value in gates.items()},
        "all_gates_passed": bool(all(gates.values())),
    }

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIRECTORY / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    figure, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    image_options = dict(vmin=-1, vmax=1, cmap="RdBu_r")
    first = axes[0, 0].imshow(state_templates[0], **image_options)
    axes[0, 0].set_title("Ground-truth State A FC", fontweight="bold")
    axes[0, 1].imshow(state_templates[1], **image_options)
    axes[0, 1].set_title("Ground-truth State B FC", fontweight="bold")
    figure.colorbar(first, ax=axes[0, :], shrink=0.75, label="Correlation")

    time = np.arange(point_truth.size)
    axes[1, 0].step(time, point_truth, where="post", label="True state", linewidth=2)
    axes[1, 0].scatter(
        windowed.centers[pure], aligned[pure], s=10, alpha=0.65,
        label="Recovered window", color="#B23A48"
    )
    axes[1, 0].scatter(
        windowed.centers[~pure], aligned[~pure], s=14, marker="x",
        label="Transition-crossing window", color="#777777"
    )
    axes[1, 0].set_yticks([0, 1], ["State A", "State B"])
    axes[1, 0].set_xlabel("Synthetic timepoint")
    axes[1, 0].set_title("Known versus recovered state sequence", fontweight="bold")
    axes[1, 0].legend(frameon=False, fontsize=8)

    axes[1, 1].bar(
        ["Accuracy", "Adjusted\nRand index"], [accuracy, ari],
        color=["#2E5D7B", "#B23A48"]
    )
    axes[1, 1].axhline(0.90, color="#555555", linestyle="--", linewidth=1)
    axes[1, 1].set_ylim(0, 1.05)
    axes[1, 1].set_title("Recovery score on unambiguous windows", fontweight="bold")
    axes[1, 1].spines[["top", "right"]].set_visible(False)
    figure.suptitle("Synthetic validation of recurrent-state recovery", fontweight="bold")
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    if not summary["all_gates_passed"]:
        raise RuntimeError("one or more recurrent-state validation gates failed")
    print(f"Saved summary to: {OUTPUT_DIRECTORY / 'summary.json'}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
