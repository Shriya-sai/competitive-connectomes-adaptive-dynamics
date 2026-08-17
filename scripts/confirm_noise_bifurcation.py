"""Confirm refined noise-bifurcation candidates on independent seeds."""

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
OUTPUT_DIRECTORY = ROOT / "results" / "noise_bifurcation_confirmation"
FIGURE_PATH = ROOT / "figures" / "noise_bifurcation_confirmation.png"
SEEDS = tuple(range(102, 132))
CONDITIONS = {
    "baseline": (-0.020, 0.001),
    "refined_candidate": (-0.025, 0.004),
    "bifurcation_only_control": (-0.025, 0.001),
    "intermediate_control": (-0.030, 0.001),
    "kinetic_tradeoff_control": (-0.040, 0.004),
}


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
    for seed in SEEDS:
        print(f"Independent seed {seed}", flush=True)
        for name, (bifurcation, noise) in CONDITIONS.items():
            simulated = np.asarray(
                hopf.simulate(connectivity, frequencies, data.n_timepoints, TR, noise, bifurcation, NOISE_TYPE, seed),
                dtype=np.float64,
            )
            rows.append({"seed": seed, "condition": name, "bifurcation_parameter": bifurcation, "noise_strength": noise, **measure(simulated, empirical_fc)})

    conditions = {}
    for name, (bifurcation, noise) in CONDITIONS.items():
        selected = [row for row in rows if row["condition"] == name]
        conditions[name] = {
            "bifurcation_parameter": bifurcation,
            "noise_strength": noise,
            **{
                metric: {
                    "mean": float(np.mean([row[metric] for row in selected])),
                    "sd": float(np.std([row[metric] for row in selected], ddof=1)),
                    "mean_absolute_error_from_empirical": float(np.mean([abs(row[metric] - empirical[metric]) for row in selected])),
                }
                for metric in METRICS
            },
        }

    paired_candidate_vs_baseline = {}
    for metric in METRICS:
        baseline = {row["seed"]: abs(row[metric] - empirical[metric]) for row in rows if row["condition"] == "baseline"}
        candidate = {row["seed"]: abs(row[metric] - empirical[metric]) for row in rows if row["condition"] == "refined_candidate"}
        differences = np.array([baseline[seed] - candidate[seed] for seed in SEEDS])
        paired_candidate_vs_baseline[metric] = {
            "candidate_closer_count": int(np.sum(differences > 0)),
            "baseline_closer_count": int(np.sum(differences < 0)),
            "ties": int(np.sum(differences == 0)),
            "mean_absolute_error_reduction": float(differences.mean()),
        }

    summary = {
        "design": {
            "conditions_frozen_before_confirmation": {name: {"bifurcation_parameter": values[0], "noise_strength": values[1]} for name, values in CONDITIONS.items()},
            "independent_seeds": list(SEEDS),
            "runs": len(rows),
            "selection_data_reused": False,
            "signed_connectivity_and_sign_gains_frozen": True,
        },
        "empirical": {metric: empirical[metric] for metric in METRICS},
        "conditions": conditions,
        "paired_refined_candidate_vs_baseline": paired_candidate_vs_baseline,
        "interpretation_scope": "simulation seeds quantify stochastic robustness, not biological population uncertainty",
    }
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIRECTORY / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (OUTPUT_DIRECTORY / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    names = list(CONDITIONS)
    labels = [name.replace("_control", "").replace("_", "\n") for name in names]
    colors = ["#B23A48", "#2E5D7B", "#4F8A70", "#A77A2D", "#7F6A93"]
    figure, axes = plt.subplots(3, 3, figsize=(13, 11), constrained_layout=True)
    for axis, metric in zip(axes.flat, METRICS, strict=True):
        means = [conditions[name][metric]["mean"] for name in names]
        errors = [conditions[name][metric]["sd"] for name in names]
        axis.bar(range(len(names)), means, yerr=errors, capsize=2, color=colors, alpha=0.85)
        if metric != "fc_correlation":
            axis.axhline(empirical[metric], color="#1A1A1A", linestyle="--", linewidth=1)
        axis.set_xticks(range(len(names)), labels, fontsize=7)
        axis.set_title(metric.replace("_", " ").title(), fontsize=9, fontweight="bold")
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Independent confirmation of noise–bifurcation candidates", fontweight="bold")
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
