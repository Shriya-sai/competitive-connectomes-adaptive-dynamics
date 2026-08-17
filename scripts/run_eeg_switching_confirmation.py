"""Run the frozen ds004295 three-participant switching confirmation gate."""

from __future__ import annotations

import csv
import gc
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import mne
import numpy as np
from mne.preprocessing import ICA, compute_current_source_density
from scipy.io import loadmat


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "eeg_switching_analysis.json"
CONFIG = json.loads(CONFIG_PATH.read_text())
DATA = ROOT / "data" / "public_reversal_eeg_pilot"
META = DATA / "metadata"
RESULT_DIR = ROOT / "results" / "reversal_eeg_confirmation"
FIGURE = ROOT / "figures" / "reversal_eeg_confirmation.png"
ROI = ["Fz", "F1", "F2", "FCz", "FC1", "FC2"]
CONDITIONS = {
    "reward_negative": "S 60",
    "reward_positive": "S 61",
    "punishment_negative": "S 80",
    "punishment_positive": "S 81",
}


def participant_mat_indices() -> dict[str, int]:
    path = ROOT / "results" / "reversal_eeg_pilot" / "behavioral_mat_mapping.csv"
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["participant_id"]: int(row["mat_index"]) - 1 for row in rows}


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
    rows = []
    counters = {"reward": 0, "punishment": 0}
    marker_to_condition = {marker: name for name, marker in CONDITIONS.items()}
    for onset, description in zip(raw.annotations.onset, raw.annotations.description):
        if description not in marker_to_condition:
            continue
        condition = marker_to_condition[description]
        task = condition.split("_")[0]
        counters[task] += 1
        rows.append(
            {
                "sample": int(round(onset * raw.info["sfreq"])),
                "condition": condition,
                "task": task,
                "feedback": condition.split("_")[1],
                "task_trial": counters[task],
            }
        )
    events = np.asarray([[row["sample"], 0, event_id[row["condition"]]] for row in rows], dtype=int)
    return events, event_id, rows


def adoption_trial(choices: np.ndarray, reversal: int, next_reversal: int) -> int | None:
    start = reversal - 1
    old = Counter(choices[max(0, start - 20) : start].tolist()).most_common(1)[0][0]
    new = 1 if old == 2 else 2
    last_start = min(next_reversal - 1, len(choices)) - 6
    for zero_based in range(start, last_start + 1):
        if np.sum(choices[zero_based : zero_based + 6] == new) >= 5:
            return zero_based + 1
    return None


def annotate_periods(
    rows: list[dict[str, object]], task_orders: list[str], behavior: dict[str, np.ndarray]
) -> list[dict[str, object]]:
    output = [dict(row) for row in rows]
    by_key = {(row["task"], row["task_trial"]): row for row in output}
    for task in ("reward", "punishment"):
        first = task_orders[0] == task
        reversals = [82, 150, 225] if first else [86, 160, 223]
        boundaries = reversals + [281]
        choices = behavior[task]
        for episode, reversal in enumerate(reversals, start=1):
            next_reversal = boundaries[episode]
            adoption = adoption_trial(choices, reversal, next_reversal)
            latency = adoption - reversal if adoption is not None else None
            for trial in range(reversal - 10, reversal):
                by_key[(task, trial)].update(
                    {"period": "stable", "reversal_episode": episode, "adoption_latency": latency}
                )
            for trial in range(reversal, min(reversal + 10, next_reversal)):
                by_key[(task, trial)].update(
                    {"period": "early", "reversal_episode": episode, "adoption_latency": latency}
                )
            if adoption is not None:
                for trial in range(adoption, min(adoption + 10, next_reversal)):
                    # Preserve early as the primary label if windows overlap.
                    target = by_key[(task, trial)]
                    target.setdefault("period", "post_adoption")
                    target.update({"reversal_episode": episode, "adoption_latency": latency})
    return output


def theta_power_db(epochs: mne.Epochs, batch_size: int = 32) -> np.ndarray:
    frequencies = np.arange(4.0, 9.0)
    values = []
    decimation = 4
    times = epochs.times[::decimation]
    baseline = (times >= -0.3) & (times <= -0.2)
    target = (times >= 0.25) & (times <= 0.5)
    for start in range(0, len(epochs), batch_size):
        data = epochs[start : start + batch_size].get_data(copy=True)
        power = mne.time_frequency.tfr_array_morlet(
            data,
            sfreq=epochs.info["sfreq"],
            freqs=frequencies,
            n_cycles=7.0,
            output="power",
            decim=decimation,
            n_jobs=1,
            verbose="error",
        )
        baseline_power = power[..., baseline].mean(axis=-1, keepdims=True)
        values.extend(
            (10.0 * np.log10(power / baseline_power))[..., target]
            .mean(axis=(1, 2, 3))
            .tolist()
        )
    return np.asarray(values)


def phase_metrics(epochs: mne.Epochs) -> list[dict[str, float]]:
    positions = epochs.get_montage().get_positions()["ch_pos"]
    xyz = np.asarray([positions[channel] for channel in epochs.ch_names])
    design = np.column_stack((2.0 * xyz, np.ones(len(xyz))))
    solution = np.linalg.lstsq(design, np.sum(xyz * xyz, axis=1), rcond=None)[0]
    center = solution[:3]
    radius = float(np.sqrt(solution[3] + np.dot(center, center)))
    sphere = (*center.tolist(), radius)
    csd = compute_current_source_density(epochs.copy(), sphere=sphere)
    csd.filter(4.0, 8.0, verbose="error")
    csd.apply_hilbert(envelope=False, verbose="error")
    analytic = csd.get_data(copy=False)
    times = csd.times
    baseline = (times >= -0.3) & (times <= -0.2)
    response = (times >= 0.2) & (times <= 1.5)
    upper = np.triu_indices(analytic.shape[1], k=1)
    output = []
    for epoch in analytic:
        phases = np.angle(epoch)
        order = np.abs(np.mean(np.exp(1j * phases), axis=0))
        baseline_pair = np.exp(
            1j
            * (
                phases[upper[0]][:, baseline]
                - phases[upper[1]][:, baseline]
            )
        ).mean(axis=1)
        baseline_unit = baseline_pair / np.maximum(np.abs(baseline_pair), 1e-12)
        response_pair = np.exp(
            1j
            * (
                phases[upper[0]][:, response]
                - phases[upper[1]][:, response]
            )
        )
        similarity = np.real(response_pair * np.conj(baseline_unit[:, None])).mean()
        output.append(
            {
                "theta_mean_synchrony": float(order[response].mean()),
                "theta_synchrony_variability": float(order[response].std(ddof=1)),
                "theta_phase_reconfiguration": float(1.0 - similarity),
            }
        )
    return output


def preprocess_participant(
    participant: str, mat_index: int, bad: dict[str, np.ndarray], behavioral: dict[str, np.ndarray]
) -> tuple[dict[str, object], list[dict[str, object]]]:
    set_file = DATA / participant / f"{participant}_task-task_eeg.set"
    raw = mne.io.read_raw_eeglab(set_file, preload=True, verbose="error")
    original_sfreq = float(raw.info["sfreq"])
    original_duration = float(raw.times[-1])
    order = task_order(raw)
    raw.resample(CONFIG["preprocessing"]["resample_hz"], npad="auto", verbose="error")
    raw.set_eeg_reference("average", projection=False, verbose="error")
    raw.notch_filter(CONFIG["preprocessing"]["notch_hz"], verbose="error")
    ica_raw = raw.copy().filter(*CONFIG["preprocessing"]["ica_fit_bandpass_hz"], verbose="error")
    ica = ICA(
        n_components=CONFIG["preprocessing"]["ica_variance"],
        method="infomax",
        fit_params={"extended": True},
        random_state=CONFIG["random_seed"],
    )
    ica.fit(
        ica_raw,
        decim=CONFIG["preprocessing"]["ica_decimation"],
        reject_by_annotation=True,
        verbose="error",
    )
    candidates = set()
    for proxy in CONFIG["preprocessing"]["blink_proxy_channels"]:
        indices, _ = ica.find_bads_eog(
            ica_raw,
            ch_name=proxy,
            threshold=CONFIG["preprocessing"]["blink_threshold"],
            verbose="error",
        )
        candidates.update(indices)
    ica.exclude = sorted(candidates)[: CONFIG["preprocessing"]["maximum_blink_components"]]
    ica.apply(raw, verbose="error")
    del ica_raw
    raw.filter(*CONFIG["preprocessing"]["analysis_bandpass_hz"], verbose="error")

    events, event_id, raw_rows = trial_events(raw)
    rows = annotate_periods(raw_rows, order, behavioral)
    bad_by_task = {
        "reward": set(np.asarray(bad["bad_trials_REW"][mat_index], dtype=int).tolist()),
        "punishment": set(np.asarray(bad["bad_trials_PUN"][mat_index], dtype=int).tolist()),
    }
    rejection_rates = {}
    for task in ("reward", "punishment"):
        for feedback in ("negative", "positive"):
            cell = [row for row in rows if row["task"] == task and row["feedback"] == feedback]
            rejected = [row for row in cell if row["task_trial"] in bad_by_task[task]]
            rejection_rates[f"{task}_{feedback}"] = len(rejected) / len(cell)
    rejection_imbalances = {
        task: abs(
            rejection_rates[f"{task}_negative"] - rejection_rates[f"{task}_positive"]
        )
        for task in ("reward", "punishment")
    }
    keep = np.asarray(
        [row["task_trial"] not in bad_by_task[row["task"]] for row in rows], dtype=bool
    )
    clean_events = events[keep]
    clean_rows = [row for row, include in zip(rows, keep) if include]

    control_epochs = mne.Epochs(
        raw,
        clean_events,
        event_id=event_id,
        tmin=-1.5,
        tmax=3.0,
        baseline=(-1.5, -1.4),
        picks=ROI,
        preload=True,
        reject_by_annotation=True,
        verbose="error",
    )
    control_rows = [clean_rows[index] for index in control_epochs.selection]
    control_theta = theta_power_db(control_epochs)
    for row, value in zip(control_rows, control_theta):
        row["fm_theta_db"] = float(value)
    del control_epochs

    network_indices = [
        index
        for index, row in enumerate(clean_rows)
        if row.get("period") in {"stable", "early"} and row["feedback"] == "negative"
    ]
    network_events = clean_events[network_indices]
    network_rows = [clean_rows[index] for index in network_indices]
    scalp_channels = [channel for channel in raw.ch_names if channel not in {"EOG1", "EOG2"}]
    positions = raw.get_montage().get_positions()["ch_pos"]
    missing_positions = [channel for channel in scalp_channels if channel not in positions]
    if missing_positions:
        raise RuntimeError(f"Missing positions for {participant}: {missing_positions}")
    network_epochs = mne.Epochs(
        raw,
        network_events,
        event_id={
            condition: code
            for condition, code in event_id.items()
            if condition.endswith("_negative")
        },
        tmin=-1.5,
        tmax=3.0,
        baseline=None,
        picks=scalp_channels,
        preload=True,
        reject_by_annotation=True,
        verbose="error",
    )
    retained_network_rows = [network_rows[index] for index in network_epochs.selection]
    metrics = phase_metrics(network_epochs)
    for row, metric in zip(retained_network_rows, metrics):
        row.update(metric)

    condition_values = {
        condition: np.asarray(
            [row["fm_theta_db"] for row in control_rows if row["condition"] == condition]
        )
        for condition in CONDITIONS
    }
    means = {name: float(values.mean()) for name, values in condition_values.items()}
    episode_rows = []
    for task in ("reward", "punishment"):
        for episode in (1, 2, 3):
            group = [
                row
                for row in retained_network_rows
                if row["task"] == task and row.get("reversal_episode") == episode
            ]
            for period in ("stable", "early"):
                cell = [row for row in group if row.get("period") == period]
                episode_rows.append(
                    {
                        "participant": participant,
                        "task": task,
                        "reversal_episode": episode,
                        "period": period,
                        "negative_feedback_trials": len(cell),
                        "adoption_latency": group[0].get("adoption_latency") if group else None,
                        "theta_phase_reconfiguration": (
                            float(np.mean([row["theta_phase_reconfiguration"] for row in cell]))
                            if cell
                            else None
                        ),
                        "theta_mean_synchrony": (
                            float(np.mean([row["theta_mean_synchrony"] for row in cell]))
                            if cell
                            else None
                        ),
                        "theta_synchrony_variability": (
                            float(np.mean([row["theta_synchrony_variability"] for row in cell]))
                            if cell
                            else None
                        ),
                    }
                )

    summary = {
        "participant": participant,
        "original_sampling_frequency": original_sfreq,
        "duration_seconds": original_duration,
        "task_order": order,
        "ica_components": int(ica.n_components_),
        "blink_components_removed": [int(index) for index in ica.exclude],
        "manual_bad_trials": {task: len(values) for task, values in bad_by_task.items()},
        "rejection_rates_by_outcome": rejection_rates,
        "maximum_outcome_rejection_imbalance": max(rejection_imbalances.values()),
        "theta_control_means_db": means,
        "reward_theta_negative_minus_positive_db": means["reward_negative"]
        - means["reward_positive"],
        "reward_theta_direction_passed": means["reward_negative"] > means["reward_positive"],
        "network_negative_feedback_epochs": len(retained_network_rows),
        "all_scalp_positions_valid": not missing_positions,
    }
    del raw, network_epochs
    gc.collect()
    return summary, episode_rows


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    integrity = json.loads((RESULT_DIR / "download_integrity.json").read_text())
    if not integrity["passed"]:
        raise RuntimeError("Confirmation download integrity gate did not pass")
    mapping = participant_mat_indices()
    bad = loadmat(META / "RevEx1_BadEEGTrials.mat", squeeze_me=True, struct_as_record=False)
    behavior_mat = loadmat(META / "RevEx1_behavioralData.mat", squeeze_me=True, struct_as_record=False)
    summaries = []
    episode_rows = []
    for participant in CONFIG["confirmation_participants"]:
        index = mapping[participant]
        behavior = {
            "reward": np.asarray(behavior_mat["REW_action"][index], dtype=int),
            "punishment": np.asarray(behavior_mat["PUN_action"][index], dtype=int),
        }
        summary, participant_episodes = preprocess_participant(
            participant, index, bad, behavior
        )
        summaries.append(summary)
        episode_rows.extend(participant_episodes)
        (RESULT_DIR / f"{participant}_summary.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
        print(json.dumps(summary, indent=2), flush=True)

    with (RESULT_DIR / "episode_metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(episode_rows[0]))
        writer.writeheader()
        writer.writerows(episode_rows)

    minimum = CONFIG["minimum_clean_trials_per_cell"]
    participant_differences = []
    sufficient_participants = 0
    for participant in CONFIG["confirmation_participants"]:
        reward = [
            row
            for row in episode_rows
            if row["participant"] == participant and row["task"] == "reward"
        ]
        period_estimates = {}
        period_counts = {}
        for period in ("stable", "early"):
            cells = [
                row
                for row in reward
                if row["period"] == period
                and row["theta_phase_reconfiguration"] is not None
            ]
            total = sum(row["negative_feedback_trials"] for row in cells)
            period_counts[period] = total
            period_estimates[period] = (
                sum(
                    row["theta_phase_reconfiguration"] * row["negative_feedback_trials"]
                    for row in cells
                )
                / total
                if total
                else None
            )
        if (
            period_counts["stable"] >= minimum
            and period_counts["early"] >= minimum
        ):
            sufficient_participants += 1
            participant_differences.append(
                {
                    "participant": participant,
                    "stable_negative_feedback_trials": period_counts["stable"],
                    "early_negative_feedback_trials": period_counts["early"],
                    "stable": float(period_estimates["stable"]),
                    "early": float(period_estimates["early"]),
                    "early_minus_stable": float(
                        period_estimates["early"] - period_estimates["stable"]
                    ),
                }
            )

    positive_reconfiguration = sum(row["early_minus_stable"] > 0 for row in participant_differences)
    theta_passes = sum(summary["reward_theta_direction_passed"] for summary in summaries)
    artifact_balance_passes = sum(
        summary["maximum_outcome_rejection_imbalance"] <= 0.20 for summary in summaries
    )
    gate = {
        "participants": CONFIG["confirmation_participants"],
        "integrity_passed": integrity["passed"],
        "participant_summaries": summaries,
        "reward_reconfiguration_differences": participant_differences,
        "participants_with_sufficient_reward_cells": sufficient_participants,
        "positive_reward_reconfiguration_count": positive_reconfiguration,
        "reward_theta_positive_control_count": theta_passes,
        "artifact_balance_pass_count": artifact_balance_passes,
        "confirmation_gate_passed": (
            integrity["passed"]
            and sufficient_participants >= 2
            and positive_reconfiguration >= 2
            and theta_passes >= 2
            and artifact_balance_passes == len(summaries)
        ),
        "interpretation_rule": (
            "This is a preregistered technical/directional gate, not a significance test."
        ),
    }
    (RESULT_DIR / "gate_summary.json").write_text(json.dumps(gate, indent=2) + "\n")

    labels = [row["participant"] for row in participant_differences]
    x = np.arange(len(labels))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, [row["stable"] for row in participant_differences], width, label="Stable")
    ax.bar(x + width / 2, [row["early"] for row in participant_differences], width, label="Early updating")
    ax.set_xticks(x, labels)
    ax.set_ylabel("Theta phase-pattern reconfiguration")
    ax.set_title("Frozen three-participant EEG confirmation gate")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=180)
    plt.close(fig)
    print(json.dumps(gate, indent=2))


if __name__ == "__main__":
    main()
