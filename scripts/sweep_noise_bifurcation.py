"""Coarse noise-by-bifurcation sweep with fitted signed connectivity frozen."""

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import load_hopf_extension, load_single_subject
from sweep_cooperative_competitive_gains import (
    DATA_DIRECTORY,
    METRICS,
    NOISE_TYPE,
    OPTIMIZATION_PATH,
    TR,
    UPSTREAM_ROOT,
    measure,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "results" / "noise_bifurcation_sweep"
FIGURE_PATH = ROOT / "figures" / "noise_bifurcation_sweep.png"
NOISE_STRENGTHS = (0.00025, 0.0005, 0.001, 0.002, 0.004)
BIFURCATION_PARAMETERS = (-0.06, -0.04, -0.02, -0.01, 0.0, 0.01)
SEEDS = tuple(range(42, 47))


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    upper = np.triu_indices(data.n_regions, k=1)
    empirical_fc_vector = np.corrcoef(data.bold)[upper]
    empirical = measure(data.bold, empirical_fc_vector)
    fitted = np.load(OPTIMIZATION_PATH)
    connectivity = np.asarray(fitted["generative_connectivity"])
    frequencies = np.asarray(fitted["regional_frequencies"])
    hopf = load_hopf_extension(UPSTREAM_ROOT)
    rows = []

    for bifurcation in BIFURCATION_PARAMETERS:
        for noise in NOISE_STRENGTHS:
            print(f"Bifurcation {bifurcation:.3f}; noise {noise:.5f}", flush=True)
            for seed in SEEDS:
                simulated = np.asarray(
                    hopf.simulate(
                        connectivity,
                        frequencies,
                        data.n_timepoints,
                        TR,
                        noise,
                        bifurcation,
                        NOISE_TYPE,
                        seed,
                    ),
                    dtype=np.float64,
                )
                rows.append({
                    "bifurcation_parameter": bifurcation,
                    "noise_strength": noise,
                    "seed": seed,
                    **measure(simulated, empirical_fc_vector),
                })

    grouped = []
    for bifurcation in BIFURCATION_PARAMETERS:
        for noise in NOISE_STRENGTHS:
            selected = [
                row for row in rows
                if row["bifurcation_parameter"] == bifurcation
                and row["noise_strength"] == noise
            ]
            record = {
                "bifurcation_parameter": bifurcation,
                "noise_strength": noise,
            }
            for metric in METRICS:
                values = np.array([row[metric] for row in selected])
                record[f"mean_{metric}"] = float(values.mean())
                record[f"sd_{metric}"] = float(values.std(ddof=1))
                record[f"absolute_error_{metric}"] = float(
                    abs(values.mean() - empirical[metric])
                )
            grouped.append(record)

    baseline = next(
        row for row in grouped
        if row["noise_strength"] == 0.001
        and row["bifurcation_parameter"] == -0.02
    )
    geometry_metrics = (
        "repertoire_dispersion",
        "effective_dimension",
        "mean_central_distance",
        "mean_nearest_recurrence_distance",
    )
    kinetic_metrics = ("mean_speed", "speed_variability")
    for row in grouped:
        row["mean_relative_geometry_error"] = float(np.mean([
            row[f"absolute_error_{metric}"] / abs(empirical[metric])
            for metric in geometry_metrics
        ]))
        row["mean_relative_kinetic_error"] = float(np.mean([
            row[f"absolute_error_{metric}"] / abs(empirical[metric])
            for metric in kinetic_metrics
        ]))
        row["geometry_error_change_from_baseline"] = row["mean_relative_geometry_error"] - float(np.mean([
            baseline[f"absolute_error_{metric}"] / abs(empirical[metric])
            for metric in geometry_metrics
        ]))
        row["kinetic_error_change_from_baseline"] = row["mean_relative_kinetic_error"] - float(np.mean([
            baseline[f"absolute_error_{metric}"] / abs(empirical[metric])
            for metric in kinetic_metrics
        ]))

    kinetic_rescue = sorted(
        [
            row for row in grouped
            if row["mean_relative_kinetic_error"] < baseline["mean_relative_kinetic_error"]
            and row["mean_relative_geometry_error"] <= baseline["mean_relative_geometry_error"] + 0.02
        ],
        key=lambda row: row["mean_relative_kinetic_error"],
    )
    closest = {
        metric: min(grouped, key=lambda row: row[f"absolute_error_{metric}"])
        for metric in METRICS
    }
    summary = {
        "design": {
            "noise_strengths": list(NOISE_STRENGTHS),
            "bifurcation_parameters": list(BIFURCATION_PARAMETERS),
            "seeds": list(SEEDS),
            "runs": len(rows),
            "signed_connectivity_frozen": True,
            "cooperative_gain": 1.0,
            "competitive_gain": 1.0,
            "exploratory_coarse_grid": True,
        },
        "empirical": {metric: empirical[metric] for metric in METRICS},
        "baseline_noise_0.001_bifurcation_-0.02": baseline,
        "kinetic_rescue_rule": "kinetic relative error below baseline while geometry relative error increases by no more than 0.02",
        "kinetic_rescue_candidates": kinetic_rescue,
        "closest_grid_point_by_metric": {
            metric: {
                "noise_strength": row["noise_strength"],
                "bifurcation_parameter": row["bifurcation_parameter"],
                "mean_value": row[f"mean_{metric}"],
                "empirical_value": empirical[metric],
                "absolute_error": row[f"absolute_error_{metric}"],
            }
            for metric, row in closest.items()
        },
        "interpretation_status": "exploratory; any selected rescue candidate requires independent-seed confirmation",
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
    (OUTPUT_DIRECTORY / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

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
                    if row["bifurcation_parameter"] == bifurcation
                    and row["noise_strength"] == noise
                )
                for noise in NOISE_STRENGTHS
            ]
            for bifurcation in BIFURCATION_PARAMETERS
        ])
        image = axis.imshow(matrix, origin="lower", aspect="auto", cmap="viridis")
        axis.scatter(NOISE_STRENGTHS.index(0.001), BIFURCATION_PARAMETERS.index(-0.02), marker="s", facecolors="none", edgecolors="white", s=90, linewidths=1.5)
        axis.set_xticks(range(len(NOISE_STRENGTHS)), [f"{value:g}" for value in NOISE_STRENGTHS], rotation=25)
        axis.set_yticks(range(len(BIFURCATION_PARAMETERS)), BIFURCATION_PARAMETERS)
        axis.set_xlabel("Noise strength")
        axis.set_ylabel("Bifurcation parameter")
        axis.set_title(titles[metric], fontweight="bold", fontsize=10)
        figure.colorbar(image, ax=axis, shrink=0.78)
    figure.suptitle(
        "Noise–bifurcation sweep with signed connectivity frozen\nWhite square = baseline (noise 0.001, a = -0.02)",
        fontweight="bold",
    )
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
