"""Run frozen EEG phase-prediction technical confirmation protocol v1.0.0."""

from __future__ import annotations

import csv
import gc
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import mne
import numpy as np
from mne.preprocessing import ICA, compute_current_source_density
from scipy.io import loadmat
from scipy.linalg import eigvalsh
from scipy.signal import hilbert


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "eeg_phase_prediction_confirmation.json"
LOCK_PATH = ROOT / "results" / "eeg_phase_prediction_confirmation" / "protocol_lock.json"
CONFIG = json.loads(CONFIG_PATH.read_text())
DATA = ROOT / "data" / "public_reversal_eeg_pilot"
META = DATA / "metadata"
OUT = ROOT / "results" / "eeg_phase_prediction_confirmation"
FIGURE = ROOT / "figures" / "eeg_phase_prediction_confirmation.png"
ROI = ["Fz", "F1", "F2", "FCz", "FC1", "FC2"]
CONDITIONS = {
    "reward_negative": "S 60",
    "reward_positive": "S 61",
    "punishment_negative": "S 80",
    "punishment_positive": "S 81",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_protocol_lock() -> None:
    lock = json.loads(LOCK_PATH.read_text())
    if lock["status"] != "locked_before_empirical_analysis":
        raise RuntimeError("Protocol is not locked")
    for relative, expected in lock["sha256"].items():
        observed = sha256(ROOT / relative)
        if observed != expected:
            raise RuntimeError(f"Frozen file changed after lock: {relative}")
    if CONFIG["protocol_version"] != lock["protocol_version"]:
        raise RuntimeError("Protocol/config version mismatch")


def verify_implementation_contract() -> None:
    expected = {
        "participants": ["sub-s6", "sub-s8", "sub-s10"],
        "stable": [-30, -11],
        "early": [0, 9],
        "baseline": [-1.3, 0.0],
        "summary": [0.05, 0.3],
        "band": [4.0, 8.0],
        "resamples": 1000,
        "minimum": 5,
    }
    observed = {
        "participants": CONFIG["technical_confirmation_participants"],
        "stable": CONFIG["behavioral_periods_relative_to_reversal"]["stable_pseudo_event_trials"],
        "early": CONFIG["behavioral_periods_relative_to_reversal"]["early_updating_trials"],
        "baseline": CONFIG["phase_prediction"]["baseline_seconds"],
        "summary": CONFIG["phase_prediction"]["primary_summary_seconds"],
        "band": CONFIG["phase_prediction"]["band_hz"],
        "resamples": CONFIG["aggregation"]["balanced_resamples"],
        "minimum": CONFIG["trial_eligibility"]["minimum_clean_negative_feedback_trials_per_period"],
    }
    if observed != expected:
        raise RuntimeError(f"Implementation contract mismatch: {observed}")


def participant_mat_indices() -> dict[str, int]:
    path = ROOT / "results" / "reversal_eeg_pilot" / "behavioral_mat_mapping.csv"
    with path.open(newline="") as handle:
        return {row["participant_id"]: int(row["mat_index"]) - 1 for row in csv.DictReader(handle)}


def task_order(raw: mne.io.BaseRaw) -> list[str]:
    starts = []
    for onset, description in zip(raw.annotations.onset, raw.annotations.description):
        if description == "S100":
            starts.append((onset, "reward"))
        elif description == "S200":
            starts.append((onset, "punishment"))
    return [task for _, task in sorted(starts)]


def trial_events(raw: mne.io.BaseRaw) -> tuple[np.ndarray, dict[str, int], list[dict[str, object]]]:
    event_id = {name: index + 1 for index, name in enumerate(CONDITIONS)}
    marker_to_condition = {marker: name for name, marker in CONDITIONS.items()}
    counters = {"reward": 0, "punishment": 0}
    rows = []
    for onset, description in zip(raw.annotations.onset, raw.annotations.description):
        if description not in marker_to_condition:
            continue
        condition = marker_to_condition[description]
        task = condition.split("_")[0]
        counters[task] += 1
        rows.append({
            "sample": int(round(onset * raw.info["sfreq"])),
            "condition": condition,
            "task": task,
            "feedback": condition.split("_")[1],
            "task_trial": counters[task],
        })
    events = np.asarray([[row["sample"], 0, event_id[row["condition"]]] for row in rows], dtype=int)
    return events, event_id, rows


def annotate_frozen_periods(rows: list[dict[str, object]], order: list[str]) -> list[dict[str, object]]:
    output = [dict(row) for row in rows]
    by_key = {(row["task"], row["task_trial"]): row for row in output}
    stable_offsets = CONFIG["behavioral_periods_relative_to_reversal"]["stable_pseudo_event_trials"]
    early_offsets = CONFIG["behavioral_periods_relative_to_reversal"]["early_updating_trials"]
    for task in ("reward", "punishment"):
        reversals = [82, 150, 225] if order[0] == task else [86, 160, 223]
        for episode, reversal in enumerate(reversals, start=1):
            for offset in range(stable_offsets[0], stable_offsets[1] + 1):
                by_key[(task, reversal + offset)].update({"period": "stable", "reversal_episode": episode})
            for offset in range(early_offsets[0], early_offsets[1] + 1):
                by_key[(task, reversal + offset)].update({"period": "early", "reversal_episode": episode})
    return output


def theta_power_db(epochs: mne.Epochs, batch_size: int = 32) -> np.ndarray:
    frequencies = np.arange(4.0, 9.0)
    decimation = 4
    times = epochs.times[::decimation]
    baseline = (times >= -0.3) & (times <= -0.2)
    target = (times >= 0.25) & (times <= 0.5)
    values = []
    for start in range(0, len(epochs), batch_size):
        data = epochs[start:start + batch_size].get_data(copy=True)
        power = mne.time_frequency.tfr_array_morlet(
            data, sfreq=epochs.info["sfreq"], freqs=frequencies, n_cycles=7.0,
            output="power", decim=decimation, n_jobs=1, verbose="error",
        )
        baseline_power = power[..., baseline].mean(axis=-1, keepdims=True)
        values.extend((10.0 * np.log10(power / baseline_power))[..., target].mean(axis=(1, 2, 3)).tolist())
    return np.asarray(values)


def fitted_sphere(epochs: mne.Epochs) -> tuple[float, float, float, float]:
    positions = epochs.get_montage().get_positions()["ch_pos"]
    xyz = np.asarray([positions[channel] for channel in epochs.ch_names])
    design = np.column_stack((2.0 * xyz, np.ones(len(xyz))))
    solution = np.linalg.lstsq(design, np.sum(xyz * xyz, axis=1), rcond=None)[0]
    center = solution[:3]
    radius = float(np.sqrt(solution[3] + np.dot(center, center)))
    return (*center.tolist(), radius)


def shrinkage_covariance(data: np.ndarray) -> np.ndarray:
    covariance = np.cov(data)
    channels = covariance.shape[0]
    return 0.9 * covariance + 0.1 * np.trace(covariance) / channels * np.eye(channels)


def riemann_distance(pre: np.ndarray, post: np.ndarray) -> float:
    values = eigvalsh(shrinkage_covariance(post), shrinkage_covariance(pre))
    values = np.maximum(values, 1e-12)
    return float(np.linalg.norm(np.log(values)) / np.sqrt(len(values)))


def phase_prediction_metrics(epochs: mne.Epochs) -> list[dict[str, float]]:
    theta = compute_current_source_density(epochs.copy(), sphere=fitted_sphere(epochs))
    theta.filter(*CONFIG["phase_prediction"]["band_hz"], verbose="error")
    signals = theta.get_data(copy=True)
    phases = np.unwrap(np.angle(hilbert(signals, axis=-1)), axis=-1)
    times = theta.times
    baseline = (times >= -1.3) & (times < 0.0)
    response = (times >= 0.05) & (times <= 0.3)
    pre_covariance = (times >= -0.3) & (times <= -0.05)
    post_covariance = response
    baseline_times = times[baseline]
    centered = baseline_times - baseline_times.mean()
    denominator = float(np.dot(centered, centered))
    channels = signals.shape[1]
    output = []
    for epoch_signals, epoch_phases in zip(signals, phases):
        baseline_phases = epoch_phases[:, baseline]
        slopes = (baseline_phases @ centered) / denominator
        intercepts = baseline_phases.mean(axis=1) - slopes * baseline_times.mean()
        predicted = intercepts[:, None] + slopes[:, None] * times[response]
        residual = epoch_phases[:, response] - predicted
        resultant_squared = np.abs(np.exp(1j * residual).sum(axis=0)) ** 2
        pair_agreement = (resultant_squared - channels) / (channels * (channels - 1))
        curve = 1.0 - pair_agreement
        output.append({
            "phase_prediction_reconfiguration": float(curve.mean()),
            "phase_prediction_reconfiguration_peak": float(curve.max()),
            "riemannian_covariance_distance": riemann_distance(
                epoch_signals[:, pre_covariance], epoch_signals[:, post_covariance]
            ),
        })
    return output


def preprocess_participant(participant: str, mat_index: int, bad: dict[str, np.ndarray]) -> tuple[dict[str, object], list[dict[str, object]]]:
    prep = CONFIG["preprocessing"]
    set_file = DATA / participant / f"{participant}_task-task_eeg.set"
    raw = mne.io.read_raw_eeglab(set_file, preload=True, verbose="error")
    original_sfreq = float(raw.info["sfreq"])
    order = task_order(raw)
    raw.resample(prep["resample_hz"], npad="auto", verbose="error")
    raw.set_eeg_reference(prep["reference"], projection=False, verbose="error")
    raw.notch_filter(prep["notch_hz"], verbose="error")
    ica_raw = raw.copy().filter(*prep["ica_fit_bandpass_hz"], verbose="error")
    ica = ICA(n_components=prep["ica_variance"], method="infomax",
              fit_params={"extended": True}, random_state=CONFIG["random_seed"])
    ica.fit(ica_raw, decim=prep["ica_decimation"], reject_by_annotation=True, verbose="error")
    candidates = set()
    for proxy in prep["blink_proxy_channels"]:
        indices, _ = ica.find_bads_eog(ica_raw, ch_name=proxy,
                                       threshold=prep["blink_threshold"], verbose="error")
        candidates.update(indices)
    ica.exclude = sorted(candidates)[:prep["maximum_blink_components"]]
    ica.apply(raw, verbose="error")
    del ica_raw
    raw.filter(*prep["analysis_bandpass_hz"], verbose="error")

    events, event_id, event_rows = trial_events(raw)
    rows = annotate_frozen_periods(event_rows, order)
    bad_by_task = {
        "reward": set(np.asarray(bad["bad_trials_REW"][mat_index], dtype=int).tolist()),
        "punishment": set(np.asarray(bad["bad_trials_PUN"][mat_index], dtype=int).tolist()),
    }
    keep = np.asarray([row["task_trial"] not in bad_by_task[row["task"]] for row in rows], dtype=bool)
    clean_events = events[keep]
    clean_rows = [row for row, include in zip(rows, keep) if include]

    control_epochs = mne.Epochs(raw, clean_events, event_id=event_id, tmin=-1.5, tmax=3.0,
                                baseline=(-1.5, -1.4), picks=ROI, preload=True,
                                reject_by_annotation=True, verbose="error")
    control_rows = [clean_rows[index] for index in control_epochs.selection]
    control_values = theta_power_db(control_epochs)
    for row, value in zip(control_rows, control_values):
        row["fm_theta_db"] = float(value)
    condition_means = {
        condition: float(np.mean([row["fm_theta_db"] for row in control_rows
                                  if row["condition"] == condition]))
        for condition in CONDITIONS
    }
    del control_epochs

    candidate_rows = [row for row in rows if row["task"] == "reward" and row["feedback"] == "negative"
                      and row.get("period") in {"stable", "early"}]
    clean_candidate_indices = [index for index, row in enumerate(clean_rows)
                               if row["task"] == "reward" and row["feedback"] == "negative"
                               and row.get("period") in {"stable", "early"}]
    network_events = clean_events[clean_candidate_indices]
    network_rows = [clean_rows[index] for index in clean_candidate_indices]
    scalp_channels = [channel for channel in raw.ch_names if channel not in {"EOG1", "EOG2"}]
    positions = raw.get_montage().get_positions()["ch_pos"]
    missing_positions = [channel for channel in scalp_channels if channel not in positions]
    if missing_positions:
        raise RuntimeError(f"Missing positions for {participant}: {missing_positions}")
    network_epochs = mne.Epochs(raw, network_events,
                                event_id={"reward_negative": event_id["reward_negative"]},
                                tmin=-1.5, tmax=3.0, baseline=None, picks=scalp_channels,
                                preload=True, reject_by_annotation=True, verbose="error")
    retained_rows = [network_rows[index] for index in network_epochs.selection]
    for row, metrics in zip(retained_rows, phase_prediction_metrics(network_epochs)):
        row.update(metrics)

    pre_counts = {period: sum(row["period"] == period for row in candidate_rows)
                  for period in ("stable", "early")}
    retained_counts = {period: sum(row["period"] == period for row in retained_rows)
                       for period in ("stable", "early")}
    retention_rates = {period: retained_counts[period] / pre_counts[period] if pre_counts[period] else 0.0
                       for period in ("stable", "early")}
    summary = {
        "participant": participant,
        "original_sampling_frequency": original_sfreq,
        "task_order": order,
        "ica_components": int(ica.n_components_),
        "blink_components_removed": [int(value) for value in ica.exclude],
        "manual_bad_trials": {task: len(values) for task, values in bad_by_task.items()},
        "candidate_negative_feedback_trials_before_exclusion": pre_counts,
        "retained_negative_feedback_trials": retained_counts,
        "retention_rates": retention_rates,
        "stable_early_retention_imbalance": abs(retention_rates["stable"] - retention_rates["early"]),
        "reward_theta_negative_minus_positive_db": condition_means["reward_negative"] - condition_means["reward_positive"],
        "reward_theta_direction_passed": condition_means["reward_negative"] > condition_means["reward_positive"],
        "theta_control_means_db": condition_means,
        "all_scalp_positions_valid": not missing_positions,
    }
    del raw, network_epochs
    gc.collect()
    return summary, retained_rows


def balanced_contrast(rows: list[dict[str, object]], participant_index: int, metric: str) -> dict[str, object] | None:
    cells = {period: np.asarray([row[metric] for row in rows if row["period"] == period], dtype=float)
             for period in ("stable", "early")}
    minimum = CONFIG["trial_eligibility"]["minimum_clean_negative_feedback_trials_per_period"]
    if min(len(cells["stable"]), len(cells["early"])) < minimum:
        return None
    n = min(len(cells["stable"]), len(cells["early"]))
    rng = np.random.default_rng(CONFIG["random_seed"] + participant_index)
    differences = []
    stable_means, early_means = [], []
    for _ in range(CONFIG["aggregation"]["balanced_resamples"]):
        stable = rng.choice(cells["stable"], n, replace=False) if len(cells["stable"]) > n else cells["stable"]
        early = rng.choice(cells["early"], n, replace=False) if len(cells["early"]) > n else cells["early"]
        stable_means.append(float(stable.mean()))
        early_means.append(float(early.mean()))
        differences.append(float(early.mean() - stable.mean()))
    return {
        "stable_trials": len(cells["stable"]), "early_trials": len(cells["early"]),
        "balanced_n": n, "stable": float(np.mean(stable_means)),
        "early": float(np.mean(early_means)), "early_minus_stable": float(np.mean(differences)),
        "resample_difference_sd": float(np.std(differences, ddof=1)),
    }


def main() -> None:
    verify_protocol_lock()
    verify_implementation_contract()
    OUT.mkdir(parents=True, exist_ok=True)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    integrity = json.loads((OUT / "download_integrity.json").read_text())
    if not integrity["passed"] or integrity["participants"] != CONFIG["technical_confirmation_participants"]:
        raise RuntimeError("Frozen-participant download integrity gate did not pass")
    mapping = participant_mat_indices()
    bad = loadmat(META / "RevEx1_BadEEGTrials.mat", squeeze_me=True, struct_as_record=False)
    summaries, trial_rows = [], []
    for participant in CONFIG["technical_confirmation_participants"]:
        summary, rows = preprocess_participant(participant, mapping[participant], bad)
        summaries.append(summary)
        for row in rows:
            trial_rows.append({"participant": participant, **row})
        (OUT / f"{participant}_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2), flush=True)

    trial_fields = ["participant", "task_trial", "period", "reversal_episode", "feedback",
                    "phase_prediction_reconfiguration", "phase_prediction_reconfiguration_peak",
                    "riemannian_covariance_distance"]
    with (OUT / "trial_metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=trial_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(trial_rows)

    primary, secondary = [], []
    for index, participant in enumerate(CONFIG["technical_confirmation_participants"]):
        rows = [row for row in trial_rows if row["participant"] == participant]
        for metric, destination in (("phase_prediction_reconfiguration", primary),
                                    ("riemannian_covariance_distance", secondary)):
            result = balanced_contrast(rows, index, metric)
            if result is not None:
                destination.append({"participant": participant, **result})

    positive_primary = sum(row["early_minus_stable"] > 0 for row in primary)
    positive_controls = sum(summary["reward_theta_direction_passed"] for summary in summaries)
    artifact_passes = sum(summary["stable_early_retention_imbalance"] <= 0.20 for summary in summaries)
    gate = {
        "protocol_version": CONFIG["protocol_version"],
        "participants": CONFIG["technical_confirmation_participants"],
        "integrity_passed": integrity["passed"],
        "participant_summaries": summaries,
        "primary_phase_prediction_contrasts": primary,
        "secondary_riemannian_contrasts": secondary,
        "participants_with_sufficient_primary_cells": len(primary),
        "positive_primary_count": positive_primary,
        "reward_theta_positive_control_count": positive_controls,
        "artifact_balance_pass_count": artifact_passes,
        "primary_directional_gate_passed": (
            len(primary) >= 2 and positive_primary >= 2 and positive_controls >= 2
            and artifact_passes == len(summaries)
        ),
        "interpretation_rule": "Small-sample technical directional confirmation; not population-level significance.",
    }
    (OUT / "gate_summary.json").write_text(json.dumps(gate, indent=2) + "\n")

    labels = [row["participant"] for row in primary]
    x = np.arange(len(labels)); width = 0.36
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].bar(x - width / 2, [row["stable"] for row in primary], width, label="Stable")
    axes[0].bar(x + width / 2, [row["early"] for row in primary], width, label="Early")
    axes[0].set(xticks=x, xticklabels=labels, ylabel="Mean excess topology error",
                title="Primary phase-prediction endpoint")
    axes[0].legend()
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].bar(labels, [row["early_minus_stable"] for row in primary])
    axes[1].set(ylabel="Early minus stable", title="Frozen participant contrasts")
    fig.suptitle("EEG phase-prediction technical confirmation v1.0.0")
    fig.tight_layout(); fig.savefig(FIGURE, dpi=180); plt.close(fig)
    print(json.dumps(gate, indent=2))


if __name__ == "__main__":
    main()
