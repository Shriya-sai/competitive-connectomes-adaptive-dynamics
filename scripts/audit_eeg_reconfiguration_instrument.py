"""Exploratory synthetic audit of the failed EEG phase-reconfiguration metric.

This does not modify or rerun the frozen confirmation gate. It asks whether the
exact estimator used there recovers known phase-pattern changes under increasingly
realistic theta-signal conditions.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "results" / "eeg_reconfiguration_instrument_audit"
FIGURE = ROOT / "figures" / "eeg_reconfiguration_instrument_audit.png"
SEED = 20260811
SFREQ = 512.0
TIMES = np.arange(-1.5, 3.0 + 1.0 / SFREQ, 1.0 / SFREQ)
BASELINE = (TIMES >= -0.3) & (TIMES <= -0.2)
RESPONSE = (TIMES >= 0.2) & (TIMES <= 1.5)
N_CHANNELS = 64
N_TRIALS = 12
LEVELS = np.asarray([0.0, 0.25, 0.5, 0.75, 1.0])
SCENARIOS = {
    "ideal": {"frequency_sd": 0.0, "phase_noise": 0.0, "sensor_noise": 0.01, "mixing": 0.0},
    "frequency_drift": {"frequency_sd": 0.35, "phase_noise": 0.0, "sensor_noise": 0.01, "mixing": 0.0},
    "phase_noise": {"frequency_sd": 0.0, "phase_noise": 0.35, "sensor_noise": 0.05, "mixing": 0.0},
    "volume_mixing": {"frequency_sd": 0.0, "phase_noise": 0.1, "sensor_noise": 0.05, "mixing": 0.4},
    "combined_realistic": {"frequency_sd": 0.35, "phase_noise": 0.35, "sensor_noise": 0.10, "mixing": 0.4},
}


def circular_interpolate(start: np.ndarray, stop: np.ndarray, amount: float) -> np.ndarray:
    delta = np.angle(np.exp(1j * (stop - start)))
    return start + amount * delta


def smooth_noise(rng: np.random.Generator, scale: float) -> np.ndarray:
    if scale == 0:
        return np.zeros((N_CHANNELS, len(TIMES)))
    white = rng.normal(size=(N_CHANNELS, len(TIMES)))
    kernel = np.ones(33) / 33.0
    smoothed = np.apply_along_axis(lambda row: np.convolve(row, kernel, mode="same"), 1, white)
    smoothed /= np.maximum(smoothed.std(axis=1, keepdims=True), 1e-12)
    return scale * smoothed


def synthesize_trial(
    rng: np.random.Generator,
    base_offsets: np.ndarray,
    target_offsets: np.ndarray,
    level: float,
    scenario: dict[str, float],
) -> tuple[np.ndarray, np.ndarray]:
    response_offsets = circular_interpolate(base_offsets, target_offsets, level)
    blend = np.clip((TIMES + 0.2) / 0.4, 0.0, 1.0)
    offsets = circular_interpolate(base_offsets[:, None], response_offsets[:, None], blend[None, :])
    frequencies = 6.0 + rng.normal(0.0, scenario["frequency_sd"], N_CHANNELS)
    phases = 2.0 * np.pi * frequencies[:, None] * TIMES[None, :] + offsets
    phases += smooth_noise(rng, scenario["phase_noise"])
    signals = np.sin(phases)
    common = signals.mean(axis=0, keepdims=True)
    signals = (1.0 - scenario["mixing"]) * signals + scenario["mixing"] * common
    signals += rng.normal(0.0, scenario["sensor_noise"], signals.shape)
    sos = butter(4, [4.0, 8.0], btype="bandpass", fs=SFREQ, output="sos")
    filtered = sosfiltfilt(sos, signals, axis=-1)
    return filtered, np.angle(hilbert(filtered, axis=-1))


def current_metric(phases: np.ndarray) -> float:
    upper = np.triu_indices(phases.shape[0], k=1)
    baseline_pair = np.exp(
        1j * (phases[upper[0]][:, BASELINE] - phases[upper[1]][:, BASELINE])
    ).mean(axis=1)
    baseline_unit = baseline_pair / np.maximum(np.abs(baseline_pair), 1e-12)
    response_pair = np.exp(
        1j * (phases[upper[0]][:, RESPONSE] - phases[upper[1]][:, RESPONSE])
    )
    similarity = np.real(response_pair * np.conj(baseline_unit[:, None])).mean()
    return float(1.0 - similarity)


def true_pattern_distance(base: np.ndarray, target: np.ndarray, level: float) -> float:
    response = circular_interpolate(base, target, level)
    upper = np.triu_indices(len(base), k=1)
    base_pair = base[upper[0]] - base[upper[1]]
    response_pair = response[upper[0]] - response[upper[1]]
    return float(1.0 - np.cos(response_pair - base_pair).mean())


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    base_offsets = rng.uniform(-np.pi, np.pi, N_CHANNELS)
    target_offsets = rng.uniform(-np.pi, np.pi, N_CHANNELS)
    rows: list[dict[str, object]] = []
    for scenario_name, scenario in SCENARIOS.items():
        for level in LEVELS:
            truth = true_pattern_distance(base_offsets, target_offsets, float(level))
            for trial in range(N_TRIALS):
                _, phases = synthesize_trial(
                    rng, base_offsets, target_offsets, float(level), scenario
                )
                rows.append(
                    {
                        "scenario": scenario_name,
                        "level": float(level),
                        "trial": trial + 1,
                        "true_pattern_distance": truth,
                        "measured_reconfiguration": current_metric(phases),
                    }
                )

    with (RESULT_DIR / "trial_metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summaries = []
    for scenario_name in SCENARIOS:
        scenario_rows = [row for row in rows if row["scenario"] == scenario_name]
        means = []
        for level in LEVELS:
            values = np.asarray(
                [
                    row["measured_reconfiguration"]
                    for row in scenario_rows
                    if row["level"] == float(level)
                ]
            )
            means.append(float(values.mean()))
        rho = float(spearmanr(LEVELS, means).statistic)
        null_values = np.asarray(
            [row["measured_reconfiguration"] for row in scenario_rows if row["level"] == 0.0]
        )
        dynamic_range = float(max(means) - min(means))
        summaries.append(
            {
                "scenario": scenario_name,
                "means_by_level": dict(zip([str(value) for value in LEVELS], means, strict=True)),
                "null_mean": float(null_values.mean()),
                "null_sd": float(null_values.std(ddof=1)),
                "dynamic_range": dynamic_range,
                "spearman_level_vs_mean": rho,
                "null_near_zero": float(null_values.mean()) < 0.10,
                "monotonic": all(right > left for left, right in zip(means, means[1:])),
                "usable_dynamic_range": dynamic_range >= 0.25,
            }
        )

    audit = {
        "status": "exploratory_instrument_audit_after_frozen_failure",
        "seed": SEED,
        "channels": N_CHANNELS,
        "trials_per_level": N_TRIALS,
        "levels": LEVELS.tolist(),
        "criteria": {
            "null_near_zero": "mean < 0.10",
            "monotonic": "strict increase at every known-change level",
            "usable_dynamic_range": "max(level mean) - min(level mean) >= 0.25",
        },
        "scenarios": summaries,
    }
    (RESULT_DIR / "audit_summary.json").write_text(json.dumps(audit, indent=2) + "\n")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for summary in summaries:
        means = [summary["means_by_level"][str(value)] for value in LEVELS]
        ax.plot(LEVELS, means, marker="o", linewidth=2, label=summary["scenario"].replace("_", " "))
    truth = [true_pattern_distance(base_offsets, target_offsets, float(level)) for level in LEVELS]
    ax.plot(LEVELS, truth, color="black", linestyle="--", linewidth=2, label="known pattern distance")
    ax.axhspan(0.9, 1.0, color="#d95f5f", alpha=0.10, label="empirical near-ceiling band")
    ax.set_xlabel("Known reconfiguration level")
    ax.set_ylabel("Measured phase-pattern reconfiguration")
    ax.set_title("Synthetic audit of the frozen EEG reconfiguration metric")
    ax.set_ylim(-0.03, 1.08)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=180)
    plt.close(fig)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
