"""Compare structural and fitted generative-connectivity matrices."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import load_single_subject


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = PROJECT_ROOT / "upstream" / "competitive-cooperative-hopf"
DATA_DIRECTORY = UPSTREAM_ROOT / "data" / "matlab" / "single"
RESULTS_DIRECTORY = PROJECT_ROOT / "results" / "single_subject_optimization"
FIGURE_PATH = PROJECT_ROOT / "figures" / "single_subject_connectivity_comparison.png"
SUMMARY_PATH = RESULTS_DIRECTORY / "connectivity_summary.json"


def summarize(matrix: np.ndarray) -> dict[str, float | int]:
    off_diagonal = ~np.eye(matrix.shape[0], dtype=bool)
    values = matrix[off_diagonal]
    nonzero = values[values != 0]
    positive = nonzero[nonzero > 0]
    negative = nonzero[nonzero < 0]
    denominator = nonzero.size if nonzero.size else 1
    return {
        "nonzero_edges": int(nonzero.size),
        "positive_edges": int(positive.size),
        "negative_edges": int(negative.size),
        "negative_fraction": float(negative.size / denominator),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "mean_positive_magnitude": float(positive.mean()) if positive.size else 0.0,
        "mean_negative_magnitude": float(np.abs(negative).mean()) if negative.size else 0.0,
        "asymmetry_mean_absolute": float(np.mean(np.abs(matrix - matrix.T))),
        "asymmetry_maximum_absolute": float(np.max(np.abs(matrix - matrix.T))),
    }


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    structural = data.structural_connectivity
    cooperative = np.load(RESULTS_DIRECTORY / "cooperative_only.npz")[
        "generative_connectivity"
    ]
    signed = np.load(RESULTS_DIRECTORY / "signed.npz")["generative_connectivity"]

    positive_signed = np.where(signed > 0, signed, 0.0)
    negative_signed = np.where(signed < 0, signed, 0.0)

    summaries = {
        "structural_connectivity": summarize(structural),
        "cooperative_only_gc": summarize(cooperative),
        "signed_gc": summarize(signed),
    }
    SUMMARY_PATH.write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")

    figure, axes = plt.subplots(2, 3, figsize=(14, 8.8), constrained_layout=True)

    structural_image = axes[0, 0].imshow(structural, cmap="viridis", vmin=0.0)
    axes[0, 0].set_title("Structural connectivity\n(anatomical scaffold)", fontweight="bold")
    figure.colorbar(structural_image, ax=axes[0, 0], shrink=0.78, label="SC weight")

    gc_limit = np.percentile(np.abs(signed[signed != 0]), 99)
    for axis, matrix, title in [
        (axes[0, 1], cooperative, "Cooperative-only GC"),
        (axes[0, 2], signed, "Signed GC"),
    ]:
        image = axis.imshow(matrix, cmap="RdBu_r", vmin=-gc_limit, vmax=gc_limit)
        axis.set_title(title, fontweight="bold")
    figure.colorbar(image, ax=axes[0, 1:].tolist(), shrink=0.78, label="Generative weight")

    positive_image = axes[1, 0].imshow(
        positive_signed,
        cmap="Reds",
        vmin=0.0,
        vmax=gc_limit,
    )
    axes[1, 0].set_title("Positive component of signed GC", fontweight="bold")
    figure.colorbar(positive_image, ax=axes[1, 0], shrink=0.78, label="Positive weight")

    negative_image = axes[1, 1].imshow(
        np.abs(negative_signed),
        cmap="Blues",
        vmin=0.0,
        vmax=gc_limit,
    )
    axes[1, 1].set_title("Negative component of signed GC\n(absolute magnitude)", fontweight="bold")
    figure.colorbar(negative_image, ax=axes[1, 1], shrink=0.78, label="|Negative weight|")

    histogram_axis = axes[1, 2]
    signed_nonzero = signed[signed != 0]
    cooperative_nonzero = cooperative[cooperative != 0]
    bins = np.linspace(
        min(signed_nonzero.min(), cooperative_nonzero.min()),
        max(signed_nonzero.max(), cooperative_nonzero.max()),
        55,
    )
    histogram_axis.hist(
        cooperative_nonzero,
        bins=bins,
        alpha=0.62,
        color="#6E87A5",
        label="Cooperative-only",
    )
    histogram_axis.hist(
        signed_nonzero,
        bins=bins,
        alpha=0.62,
        color="#B84A4A",
        label="Signed",
    )
    histogram_axis.axvline(0.0, color="black", linewidth=1.0)
    histogram_axis.set_title("Nonzero GC weight distributions", fontweight="bold")
    histogram_axis.set_xlabel("Generative-connectivity weight")
    histogram_axis.set_ylabel("Directed edges")
    histogram_axis.legend(frameon=False)
    histogram_axis.spines[["top", "right"]].set_visible(False)

    for axis in axes.flat[:5]:
        axis.set_xlabel("Source region")
        axis.set_ylabel("Target region")

    figure.suptitle(
        "Single-subject structural and fitted generative connectivity",
        fontsize=15,
        fontweight="bold",
    )
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    for name, summary in summaries.items():
        print(f"\n{name}")
        for key, value in summary.items():
            print(f"  {key}: {value}")
    print(f"\nSaved summary to: {SUMMARY_PATH}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
