"""Compare drift-calibrated EEG reconfiguration estimators on known synthetic changes."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import eigvalsh
from scipy.stats import spearmanr

from audit_eeg_reconfiguration_instrument import (
    LEVELS,
    N_CHANNELS,
    N_TRIALS,
    SCENARIOS,
    SEED,
    TIMES,
    synthesize_trial,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "eeg_reconfiguration_estimator_comparison"
FIGURE = ROOT / "figures" / "eeg_reconfiguration_estimator_comparison.png"
PRE = (TIMES >= -1.5) & (TIMES <= -0.2)
POST = (TIMES >= 0.2) & (TIMES <= 1.5)


def plv_matrix(phases: np.ndarray) -> np.ndarray:
    unit = np.exp(1j * phases)
    return np.abs(unit @ unit.conj().T / phases.shape[1])


def wpli_matrix(phases: np.ndarray) -> np.ndarray:
    unit = np.exp(1j * phases)
    cross_imag = np.imag(unit[:, None, :] * unit[None, :, :].conj())
    numerator = np.abs(cross_imag.mean(axis=-1))
    denominator = np.abs(cross_imag).mean(axis=-1)
    return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 1e-12)


def leida_projector_mean(phases: np.ndarray) -> np.ndarray:
    projectors = []
    for point in range(0, phases.shape[1], 16):
        vector = np.exp(1j * phases[:, point])
        coherence = np.real(vector[:, None] * vector[None, :].conj())
        values, vectors = np.linalg.eigh(coherence)
        lead = vectors[:, np.argmax(values)]
        projectors.append(np.outer(lead, lead))
    return np.mean(projectors, axis=0)


def covariance_spd(signals: np.ndarray) -> np.ndarray:
    covariance = np.cov(signals)
    shrink = 0.10 * np.trace(covariance) / len(covariance)
    return 0.90 * covariance + shrink * np.eye(len(covariance))


def frobenius_distance(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.linalg.norm(left - right, ord="fro") / np.sqrt(N_CHANNELS * (N_CHANNELS - 1)))


def riemannian_distance(left: np.ndarray, right: np.ndarray) -> float:
    eigenvalues = np.maximum(eigvalsh(right, left), 1e-12)
    return float(np.linalg.norm(np.log(eigenvalues)) / np.sqrt(N_CHANNELS))


def metrics(signals: np.ndarray, phases: np.ndarray) -> dict[str, float]:
    pre_phase, post_phase = phases[:, PRE], phases[:, POST]
    pre_signal, post_signal = signals[:, PRE], signals[:, POST]
    return {
        "equal_window_plv": frobenius_distance(plv_matrix(pre_phase), plv_matrix(post_phase)),
        "equal_window_wpli": frobenius_distance(wpli_matrix(pre_phase), wpli_matrix(post_phase)),
        "leida_distribution": float(
            np.linalg.norm(leida_projector_mean(pre_phase) - leida_projector_mean(post_phase), ord="fro")
        ),
        "riemannian_covariance": riemannian_distance(covariance_spd(pre_signal), covariance_spd(post_signal)),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    base = rng.uniform(-np.pi, np.pi, N_CHANNELS)
    target = rng.uniform(-np.pi, np.pi, N_CHANNELS)
    rows = []
    for scenario_name, scenario in SCENARIOS.items():
        for level in LEVELS:
            for trial in range(N_TRIALS):
                paired_seed = int(rng.integers(0, np.iinfo(np.int32).max))
                signals, phases = synthesize_trial(
                    np.random.default_rng(paired_seed), base, target, float(level), scenario
                )
                null_signals, null_phases = synthesize_trial(
                    np.random.default_rng(paired_seed), base, target, 0.0, scenario
                )
                observed = metrics(signals, phases)
                expected = metrics(null_signals, null_phases)
                for estimator, value in observed.items():
                    rows.append({
                        "scenario": scenario_name,
                        "level": float(level),
                        "trial": trial + 1,
                        "estimator": estimator,
                        "raw_distance": value,
                        "matched_expected_drift": expected[estimator],
                        "excess_distance": value - expected[estimator],
                    })

    estimators = sorted({row["estimator"] for row in rows})
    summaries = []
    for scenario in SCENARIOS:
        for estimator in estimators:
            subset = [row for row in rows if row["scenario"] == scenario and row["estimator"] == estimator]
            means = []
            for level in LEVELS:
                eligible = [row for row in subset if row["level"] == float(level)]
                means.append(float(np.mean([row["excess_distance"] for row in eligible])))
            dynamic_range = max(means) - min(means)
            summaries.append({
                "scenario": scenario, "estimator": estimator,
                "mean_matched_expected_drift": float(np.mean([row["matched_expected_drift"] for row in subset])),
                "excess_means_by_level": dict(zip([str(x) for x in LEVELS], means, strict=True)),
                "null_excess": means[0], "dynamic_range": float(dynamic_range),
                "spearman": float(spearmanr(LEVELS, means).statistic),
                "monotonic": all(b > a for a, b in zip(means, means[1:])),
            })
    with (OUT / "trial_metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    result = {"status": "exploratory_post_failure_comparison", "equal_window_seconds": 1.3,
              "drift_calibration": "paired counterfactual preserving frequencies, noise and mixing", "summaries": summaries}
    (OUT / "summary.json").write_text(json.dumps(result, indent=2) + "\n")

    fig, axes = plt.subplots(2, 2, figsize=(11, 8), sharex=True)
    for ax, estimator in zip(axes.flat, estimators, strict=True):
        for scenario in SCENARIOS:
            summary = next(x for x in summaries if x["scenario"] == scenario and x["estimator"] == estimator)
            ax.plot(LEVELS, [summary["excess_means_by_level"][str(x)] for x in LEVELS], marker="o", label=scenario.replace("_", " "))
        ax.axhline(0, color="black", linewidth=1, linestyle="--")
        ax.set_title(estimator.replace("_", " "))
        ax.set_ylabel("Excess over expected drift")
    for ax in axes[-1]: ax.set_xlabel("Known reconfiguration level")
    axes[0, 0].legend(frameon=False, fontsize=8)
    fig.suptitle("Drift-calibrated comparison of EEG reconfiguration estimators")
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=180)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
