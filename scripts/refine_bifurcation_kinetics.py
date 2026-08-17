"""Refine the bifurcation interval between kinetic and geometric optima."""

import csv
import json
from pathlib import Path

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
OUTPUT_DIRECTORY = ROOT / "results" / "bifurcation_kinetic_refinement"
BIFURCATIONS = (-0.035, -0.030, -0.025)
NOISE_STRENGTHS = (0.001, 0.004)
SEEDS = tuple(range(42, 47))
GEOMETRY_METRICS = (
    "repertoire_dispersion",
    "effective_dimension",
    "mean_central_distance",
    "mean_nearest_recurrence_distance",
)
KINETIC_METRICS = ("mean_speed", "speed_variability")


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    upper = np.triu_indices(data.n_regions, k=1)
    empirical_fc = np.corrcoef(data.bold)[upper]
    empirical = measure(data.bold, empirical_fc)
    fitted = np.load(OPTIMIZATION_PATH)
    connectivity = np.asarray(fitted["generative_connectivity"])
    frequencies = np.asarray(fitted["regional_frequencies"])
    hopf = load_hopf_extension(UPSTREAM_ROOT)
    rows = []
    for bifurcation in BIFURCATIONS:
        for noise in NOISE_STRENGTHS:
            print(f"Refinement a={bifurcation:.3f}; noise={noise:.3f}", flush=True)
            for seed in SEEDS:
                simulated = np.asarray(
                    hopf.simulate(connectivity, frequencies, data.n_timepoints, TR, noise, bifurcation, NOISE_TYPE, seed),
                    dtype=np.float64,
                )
                rows.append({"bifurcation_parameter": bifurcation, "noise_strength": noise, "seed": seed, **measure(simulated, empirical_fc)})

    grouped = []
    for bifurcation in BIFURCATIONS:
        for noise in NOISE_STRENGTHS:
            selected = [row for row in rows if row["bifurcation_parameter"] == bifurcation and row["noise_strength"] == noise]
            record = {"bifurcation_parameter": bifurcation, "noise_strength": noise}
            for metric in METRICS:
                values = np.array([row[metric] for row in selected])
                record[f"mean_{metric}"] = float(values.mean())
                record[f"sd_{metric}"] = float(values.std(ddof=1))
                record[f"absolute_error_{metric}"] = float(abs(values.mean() - empirical[metric]))
            record["mean_relative_geometry_error"] = float(np.mean([record[f"absolute_error_{metric}"] / abs(empirical[metric]) for metric in GEOMETRY_METRICS]))
            record["mean_relative_kinetic_error"] = float(np.mean([record[f"absolute_error_{metric}"] / abs(empirical[metric]) for metric in KINETIC_METRICS]))
            grouped.append(record)

    summary = {
        "design": {"bifurcations": list(BIFURCATIONS), "noise_strengths": list(NOISE_STRENGTHS), "seeds": list(SEEDS), "runs": len(rows), "signed_connectivity_frozen": True},
        "empirical": {metric: empirical[metric] for metric in METRICS},
        "ranked_by_kinetic_error": sorted(grouped, key=lambda row: row["mean_relative_kinetic_error"]),
        "interpretation_status": "focused discovery refinement; selected candidates require independent seeds",
    }
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIRECTORY / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    with (OUTPUT_DIRECTORY / "grid_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(grouped[0]))
        writer.writeheader(); writer.writerows(grouped)
    (OUTPUT_DIRECTORY / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")


if __name__ == "__main__":
    main()
