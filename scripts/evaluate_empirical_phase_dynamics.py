"""Compare empirical and frozen-model phase dynamics across matched seeds."""

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import (
    bandpass_signals,
    load_hopf_extension,
    load_single_subject,
    phase_dynamics,
)


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = ROOT / "upstream" / "competitive-cooperative-hopf"
DATA_DIRECTORY = UPSTREAM_ROOT / "data" / "matlab" / "single"
OPTIMIZATION_DIRECTORY = ROOT / "results" / "single_subject_optimization"
OUTPUT_DIRECTORY = ROOT / "results" / "empirical_phase_dynamics"
FIGURE_PATH = ROOT / "figures" / "empirical_phase_dynamics.png"

TR = 0.72
FILTER_LOW = 0.008
FILTER_HIGH = 0.09
FILTER_ORDER = 2
NOISE_STRENGTH = 0.001
BIFURCATION_PARAMETER = -0.02
NOISE_TYPE = 1
SEEDS = list(range(42, 72))
TRIMS = (0, 20, 50, 100)
PRIMARY_TRIM = 0  # Closest replication: the paper does not report edge trimming.


def measure(signals: np.ndarray, trim: int) -> dict[str, float]:
    filtered = bandpass_signals(
        signals, TR, FILTER_LOW, FILTER_HIGH, FILTER_ORDER
    )
    result = phase_dynamics(filtered, trim=trim)
    return {
        "mean_synchrony": result.synchrony,
        "maximum_synchrony": result.maximum_synchrony,
        "metastability": result.metastability,
    }


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    empirical_by_trim = {str(trim): measure(data.bold, trim) for trim in TRIMS}
    empirical_filtered = bandpass_signals(
        data.bold, TR, FILTER_LOW, FILTER_HIGH, FILTER_ORDER
    )
    empirical_dynamics = phase_dynamics(empirical_filtered, trim=PRIMARY_TRIM)

    fitted = {
        "cooperative_only": np.load(OPTIMIZATION_DIRECTORY / "cooperative_only.npz"),
        "signed": np.load(OPTIMIZATION_DIRECTORY / "signed.npz"),
    }
    frequencies = np.asarray(fitted["signed"]["regional_frequencies"])
    hopf = load_hopf_extension(UPSTREAM_ROOT)
    records: list[dict[str, str | int | float]] = []

    for seed in SEEDS:
        print(f"Seed {seed}", flush=True)
        for condition, result_file in fitted.items():
            simulated = np.asarray(
                hopf.simulate(
                    result_file["generative_connectivity"],
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
            for trim in TRIMS:
                metrics = measure(simulated, trim)
                records.append(
                    {
                        "seed": seed,
                        "condition": condition,
                        "trim": trim,
                        **metrics,
                    }
                )

    primary_records = [record for record in records if record["trim"] == PRIMARY_TRIM]
    primary_empirical = empirical_by_trim[str(PRIMARY_TRIM)]
    summary: dict[str, object] = {
        "method": {
            "filter_hz": [FILTER_LOW, FILTER_HIGH],
            "butterworth_order": FILTER_ORDER,
            "repetition_time_seconds": TR,
            "metastability_definition": "population SD of KOP over time",
            "paper_synchrony_measure": "maximum KOP over time",
            "additional_synchrony_measure": "mean KOP over time",
            "primary_trim_samples_per_edge": PRIMARY_TRIM,
            "trim_sensitivity_samples_per_edge": list(TRIMS),
            "primary_trim_rationale": "No boundary trimming is reported in the paper; alternate trims are sensitivity analyses.",
        },
        "empirical_by_trim": empirical_by_trim,
        "models_primary_trim": {},
        "trim_sensitivity": {},
    }
    metrics = ("mean_synchrony", "maximum_synchrony", "metastability")
    for condition in fitted:
        selected = [r for r in primary_records if r["condition"] == condition]
        condition_summary = {}
        for metric in metrics:
            values = np.asarray([float(r[metric]) for r in selected])
            empirical_value = primary_empirical[metric]
            condition_summary[metric] = {
                "mean": float(values.mean()),
                "sd": float(values.std(ddof=1)),
                "empirical": empirical_value,
                "mean_absolute_error_from_empirical": float(
                    np.mean(np.abs(values - empirical_value))
                ),
            }
        summary["models_primary_trim"][condition] = condition_summary

    for trim in TRIMS:
        trim_summary = {}
        for condition in fitted:
            selected = [
                r for r in records if r["condition"] == condition and r["trim"] == trim
            ]
            trim_summary[condition] = {
                metric: float(np.mean([float(r[metric]) for r in selected]))
                for metric in metrics
            }
        summary["trim_sensitivity"][str(trim)] = trim_summary

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIRECTORY / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (OUTPUT_DIRECTORY / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    figure, axes = plt.subplots(1, 3, figsize=(13, 4.5), constrained_layout=True)
    time_minutes = np.arange(data.n_timepoints) * TR / 60
    axes[0].plot(time_minutes, empirical_dynamics.order_parameter, color="#414B5A", linewidth=0.9)
    axes[0].set_xlabel("Time (minutes)")
    axes[0].set_ylabel("Empirical KOP, R(t)")
    axes[0].set_title("Empirical coordination over time", fontweight="bold")

    colors = {"cooperative_only": "#6E87A5", "signed": "#B84A4A"}
    labels = {"cooperative_only": "Cooperative-only", "signed": "Signed"}
    for axis, metric, title in (
        (axes[1], "metastability", "Metastability: SD[KOP]"),
        (axes[2], "maximum_synchrony", "Maximum synchrony: max[KOP]"),
    ):
        distributions = [
            [float(r[metric]) for r in primary_records if r["condition"] == condition]
            for condition in ("cooperative_only", "signed")
        ]
        violin = axis.violinplot(distributions, showmeans=True, showextrema=True)
        for body, condition in zip(violin["bodies"], ("cooperative_only", "signed"), strict=True):
            body.set_facecolor(colors[condition])
            body.set_edgecolor(colors[condition])
            body.set_alpha(0.75)
        axis.axhline(primary_empirical[metric], color="#414B5A", linestyle="--", label="Empirical")
        axis.set_xticks([1, 2], [labels["cooperative_only"], labels["signed"]])
        axis.set_title(title, fontweight="bold")
        axis.legend(frameon=False)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Empirical and frozen-model phase dynamics", fontweight="bold")
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
