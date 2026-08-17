"""Validate the frozen minimal relative-phase prediction instrument synthetically."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import eigvalsh
from scipy.signal import butter, hilbert, sosfiltfilt
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs" / "phase_prediction_instrument.json").read_text())
OUT = ROOT / "results" / "phase_prediction_instrument"
FIGURE = ROOT / "figures" / "phase_prediction_instrument_validation.png"
SFREQ = float(CONFIG["sampling_frequency_hz"])
TIMES = np.arange(-2.5, 2.3 + 1 / SFREQ, 1 / SFREQ)
RESPONSE = (TIMES >= 0) & (TIMES <= CONFIG["response_seconds"])
RESPONSE_TIMES = TIMES[RESPONSE]
SUMMARY_WINDOW = (RESPONSE_TIMES >= 0.05) & (RESPONSE_TIMES <= 0.30)
N = int(CONFIG["channels"])
SOS = butter(4, [4.0, 8.0], btype="bandpass", fs=SFREQ, output="sos")


def circular_interpolate(start: np.ndarray, stop: np.ndarray, amount: np.ndarray) -> np.ndarray:
    return start + np.angle(np.exp(1j * (stop - start))) * amount


def smooth_noise(rng: np.random.Generator, shape: tuple[int, int], scale: float) -> np.ndarray:
    if scale == 0:
        return np.zeros(shape)
    white = rng.normal(size=shape)
    kernel = np.ones(33) / 33
    values = np.apply_along_axis(lambda row: np.convolve(row, kernel, mode="same"), 1, white)
    values /= np.maximum(values.std(axis=1, keepdims=True), 1e-12)
    return scale * values


def generate_trial(seed: int, base: np.ndarray, target: np.ndarray, *, magnitude: float,
                   onset: float = 0.0, frequency_sd: float = 0.0,
                   frequency_change_sd: float = 0.0, phase_noise: float = 0.0,
                   sensor_noise: float = 0.01, mixing: float = 0.0,
                   amplitude: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    frequencies = 6.0 + rng.normal(0, frequency_sd, N)
    post_frequency_change = rng.normal(0, frequency_change_sd, N)
    transition = np.clip((TIMES - onset) / 0.05, 0, 1)
    response_offsets = circular_interpolate(base, target, np.asarray(magnitude))
    offsets = circular_interpolate(base[:, None], response_offsets[:, None], transition[None, :])
    positive_time = np.maximum(TIMES - onset, 0)
    phase = 2 * np.pi * frequencies[:, None] * TIMES + offsets
    phase += 2 * np.pi * post_frequency_change[:, None] * positive_time
    phase += smooth_noise(rng, phase.shape, phase_noise)
    signals = amplitude * np.sin(phase)
    signals = (1 - mixing) * signals + mixing * signals.mean(axis=0, keepdims=True)
    signals += rng.normal(0, sensor_noise, signals.shape)
    filtered = sosfiltfilt(SOS, signals, axis=-1)
    observed_phase = np.unwrap(np.angle(hilbert(filtered, axis=-1)), axis=-1)
    return filtered, observed_phase


def predict_curve(phases: np.ndarray, baseline_seconds: float) -> np.ndarray:
    baseline = (TIMES >= -baseline_seconds) & (TIMES < 0)
    t = TIMES[baseline]
    centered = t - t.mean()
    values = phases[:, baseline]
    slopes = (values @ centered) / np.dot(centered, centered)
    intercepts = values.mean(axis=1) - slopes * t.mean()
    predicted = intercepts[:, None] + slopes[:, None] * RESPONSE_TIMES
    residual = phases[:, RESPONSE] - predicted
    resultant_squared = np.abs(np.exp(1j * residual).sum(axis=0)) ** 2
    pair_agreement = (resultant_squared - N) / (N * (N - 1))
    return 1.0 - pair_agreement


def old_metric(phases: np.ndarray) -> float:
    baseline = (TIMES >= -0.3) & (TIMES <= -0.2)
    upper = np.triu_indices(N, k=1)
    base_pair = np.exp(1j * (phases[upper[0]][:, baseline] - phases[upper[1]][:, baseline])).mean(1)
    base_unit = base_pair / np.maximum(np.abs(base_pair), 1e-12)
    response_pair = np.exp(1j * (phases[upper[0]][:, RESPONSE] - phases[upper[1]][:, RESPONSE]))
    return float(1 - np.real(response_pair * np.conj(base_unit[:, None])).mean())


def covariance_spd(signals: np.ndarray, mask: np.ndarray) -> np.ndarray:
    cov = np.cov(signals[:, mask])
    return 0.9 * cov + 0.1 * np.trace(cov) / N * np.eye(N)


def riemann_distance(signals: np.ndarray, horizon: float) -> float:
    post = (TIMES >= 0) & (TIMES <= horizon)
    pre = (TIMES >= -horizon) & (TIMES < 0)
    vals = np.maximum(eigvalsh(covariance_spd(signals, post), covariance_spd(signals, pre)), 1e-12)
    return float(np.linalg.norm(np.log(vals)) / np.sqrt(N))


def curve_value(curve: np.ndarray, horizon: float) -> float:
    return float(curve[np.argmin(np.abs(RESPONSE_TIMES - horizon))])


def trial_summary(curve: np.ndarray) -> float:
    """Frozen empirical endpoint: mean excess topology error from 50--300 ms."""
    return float(np.mean(curve[SUMMARY_WINDOW]))


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    pooled = np.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1)) / (len(a)+len(b)-2))
    return float((b.mean() - a.mean()) / max(pooled, 1e-12))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True); FIGURE.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(CONFIG["seed"])
    base = rng.uniform(-np.pi, np.pi, N); target = rng.uniform(-np.pi, np.pi, N)
    horizons = CONFIG["horizons_seconds"]; trials = int(CONFIG["trials_per_condition"])
    combined = CONFIG["combined_realistic"]
    rows, curves = [], {}

    # Primary clean and combined magnitude series, with matched zero counterfactuals for covariance.
    for regime, params in [("clean", {}), ("combined_realistic", combined)]:
        for magnitude in CONFIG["magnitudes"]:
            for trial in range(trials):
                seed = int(rng.integers(2**31 - 1))
                kwargs = dict(magnitude=magnitude, onset=params.get("perturbation_timing_seconds", 0),
                              frequency_sd=params.get("frequency_sd_hz", 0), phase_noise=params.get("phase_noise_sd_rad", 0),
                              sensor_noise=params.get("sensor_noise_sd", 0.01), mixing=params.get("mixing", 0),
                              amplitude=params.get("amplitude", 1.0))
                signals, phases = generate_trial(seed, base, target, **kwargs)
                null_signals, _ = generate_trial(seed, base, target, **{**kwargs, "magnitude": 0.0})
                curve = predict_curve(phases, params.get("baseline_seconds", 1.3))
                curves[(regime, magnitude, trial)] = curve
                for horizon in horizons:
                    rows.append({"family":"magnitude", "regime":regime, "level":magnitude, "trial":trial,
                                 "horizon":horizon, "prediction_error":curve_value(curve,horizon),
                                 "old_metric":np.nan,
                                 "riemann_excess":riemann_distance(signals,horizon)-riemann_distance(null_signals,horizon)})

    # Crucial heterogeneous ordinary-evolution zero and one-factor zero tests.
    factor_specs = {
        "frequency_sd": CONFIG["frequency_sd_hz"], "phase_noise": CONFIG["phase_noise_sd_rad"],
        "frequency_change_sd": CONFIG["frequency_change_sd_hz"],
        "sensor_noise": CONFIG["sensor_noise_sd"], "mixing": CONFIG["mixing"],
        "amplitude": CONFIG["amplitudes"], "baseline_seconds": CONFIG["baseline_seconds"]}
    for factor, levels in factor_specs.items():
        for level in levels:
            for trial in range(trials):
                seed = int(rng.integers(2**31 - 1)); kwargs = {"magnitude":0.0}
                if factor != "baseline_seconds": kwargs[factor] = level
                _, phases = generate_trial(seed, base, target, **kwargs)
                curve = predict_curve(phases, level if factor == "baseline_seconds" else 1.3)
                frozen_value = old_metric(phases) if factor == "frequency_sd" and level == 0.35 else np.nan
                for horizon in horizons:
                    rows.append({"family":"zero_factor", "regime":factor, "level":level, "trial":trial,
                                 "horizon":horizon, "prediction_error":curve_value(curve,horizon),
                                 "old_metric":frozen_value, "riemann_excess":np.nan})

    # Baseline-length interaction with the combined realistic condition.
    for baseline_seconds in CONFIG["baseline_seconds"]:
        for magnitude in (0.0, 0.75):
            for trial in range(trials):
                seed = int(rng.integers(2**31 - 1))
                _, phases = generate_trial(
                    seed, base, target, magnitude=magnitude,
                    frequency_sd=combined["frequency_sd_hz"],
                    phase_noise=combined["phase_noise_sd_rad"],
                    sensor_noise=combined["sensor_noise_sd"], mixing=combined["mixing"],
                    amplitude=combined["amplitude"],
                )
                curve = predict_curve(phases, baseline_seconds)
                for horizon in horizons:
                    rows.append({"family":f"combined_baseline_magnitude_{magnitude}", "regime":"baseline_seconds",
                                 "level":baseline_seconds, "trial":trial, "horizon":horizon,
                                 "prediction_error":curve_value(curve,horizon), "old_metric":np.nan,
                                 "riemann_excess":np.nan})

    # Clean perturbation-timing localization.
    timing_errors = []
    for onset in CONFIG["timings_seconds"]:
        for trial in range(trials):
            seed = int(rng.integers(2**31 - 1))
            _, phases = generate_trial(seed, base, target, magnitude=1.0, onset=onset)
            curve = predict_curve(phases, 1.3)
            candidates = np.flatnonzero((RESPONSE_TIMES >= 0.02) & (curve >= 0.10))
            detected = float(RESPONSE_TIMES[candidates[0]]) if len(candidates) else np.nan
            timing_errors.append({"onset":onset,"trial":trial,"detected":detected,
                                  "absolute_error":abs(detected-onset) if np.isfinite(detected) else np.nan,
                                  "trial_summary_50_300_ms":trial_summary(curve)})

    with (OUT/"synthetic_scores.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with (OUT/"timing_localization.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(timing_errors[0])); writer.writeheader(); writer.writerows(timing_errors)

    gate_rows=[]; g=CONFIG["gate"]
    combined_rows=[r for r in rows if r["family"]=="magnitude" and r["regime"]=="combined_realistic"]
    for horizon in horizons:
        by_level={level:np.array([r["prediction_error"] for r in combined_rows if r["level"]==level and r["horizon"]==horizon]) for level in CONFIG["magnitudes"]}
        means=np.array([by_level[x].mean() for x in CONFIG["magnitudes"]])
        rho=float(spearmanr(CONFIG["magnitudes"],means).statistic)
        first=np.array([np.mean([curves[("combined_realistic",level,t)][np.argmin(abs(RESPONSE_TIMES-horizon))] for t in range(trials//2)]) for level in CONFIG["magnitudes"]])
        second=np.array([np.mean([curves[("combined_realistic",level,t)][np.argmin(abs(RESPONSE_TIMES-horizon))] for t in range(trials//2,trials)]) for level in CONFIG["magnitudes"]])
        reliability=float(spearmanr(first,second).statistic)
        null=by_level[0.0]; separation=cohens_d(null,by_level[1.0])
        passed=(np.median(null)<=g["null_median_max"] and np.quantile(null,.95)<=g["null_p95_max"] and rho>=g["magnitude_spearman_min"] and separation>=g["cohens_d_min"] and reliability>=g["split_seed_reliability_min"])
        gate_rows.append({"horizon":horizon,"null_median":float(np.median(null)),"null_p95":float(np.quantile(null,.95)),
                          "magnitude_spearman":rho,"cohens_d_full_vs_zero":separation,"split_seed_reliability":reliability,"passed":bool(passed)})
    median_timing=float(np.nanmedian([x["absolute_error"] for x in timing_errors]))
    valid=[x["horizon"] for x in gate_rows if x["passed"] and x["horizon"]>=g["minimum_valid_horizon_seconds"]]
    endpoint_by_level = {
        level: np.array([trial_summary(curves[("combined_realistic", level, trial)])
                         for trial in range(trials)])
        for level in CONFIG["magnitudes"]
    }
    endpoint_means = np.array([endpoint_by_level[level].mean() for level in CONFIG["magnitudes"]])
    endpoint_rho = float(spearmanr(CONFIG["magnitudes"], endpoint_means).statistic)
    endpoint_first = np.array([
        np.mean([trial_summary(curves[("combined_realistic", level, trial)])
                 for trial in range(trials // 2)])
        for level in CONFIG["magnitudes"]
    ])
    endpoint_second = np.array([
        np.mean([trial_summary(curves[("combined_realistic", level, trial)])
                 for trial in range(trials // 2, trials)])
        for level in CONFIG["magnitudes"]
    ])
    endpoint_reliability = float(spearmanr(endpoint_first, endpoint_second).statistic)
    endpoint_null = endpoint_by_level[0.0]
    endpoint_d = cohens_d(endpoint_null, endpoint_by_level[1.0])
    timing_summary_means = {
        str(onset): float(np.mean([row["trial_summary_50_300_ms"] for row in timing_errors
                                   if row["onset"] == onset]))
        for onset in CONFIG["timings_seconds"]
    }
    timing_order_rho = float(spearmanr(
        CONFIG["timings_seconds"],
        [timing_summary_means[str(onset)] for onset in CONFIG["timings_seconds"]],
    ).statistic)
    late_onsets = [onset for onset in CONFIG["timings_seconds"] if onset >= 0.5]
    timing_specificity_passed = (
        timing_order_rho <= -0.8
        and max(timing_summary_means[str(onset)] for onset in late_onsets) <= g["null_median_max"]
    )
    endpoint_passed = (
        np.median(endpoint_null) <= g["null_median_max"]
        and np.quantile(endpoint_null, .95) <= g["null_p95_max"]
        and endpoint_rho >= g["magnitude_spearman_min"]
        and endpoint_d >= g["cohens_d_min"]
        and endpoint_reliability >= g["split_seed_reliability_min"]
        and timing_specificity_passed
    )
    endpoint_validation = {
        "definition": "mean E(t) from 0.05 through 0.30 seconds inclusive",
        "null_median": float(np.median(endpoint_null)),
        "null_p95": float(np.quantile(endpoint_null, .95)),
        "magnitude_spearman": endpoint_rho,
        "cohens_d_full_vs_zero": endpoint_d,
        "split_seed_reliability": endpoint_reliability,
        "timing_summary_means": timing_summary_means,
        "timing_order_spearman": timing_order_rho,
        "timing_specificity_passed": bool(timing_specificity_passed),
        "passed": bool(endpoint_passed),
    }
    summary={"status":"completed_against_frozen_gate","construct":CONFIG["construct"],"horizon_gates":gate_rows,
             "median_timing_error_seconds":median_timing,"timing_gate_passed":median_timing<=g["timing_error_seconds_max"],
             "instrument_gate_passed":bool(valid) and median_timing<=g["timing_error_seconds_max"],
             "longest_valid_horizon_seconds":max(valid) if valid else None,
             "trial_endpoint_validation": endpoint_validation}
    (OUT/"validation_summary.json").write_text(json.dumps(summary,indent=2)+"\n")

    fig,axes=plt.subplots(2,2,figsize=(11,8))
    for magnitude in CONFIG["magnitudes"]:
        values=np.stack([curves[("combined_realistic",magnitude,t)] for t in range(trials)])
        axes[0,0].plot(RESPONSE_TIMES,values.mean(0),label=str(magnitude))
    axes[0,0].set(title="Combined realistic: time-resolved error",ylabel="E(t)",xlabel="Prediction horizon (s)"); axes[0,0].legend(title="Change")
    zero=np.stack([curves[("combined_realistic",0.0,t)] for t in range(trials)])
    axes[0,1].plot(RESPONSE_TIMES,np.median(zero,0)); axes[0,1].fill_between(RESPONSE_TIMES,np.quantile(zero,.05,0),np.quantile(zero,.95,0),alpha=.25)
    axes[0,1].axhline(g["null_median_max"],ls="--",color="red"); axes[0,1].set(title="Zero-change prediction horizon",ylabel="E(t)",xlabel="Time (s)")
    axes[1,0].plot([x["horizon"] for x in gate_rows],[x["magnitude_spearman"] for x in gate_rows],marker="o",label="Phase prediction")
    benchmark=[]
    for h in horizons:
        means=[np.mean([r["riemann_excess"] for r in combined_rows if r["level"]==level and r["horizon"]==h]) for level in CONFIG["magnitudes"]]
        benchmark.append(spearmanr(CONFIG["magnitudes"],means).statistic)
    axes[1,0].plot(horizons,benchmark,marker="o",label="Riemann benchmark"); axes[1,0].axhline(.8,ls="--",color="gray"); axes[1,0].set(title="Known-magnitude ordering",ylabel="Spearman rho",xlabel="Horizon (s)"); axes[1,0].legend()
    hetero=[r for r in rows if r["family"]=="zero_factor" and r["regime"]=="frequency_sd" and r["level"]==.35 and r["horizon"]==1.3]
    axes[1,1].boxplot([[r["old_metric"] for r in hetero],[r["prediction_error"] for r in hetero]],tick_labels=["Old metric","New predictor"])
    axes[1,1].set(title="Crucial heterogeneous zero condition",ylabel="Reported reconfiguration")
    fig.suptitle("Minimal relative-phase prediction instrument validation"); fig.tight_layout(); fig.savefig(FIGURE,dpi=180)
    print(json.dumps(summary,indent=2))


if __name__ == "__main__": main()
