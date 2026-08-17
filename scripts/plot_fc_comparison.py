"""Visualize empirical FC against cooperative-only and signed simulations."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import load_single_subject


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = PROJECT_ROOT / "upstream" / "competitive-cooperative-hopf"
DATA_DIRECTORY = UPSTREAM_ROOT / "data" / "matlab" / "single"
RESULTS_DIRECTORY = PROJECT_ROOT / "results" / "single_subject_optimization"
FIGURE_PATH = PROJECT_ROOT / "figures" / "single_subject_fc_comparison.png"


def lower_triangle_correlation(first: np.ndarray, second: np.ndarray) -> float:
    indices = np.tril_indices_from(first, k=-1)
    return float(np.corrcoef(first[indices], second[indices])[0, 1])


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    empirical_fc = np.corrcoef(data.bold)
    cooperative_fc = np.load(RESULTS_DIRECTORY / "cooperative_only.npz")[
        "simulated_fc"
    ]
    signed_fc = np.load(RESULTS_DIRECTORY / "signed.npz")["simulated_fc"]

    cooperative_fit = lower_triangle_correlation(empirical_fc, cooperative_fc)
    signed_fit = lower_triangle_correlation(empirical_fc, signed_fc)
    cooperative_error = np.abs(empirical_fc - cooperative_fc)
    signed_error = np.abs(empirical_fc - signed_fc)

    off_diagonal = np.tril_indices_from(empirical_fc, k=-1)
    cooperative_mae = float(np.mean(cooperative_error[off_diagonal]))
    signed_mae = float(np.mean(signed_error[off_diagonal]))

    figure, axes = plt.subplots(2, 3, figsize=(13.5, 8.5), constrained_layout=True)
    matrices = [empirical_fc, cooperative_fc, signed_fc]
    titles = [
        "Empirical FC",
        f"Cooperative-only simulated FC\nr = {cooperative_fit:.3f}",
        f"Signed simulated FC\nr = {signed_fit:.3f}",
    ]

    for axis, matrix, title in zip(axes[0], matrices, titles, strict=True):
        image = axis.imshow(matrix, cmap="RdBu_r", vmin=-1.0, vmax=1.0)
        axis.set_title(title, fontsize=11, fontweight="bold")
        axis.set_xlabel("Brain region")
        axis.set_ylabel("Brain region")

    colorbar = figure.colorbar(image, ax=axes[0].tolist(), shrink=0.85)
    colorbar.set_label("Pearson correlation")

    errors = [cooperative_error, signed_error]
    error_titles = [
        f"Absolute error: cooperative-only\nMAE = {cooperative_mae:.3f}",
        f"Absolute error: signed\nMAE = {signed_mae:.3f}",
    ]
    maximum_error = max(np.percentile(cooperative_error, 99), np.percentile(signed_error, 99))
    for axis, matrix, title in zip(axes[1, :2], errors, error_titles, strict=True):
        error_image = axis.imshow(matrix, cmap="magma", vmin=0.0, vmax=maximum_error)
        axis.set_title(title, fontsize=11, fontweight="bold")
        axis.set_xlabel("Brain region")
        axis.set_ylabel("Brain region")

    error_colorbar = figure.colorbar(error_image, ax=axes[1, :2].tolist(), shrink=0.85)
    error_colorbar.set_label("Absolute FC error")

    summary_axis = axes[1, 2]
    conditions = ["Cooperative-only", "Signed"]
    correlations = [cooperative_fit, signed_fit]
    colors = ["#6E87A5", "#B84A4A"]
    bars = summary_axis.bar(conditions, correlations, color=colors, width=0.62)
    summary_axis.set_ylim(0.0, 0.75)
    summary_axis.set_ylabel("Empirical–simulated FC correlation")
    summary_axis.set_title("FC reconstruction", fontsize=11, fontweight="bold")
    summary_axis.spines[["top", "right"]].set_visible(False)
    summary_axis.bar_label(bars, fmt="%.3f", padding=4, fontweight="bold")
    summary_axis.tick_params(axis="x", rotation=12)

    figure.suptitle(
        "Single-subject Hopf model: empirical and simulated functional connectivity",
        fontsize=15,
        fontweight="bold",
    )
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(f"Cooperative-only FC correlation: {cooperative_fit:.6f}")
    print(f"Signed FC correlation: {signed_fit:.6f}")
    print(f"Cooperative-only FC MAE: {cooperative_mae:.6f}")
    print(f"Signed FC MAE: {signed_mae:.6f}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
