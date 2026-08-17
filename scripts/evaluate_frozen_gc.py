"""Evaluate frozen fitted GCs across matched stochastic simulation seeds."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import load_hopf_extension, load_single_subject


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = PROJECT_ROOT / "upstream" / "competitive-cooperative-hopf"
DATA_DIRECTORY = UPSTREAM_ROOT / "data" / "matlab" / "single"
OPTIMIZATION_DIRECTORY = PROJECT_ROOT / "results" / "single_subject_optimization"
OUTPUT_DIRECTORY = PROJECT_ROOT / "results" / "frozen_gc_evaluation"
FIGURE_PATH = PROJECT_ROOT / "figures" / "frozen_gc_stochastic_evaluation.png"

REPETITION_TIME = 0.72
NOISE_STRENGTH = 0.001
BIFURCATION_PARAMETER = -0.02
NOISE_TYPE = 1


def lower_triangle_values(matrix: np.ndarray) -> np.ndarray:
    return matrix[np.tril_indices_from(matrix, k=-1)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--first-seed", type=int, default=42)
    args = parser.parse_args()
    if args.runs < 2:
        raise ValueError("At least two runs are required")

    data = load_single_subject(DATA_DIRECTORY)
    empirical_fc = np.corrcoef(data.bold)
    empirical_values = lower_triangle_values(empirical_fc)
    signed_results = np.load(OPTIMIZATION_DIRECTORY / "signed.npz")
    cooperative_results = np.load(OPTIMIZATION_DIRECTORY / "cooperative_only.npz")
    frequencies = signed_results["regional_frequencies"]
    connectivities = {
        "cooperative_only": cooperative_results["generative_connectivity"],
        "signed": signed_results["generative_connectivity"],
    }
    hopf = load_hopf_extension(UPSTREAM_ROOT)

    records: list[dict[str, float | int | str]] = []
    for seed in range(args.first_seed, args.first_seed + args.runs):
        print(f"Seed {seed}", flush=True)
        for condition, connectivity in connectivities.items():
            simulated_bold = np.asarray(
                hopf.simulate(
                    connectivity,
                    frequencies,
                    data.n_timepoints,
                    REPETITION_TIME,
                    NOISE_STRENGTH,
                    BIFURCATION_PARAMETER,
                    NOISE_TYPE,
                    seed,
                ),
                dtype=np.float64,
            )
            simulated_fc = np.corrcoef(simulated_bold)
            simulated_values = lower_triangle_values(simulated_fc)
            records.append(
                {
                    "seed": seed,
                    "condition": condition,
                    "fc_correlation": float(
                        np.corrcoef(empirical_values, simulated_values)[0, 1]
                    ),
                    "fc_mae": float(np.mean(np.abs(empirical_values - simulated_values))),
                }
            )

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIRECTORY / "runs.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    summary: dict[str, dict[str, float]] = {}
    for condition in connectivities:
        selected = [record for record in records if record["condition"] == condition]
        correlations = np.array([record["fc_correlation"] for record in selected])
        errors = np.array([record["fc_mae"] for record in selected])
        summary[condition] = {
            "mean_fc_correlation": float(correlations.mean()),
            "sd_fc_correlation": float(correlations.std(ddof=1)),
            "minimum_fc_correlation": float(correlations.min()),
            "maximum_fc_correlation": float(correlations.max()),
            "mean_fc_mae": float(errors.mean()),
            "sd_fc_mae": float(errors.std(ddof=1)),
        }

    paired_differences = []
    for seed in range(args.first_seed, args.first_seed + args.runs):
        pair = {
            str(record["condition"]): float(record["fc_correlation"])
            for record in records
            if record["seed"] == seed
        }
        paired_differences.append(pair["signed"] - pair["cooperative_only"])
    summary["paired_signed_minus_cooperative"] = {
        "mean": float(np.mean(paired_differences)),
        "sd": float(np.std(paired_differences, ddof=1)),
        "minimum": float(np.min(paired_differences)),
        "maximum": float(np.max(paired_differences)),
        "fraction_signed_higher": float(np.mean(np.array(paired_differences) > 0)),
    }

    summary_path = OUTPUT_DIRECTORY / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.5), constrained_layout=True)
    colors = {"cooperative_only": "#6E87A5", "signed": "#B84A4A"}
    labels = {"cooperative_only": "Cooperative-only", "signed": "Signed"}
    for condition in connectivities:
        selected = [record for record in records if record["condition"] == condition]
        x = np.array([record["seed"] for record in selected])
        y = np.array([record["fc_correlation"] for record in selected])
        axes[0].plot(x, y, "o-", color=colors[condition], alpha=0.75, label=labels[condition])
    axes[0].set_xlabel("Matched random seed")
    axes[0].set_ylabel("Empirical–simulated FC correlation")
    axes[0].set_title("Frozen-GC forward simulations", fontweight="bold")
    axes[0].legend(frameon=False)

    distributions = [
        [
            float(record["fc_correlation"])
            for record in records
            if record["condition"] == condition
        ]
        for condition in ("cooperative_only", "signed")
    ]
    violin = axes[1].violinplot(distributions, showmeans=True, showextrema=True)
    for body, color in zip(violin["bodies"], [colors["cooperative_only"], colors["signed"]], strict=True):
        body.set_facecolor(color)
        body.set_edgecolor(color)
        body.set_alpha(0.7)
    axes[1].set_xticks([1, 2], ["Cooperative-only", "Signed"])
    axes[1].set_ylabel("Empirical–simulated FC correlation")
    axes[1].set_title("Stochastic variability", fontweight="bold")

    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Frozen fitted connectivity across stochastic simulations", fontweight="bold")
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved runs to: {csv_path}")
    print(f"Saved summary to: {summary_path}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
