"""Validate continuous LEiDA landscape metrics on known trajectories."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import summarize_leida_landscape


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "results" / "leida_landscape_validation"
FIGURE_PATH = ROOT / "figures" / "leida_landscape_validation.png"
N_TIMEPOINTS = 600
N_DIMENSIONS = 20


def trajectories() -> dict[str, np.ndarray]:
    fixed = np.tile(np.eye(N_DIMENSIONS)[0], (N_TIMEPOINTS, 1))
    switching = np.empty_like(fixed)
    switching[:200] = np.eye(N_DIMENSIONS)[0]
    switching[200:400] = np.eye(N_DIMENSIONS)[1]
    switching[400:] = np.eye(N_DIMENSIONS)[0]

    angle = np.linspace(0, 8 * np.pi, N_TIMEPOINTS)
    circular = np.zeros_like(fixed)
    circular[:, 0] = np.cos(angle)
    circular[:, 1] = np.sin(angle)

    rng = np.random.default_rng(42)
    wandering = rng.normal(size=(N_TIMEPOINTS, N_DIMENSIONS))
    wandering /= np.linalg.norm(wandering, axis=1, keepdims=True)
    return {
        "fixed": fixed,
        "switching": switching,
        "circular": circular,
        "wandering": wandering,
    }


def main() -> None:
    results = {}
    for name, vectors in trajectories().items():
        result = summarize_leida_landscape(
            vectors, repetition_time=1.0, recurrence_exclusion=20
        )
        results[name] = result.__dict__
    gates = {
        "fixed_dimension_is_one": abs(results["fixed"]["effective_dimension"] - 1) < 1e-10,
        "switching_dimension_exceeds_fixed": results["switching"]["effective_dimension"] > results["fixed"]["effective_dimension"],
        "wandering_dimension_exceeds_switching": results["wandering"]["effective_dimension"] > results["switching"]["effective_dimension"],
        "wandering_dispersion_exceeds_switching": results["wandering"]["repertoire_dispersion"] > results["switching"]["repertoire_dispersion"],
        "wandering_speed_exceeds_circular": results["wandering"]["mean_speed"] > results["circular"]["mean_speed"],
        "circular_recurrence_closer_than_wandering": results["circular"]["mean_nearest_recurrence_distance"] < results["wandering"]["mean_nearest_recurrence_distance"],
    }
    summary = {
        "definitions": {
            "distance": "projective angular distance in radians; v and -v identical",
            "dispersion": "mean distance between all pairs of trajectory points",
            "effective_dimension": "participation ratio of the mean projective scatter matrix",
            "speed": "consecutive distance divided by repetition time",
            "recurrence": "nearest distance outside a 20-sample temporal neighborhood",
        },
        "results": results,
        "validation_gates": {key: bool(value) for key, value in gates.items()},
        "all_gates_passed": bool(all(gates.values())),
    }
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIRECTORY / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    metrics = ("repertoire_dispersion", "effective_dimension", "mean_speed", "mean_nearest_recurrence_distance")
    figure, axes = plt.subplots(1, 4, figsize=(14, 3.8), constrained_layout=True)
    names = list(results)
    colors = ["#6E87A5", "#A77A2D", "#4F8A70", "#B23A48"]
    for axis, metric in zip(axes, metrics, strict=True):
        axis.bar(names, [results[name][metric] for name in names], color=colors)
        axis.set_title(metric.replace("_", " ").title(), fontsize=9, fontweight="bold")
        axis.tick_params(axis="x", rotation=35)
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Continuous LEiDA landscape measurement validation", fontweight="bold")
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    if not summary["all_gates_passed"]:
        raise RuntimeError("one or more continuous-landscape gates failed")
    print(f"Saved summary to: {OUTPUT_DIRECTORY / 'summary.json'}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
