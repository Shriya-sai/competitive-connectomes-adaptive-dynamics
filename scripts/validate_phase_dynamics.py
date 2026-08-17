"""Validate Phase 3 phase-dynamics measurements on known synthetic regimes."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import phase_dynamics


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "results" / "phase_dynamics_validation"
FIGURE_PATH = ROOT / "figures" / "phase_dynamics_validation.png"

N_REGIONS = 100
N_TIMEPOINTS = 2000
TRIM = 100


def synthetic_regimes() -> dict[str, np.ndarray]:
    time = np.arange(N_TIMEPOINTS, dtype=np.float64)
    carrier = 2 * np.pi * 0.03 * time
    offsets = np.linspace(0, 2 * np.pi, N_REGIONS, endpoint=False)

    synchronized = np.repeat(np.cos(carrier)[None, :], N_REGIONS, axis=0)
    dispersed = np.cos(carrier[None, :] + offsets[:, None])

    modulation = (1 - np.cos(2 * np.pi * time / 500)) / 2
    switching_phases = carrier[None, :] + offsets[:, None] * modulation[None, :]
    switching = np.cos(switching_phases)

    rng = np.random.default_rng(42)
    random_offsets = rng.uniform(0, 2 * np.pi, size=(N_REGIONS, N_TIMEPOINTS))
    random_phase = np.cos(carrier[None, :] + random_offsets)
    return {
        "synchronized": synchronized,
        "dispersed": dispersed,
        "switching": switching,
        "random_phase": random_phase,
    }


def main() -> None:
    results = {}
    dynamics = {}
    for name, signals in synthetic_regimes().items():
        result = phase_dynamics(signals, trim=TRIM)
        dynamics[name] = result
        results[name] = {
            "synchrony": result.synchrony,
            "metastability": result.metastability,
            "maximum_synchrony": result.maximum_synchrony,
            "minimum_order_parameter": float(result.order_parameter[TRIM:-TRIM].min()),
            "maximum_order_parameter": float(result.order_parameter[TRIM:-TRIM].max()),
        }

    gates = {
        "synchronized_high_synchrony": results["synchronized"]["synchrony"] > 0.99,
        "synchronized_low_metastability": results["synchronized"]["metastability"] < 0.01,
        "dispersed_low_synchrony": results["dispersed"]["synchrony"] < 0.05,
        "switching_high_metastability": results["switching"]["metastability"] > 0.20,
        "switching_visits_aligned_state": results["switching"]["maximum_order_parameter"] > 0.90,
        "switching_visits_dispersed_state": results["switching"]["minimum_order_parameter"] < 0.15,
        "random_phase_low_synchrony": results["random_phase"]["synchrony"] < 0.20,
    }
    output = {"definitions": {"synchrony": "mean R(t)", "metastability": "population SD of R(t)"}, "trim_samples_per_edge": TRIM, "results": results, "validation_gates": gates, "all_gates_passed": all(gates.values())}

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIRECTORY / "summary.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    colors = {"synchronized": "#2E5D7B", "dispersed": "#A77A2D", "switching": "#B23A48", "random_phase": "#777777"}
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.7), constrained_layout=True)
    shown = slice(TRIM, 900)
    for name, result in dynamics.items():
        axes[0].plot(result.order_parameter[shown], label=name.replace("_", " ").title(), color=colors[name], alpha=0.85)
    axes[0].set_xlabel("Synthetic timepoint")
    axes[0].set_ylabel("Kuramoto order parameter R(t)")
    axes[0].set_title("Known coordination regimes", fontweight="bold")
    axes[0].legend(frameon=False, fontsize=8)

    names = list(results)
    x = np.arange(len(names))
    width = 0.36
    axes[1].bar(x - width / 2, [results[name]["synchrony"] for name in names], width, label="Synchrony", color="#2E5D7B")
    axes[1].bar(x + width / 2, [results[name]["metastability"] for name in names], width, label="Metastability", color="#B23A48")
    axes[1].set_xticks(x, [name.replace("_", "\n").title() for name in names])
    axes[1].set_ylabel("Metric value")
    axes[1].set_title("Recovered summary measurements", fontweight="bold")
    axes[1].legend(frameon=False)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Phase-dynamics measurement validation", fontweight="bold")
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(output, indent=2))
    if not output["all_gates_passed"]:
        raise RuntimeError("one or more phase-dynamics validation gates failed")
    print(f"Saved summary to: {OUTPUT_DIRECTORY / 'summary.json'}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
