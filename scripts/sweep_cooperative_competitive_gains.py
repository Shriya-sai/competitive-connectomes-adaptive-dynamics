"""Coarse two-dimensional gain sweep of frozen signed Hopf connectivity."""

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import (
    bandpass_signals,
    instantaneous_phase,
    kuramoto_order_parameter,
    leading_phase_eigenvectors,
    load_hopf_extension,
    load_single_subject,
    summarize_leida_landscape,
    summarize_order_parameter,
)


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = ROOT / "upstream" / "competitive-cooperative-hopf"
DATA_DIRECTORY = UPSTREAM_ROOT / "data" / "matlab" / "single"
OPTIMIZATION_PATH = ROOT / "results" / "single_subject_optimization" / "signed.npz"
OUTPUT_DIRECTORY = ROOT / "results" / "cooperative_competitive_gain_sweep"
FIGURE_PATH = ROOT / "figures" / "cooperative_competitive_gain_sweep.png"

TR = 0.72
NOISE_STRENGTH = 0.001
BIFURCATION_PARAMETER = -0.02
NOISE_TYPE = 1
GAINS = (0.0, 0.5, 0.75, 1.0, 1.25, 1.5)
SEEDS = tuple(range(42, 47))
RECURRENCE_EXCLUSION = 20
METRICS = (
    "fc_correlation",
    "mean_synchrony",
    "metastability",
    "repertoire_dispersion",
    "effective_dimension",
    "mean_central_distance",
    "mean_speed",
    "speed_variability",
    "mean_nearest_recurrence_distance",
)


def measure(signals: np.ndarray, empirical_fc_vector: np.ndarray) -> dict[str, float]:
    upper = np.triu_indices(signals.shape[0], k=1)
    fc_vector = np.corrcoef(signals)[upper]
    fc_correlation = float(np.corrcoef(fc_vector, empirical_fc_vector)[0, 1])
    filtered = bandpass_signals(signals, TR)
    phases = instantaneous_phase(filtered)
    order_parameter = kuramoto_order_parameter(phases)
    synchrony, _, metastability = summarize_order_parameter(order_parameter)
    vectors, _ = leading_phase_eigenvectors(phases)
    landscape = summarize_leida_landscape(
        vectors,
        repetition_time=TR,
        recurrence_exclusion=RECURRENCE_EXCLUSION,
    )
    return {
        "fc_correlation": fc_correlation,
        "mean_synchrony": synchrony,
        "metastability": metastability,
        **landscape.__dict__,
    }


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    upper = np.triu_indices(data.n_regions, k=1)
    empirical_fc_vector = np.corrcoef(data.bold)[upper]
    empirical = measure(data.bold, empirical_fc_vector)

    fitted = np.load(OPTIMIZATION_PATH)
    signed_connectivity = np.asarray(fitted["generative_connectivity"])
    positive = np.clip(signed_connectivity, 0, None)
    negative = np.clip(signed_connectivity, None, 0)
    frequencies = np.asarray(fitted["regional_frequencies"])
    hopf = load_hopf_extension(UPSTREAM_ROOT)
    rows = []

    for cooperative_gain in GAINS:
        for competitive_gain in GAINS:
            print(
                f"Cooperative gain {cooperative_gain:.2f}; competitive gain {competitive_gain:.2f}",
                flush=True,
            )
            connectivity = cooperative_gain * positive + competitive_gain * negative
            for seed in SEEDS:
                simulated = np.asarray(
                    hopf.simulate(
                        connectivity,
                        frequencies,
                        data.n_timepoints,
                        TR,
                        NOISE_STRENGTH,
                        BIFURCATION_PARAMETER,
                        NOISE_TYPE,
                        seed,
                    ),
                    dtype=np.float64,
                )
                rows.append(
                    {
                        "cooperative_gain": cooperative_gain,
                        "competitive_gain": competitive_gain,
                        "seed": seed,
                        **measure(simulated, empirical_fc_vector),
                    }
                )

    grouped = []
    for cooperative_gain in GAINS:
        for competitive_gain in GAINS:
            selected = [
                row for row in rows
                if row["cooperative_gain"] == cooperative_gain
                and row["competitive_gain"] == competitive_gain
            ]
            record = {
                "cooperative_gain": cooperative_gain,
                "competitive_gain": competitive_gain,
            }
            for metric in METRICS:
                values = np.array([row[metric] for row in selected])
                record[f"mean_{metric}"] = float(values.mean())
                record[f"sd_{metric}"] = float(values.std(ddof=1))
                record[f"absolute_error_{metric}"] = float(
                    abs(values.mean() - empirical[metric])
                )
            grouped.append(record)

    closest = {}
    for metric in METRICS:
        best = min(grouped, key=lambda row: row[f"absolute_error_{metric}"])
        closest[metric] = {
            "cooperative_gain": best["cooperative_gain"],
            "competitive_gain": best["competitive_gain"],
            "mean_value": best[f"mean_{metric}"],
            "empirical_value": empirical[metric],
            "absolute_error": best[f"absolute_error_{metric}"],
        }

    def condition(g_coop: float, g_comp: float) -> dict[str, float]:
        return next(
            row for row in grouped
            if row["cooperative_gain"] == g_coop
            and row["competitive_gain"] == g_comp
        )

    summary = {
        "design": {
            "cooperative_gains": list(GAINS),
            "competitive_gains": list(GAINS),
            "seeds": list(SEEDS),
            "runs": len(rows),
            "frozen_positive_and_negative_topology": True,
            "scaled_connectivity": "g_coop * positive(GC) + g_comp * negative(GC)",
            "exploratory_coarse_grid": True,
        },
        "empirical": {metric: empirical[metric] for metric in METRICS},
        "reference_conditions": {
            "original_signed_1_1": condition(1.0, 1.0),
            "negative_removed_from_signed_1_0": condition(1.0, 0.0),
            "competitive_only_0_1": condition(0.0, 1.0),
            "uncoupled_0_0": condition(0.0, 0.0),
        },
        "closest_grid_point_by_metric": closest,
        "interpretation_status": "exploratory; focused conditions require 30-seed confirmation",
    }

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIRECTORY / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (OUTPUT_DIRECTORY / "grid_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(grouped[0]))
        writer.writeheader()
        writer.writerows(grouped)
    (OUTPUT_DIRECTORY / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    titles = {
        "fc_correlation": "Empirical FC correlation",
        "mean_synchrony": "Mean synchrony",
        "metastability": "Metastability",
        "repertoire_dispersion": "Repertoire dispersion",
        "effective_dimension": "Effective dimension",
        "mean_central_distance": "Central distance",
        "mean_speed": "Trajectory speed",
        "speed_variability": "Speed variability",
        "mean_nearest_recurrence_distance": "Nearest recurrence distance",
    }
    figure, axes = plt.subplots(3, 3, figsize=(13, 11), constrained_layout=True)
    for axis, metric in zip(axes.flat, METRICS, strict=True):
        matrix = np.array([
            [
                next(
                    row[f"mean_{metric}"] for row in grouped
                    if row["cooperative_gain"] == cooperative_gain
                    and row["competitive_gain"] == competitive_gain
                )
                for cooperative_gain in GAINS
            ]
            for competitive_gain in GAINS
        ])
        image = axis.imshow(matrix, origin="lower", aspect="auto", cmap="viridis")
        axis.scatter(GAINS.index(1.0), GAINS.index(1.0), marker="s", facecolors="none", edgecolors="white", s=90, linewidths=1.5)
        axis.set_xticks(range(len(GAINS)), GAINS)
        axis.set_yticks(range(len(GAINS)), GAINS)
        axis.set_xlabel("Cooperative gain")
        axis.set_ylabel("Competitive gain")
        axis.set_title(titles[metric], fontweight="bold", fontsize=10)
        figure.colorbar(image, ax=axis, shrink=0.78)
    figure.suptitle(
        "Cooperative–competitive gain sweep\nWhite square = fitted signed model (1, 1)",
        fontweight="bold",
    )
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
