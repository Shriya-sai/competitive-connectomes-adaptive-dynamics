"""Confirm preregistered gain-sweep candidates on independent simulation seeds."""

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import load_hopf_extension, load_single_subject
from sweep_cooperative_competitive_gains import (
    BIFURCATION_PARAMETER,
    DATA_DIRECTORY,
    METRICS,
    NOISE_STRENGTH,
    NOISE_TYPE,
    OPTIMIZATION_PATH,
    TR,
    UPSTREAM_ROOT,
    measure,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "results" / "cooperative_competitive_gain_confirmation"
FIGURE_PATH = ROOT / "figures" / "cooperative_competitive_gain_confirmation.png"
SEEDS = tuple(range(72, 102))
CONDITIONS = {
    "negative_removed": (1.0, 0.0),
    "competitive_only": (0.0, 1.0),
    "low_balanced": (0.5, 0.5),
    "metastability_candidate": (0.75, 0.5),
    "dimension_candidate": (1.0, 0.75),
    "fitted_signed": (1.0, 1.0),
    "high_balanced": (1.5, 1.5),
}
DYNAMIC_METRICS = tuple(metric for metric in METRICS if metric != "fc_correlation")


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

    for seed in SEEDS:
        print(f"Independent seed {seed}", flush=True)
        for name, (cooperative_gain, competitive_gain) in CONDITIONS.items():
            connectivity = cooperative_gain * positive + competitive_gain * negative
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
            rows.append({
                "seed": seed,
                "condition": name,
                "cooperative_gain": cooperative_gain,
                "competitive_gain": competitive_gain,
                **measure(simulated, empirical_fc_vector),
            })

    conditions_summary = {}
    for name in CONDITIONS:
        selected = [row for row in rows if row["condition"] == name]
        conditions_summary[name] = {
            "cooperative_gain": CONDITIONS[name][0],
            "competitive_gain": CONDITIONS[name][1],
            **{
                metric: {
                    "mean": float(np.mean([row[metric] for row in selected])),
                    "sd": float(np.std([row[metric] for row in selected], ddof=1)),
                    "mean_absolute_error_from_empirical": float(
                        np.mean([abs(row[metric] - empirical[metric]) for row in selected])
                    ),
                }
                for metric in METRICS
            },
        }

    seed_winners = {}
    for metric in DYNAMIC_METRICS:
        counts = {name: 0 for name in CONDITIONS}
        for seed in SEEDS:
            candidates = {
                row["condition"]: abs(row[metric] - empirical[metric])
                for row in rows if row["seed"] == seed
            }
            counts[min(candidates, key=candidates.get)] += 1
        seed_winners[metric] = counts

    summary = {
        "design": {
            "conditions_frozen_before_confirmation": {
                name: {"cooperative_gain": gains[0], "competitive_gain": gains[1]}
                for name, gains in CONDITIONS.items()
            },
            "independent_seeds": list(SEEDS),
            "runs": len(rows),
            "selection_data_reused": False,
            "topology_and_weights_other_than_sign_gain_frozen": True,
        },
        "empirical": {metric: empirical[metric] for metric in METRICS},
        "conditions": conditions_summary,
        "closest_condition_count_by_seed": seed_winners,
        "interpretation_scope": "simulation seeds quantify stochastic robustness, not biological population uncertainty",
    }
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIRECTORY / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUTPUT_DIRECTORY / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    figure, axes = plt.subplots(3, 3, figsize=(14, 11), constrained_layout=True)
    names = list(CONDITIONS)
    short = [name.replace("_candidate", "").replace("_", "\n") for name in names]
    colors = ["#7F8C8D", "#6C5B7B", "#4F8A70", "#A77A2D", "#2E5D7B", "#B23A48", "#8E5D3B"]
    for axis, metric in zip(axes.flat, METRICS, strict=True):
        values = [conditions_summary[name][metric]["mean"] for name in names]
        errors = [conditions_summary[name][metric]["sd"] for name in names]
        axis.bar(range(len(names)), values, yerr=errors, color=colors, alpha=0.85, capsize=2)
        if metric != "fc_correlation":
            axis.axhline(empirical[metric], color="#1A1A1A", linestyle="--", linewidth=1, label="Empirical")
        axis.set_xticks(range(len(names)), short, fontsize=7)
        axis.set_title(metric.replace("_", " ").title(), fontsize=9, fontweight="bold")
        axis.spines[["top", "right"]].set_visible(False)
    axes[0, 1].legend(frameon=False, fontsize=8)
    figure.suptitle("Independent confirmation of cooperative–competitive gain candidates", fontweight="bold")
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
