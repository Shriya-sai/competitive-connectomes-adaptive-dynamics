"""Compare empirical and frozen Hopf models in continuous LEiDA geometry."""

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import (
    bandpass_signals,
    instantaneous_phase,
    leading_phase_eigenvectors,
    load_hopf_extension,
    load_single_subject,
    summarize_leida_landscape,
)


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = ROOT / "upstream" / "competitive-cooperative-hopf"
DATA_DIRECTORY = UPSTREAM_ROOT / "data" / "matlab" / "single"
OPTIMIZATION_DIRECTORY = ROOT / "results" / "single_subject_optimization"
OUTPUT_DIRECTORY = ROOT / "results" / "leida_landscape_evaluation"
FIGURE_PATH = ROOT / "figures" / "leida_landscape_evaluation.png"

TR = 0.72
NOISE_STRENGTH = 0.001
BIFURCATION_PARAMETER = -0.02
NOISE_TYPE = 1
SEEDS = tuple(range(42, 72))
RECURRENCE_EXCLUSION = 20
METRICS = (
    "repertoire_dispersion",
    "effective_dimension",
    "mean_speed",
    "speed_variability",
    "mean_central_distance",
    "mean_nearest_recurrence_distance",
)


def measure(signals: np.ndarray) -> tuple[dict[str, float], np.ndarray]:
    filtered = bandpass_signals(signals, TR)
    phases = instantaneous_phase(filtered)
    vectors, dominance = leading_phase_eigenvectors(phases)
    landscape = summarize_leida_landscape(
        vectors,
        repetition_time=TR,
        recurrence_exclusion=RECURRENCE_EXCLUSION,
    )
    values = landscape.__dict__.copy()
    values["mean_leading_mode_dominance"] = float(dominance.mean())
    return values, vectors


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    empirical, empirical_vectors = measure(data.bold)
    fitted = {
        "cooperative_only": np.load(OPTIMIZATION_DIRECTORY / "cooperative_only.npz"),
        "signed": np.load(OPTIMIZATION_DIRECTORY / "signed.npz"),
    }
    frequencies = np.asarray(fitted["signed"]["regional_frequencies"])
    hopf = load_hopf_extension(UPSTREAM_ROOT)
    rows = []
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
            values, _ = measure(simulated)
            rows.append({"seed": seed, "condition": condition, **values})

    summary = {
        "method": {
            "representation": "instantaneous dominant phase-locking eigenvector",
            "geometry": "projective angular; antipodal signs identified",
            "repetition_time_seconds": TR,
            "recurrence_exclusion_samples": RECURRENCE_EXCLUSION,
            "seeds": list(SEEDS),
            "frozen_models": True,
            "clustering_used": False,
        },
        "empirical": empirical,
        "models": {},
        "paired_closeness": {},
    }
    for condition in fitted:
        selected = [row for row in rows if row["condition"] == condition]
        summary["models"][condition] = {
            metric: {
                "mean": float(np.mean([row[metric] for row in selected])),
                "sd": float(np.std([row[metric] for row in selected], ddof=1)),
                "mean_absolute_error_from_empirical": float(
                    np.mean([abs(row[metric] - empirical[metric]) for row in selected])
                ),
            }
            for metric in (*METRICS, "mean_leading_mode_dominance")
        }
    for metric in (*METRICS, "mean_leading_mode_dominance"):
        cooperative = {
            row["seed"]: row[metric] for row in rows
            if row["condition"] == "cooperative_only"
        }
        signed = {
            row["seed"]: row[metric] for row in rows
            if row["condition"] == "signed"
        }
        cooperative_error = np.array([
            abs(cooperative[seed] - empirical[metric]) for seed in SEEDS
        ])
        signed_error = np.array([
            abs(signed[seed] - empirical[metric]) for seed in SEEDS
        ])
        summary["paired_closeness"][metric] = {
            "signed_closer_count": int(np.sum(signed_error < cooperative_error)),
            "cooperative_closer_count": int(np.sum(cooperative_error < signed_error)),
            "ties": int(np.sum(cooperative_error == signed_error)),
            "mean_absolute_error_reduction_signed_minus_cooperative": float(
                np.mean(cooperative_error - signed_error)
            ),
        }

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIRECTORY / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUTPUT_DIRECTORY / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    figure, axes = plt.subplots(2, 3, figsize=(13, 8), constrained_layout=True)
    labels = {"cooperative_only": "Cooperative-only", "signed": "Signed"}
    colors = {"cooperative_only": "#6E87A5", "signed": "#B84A4A"}
    for axis, metric in zip(axes.flat, METRICS, strict=True):
        distributions = [
            [row[metric] for row in rows if row["condition"] == condition]
            for condition in ("cooperative_only", "signed")
        ]
        violin = axis.violinplot(distributions, showmeans=True, showextrema=True)
        for body, condition in zip(violin["bodies"], ("cooperative_only", "signed"), strict=True):
            body.set_facecolor(colors[condition])
            body.set_edgecolor(colors[condition])
            body.set_alpha(0.75)
        axis.axhline(empirical[metric], color="#414B5A", linestyle="--", label="Empirical")
        axis.set_xticks([1, 2], [labels["cooperative_only"], labels["signed"]])
        axis.set_title(metric.replace("_", " ").title(), fontsize=9, fontweight="bold")
        axis.spines[["top", "right"]].set_visible(False)
    axes[0, 0].legend(frameon=False)
    figure.suptitle("Empirical and frozen-model continuous LEiDA landscapes", fontweight="bold")
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
