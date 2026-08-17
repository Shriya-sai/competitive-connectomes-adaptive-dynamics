"""Preprocess ds004295 participant 1 and run the published FM-theta control.

The original manual ICA component decisions are not included in the BIDS raw
release. This pilot uses a declared automated approximation and the authors'
released manual bad-trial indices. It must not be described as an exact
reproduction of the BrainVision Analyzer pipeline.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import mne
import numpy as np
from mne.preprocessing import ICA
from scipy.io import loadmat


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "public_reversal_eeg_pilot"
SET_FILE = DATA / "sub-s1" / "sub-s1_task-task_eeg.set"
BAD_FILE = DATA / "metadata" / "RevEx1_BadEEGTrials.mat"
RESULT_DIR = ROOT / "results" / "reversal_eeg_preprocessing_pilot"
FIGURE = ROOT / "figures" / "reversal_eeg_preprocessing_pilot.png"

ROI = ["Fz", "F1", "F2", "FCz", "FC1", "FC2"]
CONDITIONS = {
    "reward_negative": "S 60",
    "reward_positive": "S 61",
    "punishment_negative": "S 80",
    "punishment_positive": "S 81",
}


def trial_events(raw: mne.io.BaseRaw) -> tuple[np.ndarray, dict[str, int], list[dict[str, object]]]:
    event_id = {name: index + 1 for index, name in enumerate(CONDITIONS)}
    rows = []
    counters = {"reward": 0, "punishment": 0}
    for onset, description in zip(raw.annotations.onset, raw.annotations.description):
        matches = [name for name, marker in CONDITIONS.items() if description == marker]
        if not matches:
            continue
        condition = matches[0]
        task = condition.split("_")[0]
        counters[task] += 1
        rows.append(
            {
                "sample": int(round(onset * raw.info["sfreq"])),
                "condition": condition,
                "task": task,
                "task_trial": counters[task],
            }
        )
    events = np.asarray([[row["sample"], 0, event_id[row["condition"]]] for row in rows], dtype=int)
    return events, event_id, rows


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
        power_db = 10.0 * np.log10(power / baseline_power)
        values.extend(power_db[..., target].mean(axis=(1, 2, 3)).tolist())
    return np.asarray(values)


def main() -> None:
    if not SET_FILE.exists():
        raise FileNotFoundError("Run scripts/download_openneuro_eeg_pilot.py first")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)

    raw = mne.io.read_raw_eeglab(SET_FILE, preload=True, verbose="error")
    original = {
        "channels": len(raw.ch_names),
        "sampling_frequency": raw.info["sfreq"],
        "duration_seconds": raw.times[-1],
        "annotations": len(raw.annotations),
    }
    raw.resample(512, npad="auto", verbose="error")
    raw.set_eeg_reference("average", projection=False, verbose="error")
    raw.notch_filter(50.0, verbose="error")

    # Fit ICA on a 1-Hz high-passed copy, matching the authors' rationale.
    ica_raw = raw.copy().filter(1.0, 100.0, verbose="error")
    ica = ICA(n_components=0.99, method="infomax", fit_params={"extended": True}, random_state=42)
    ica.fit(ica_raw, decim=4, reject_by_annotation=True, verbose="error")
    blink_candidates = set()
    for proxy in ("Fp1", "Fp2"):
        indices, _ = ica.find_bads_eog(ica_raw, ch_name=proxy, threshold=3.0, verbose="error")
        blink_candidates.update(indices)
    # Prevent an automated proxy from deleting an unconstrained number of sources.
    ica.exclude = sorted(blink_candidates)[:2]
    ica.apply(raw, verbose="error")
    raw.filter(0.1, 100.0, verbose="error")

    events, event_id, event_rows = trial_events(raw)
    bad = loadmat(BAD_FILE, squeeze_me=True, struct_as_record=False)
    bad_by_task = {
        "reward": set(np.asarray(bad["bad_trials_REW"][0], dtype=int).tolist()),
        "punishment": set(np.asarray(bad["bad_trials_PUN"][0], dtype=int).tolist()),
    }
    keep = np.asarray(
        [row["task_trial"] not in bad_by_task[row["task"]] for row in event_rows], dtype=bool
    )
    clean_events = events[keep]
    clean_rows = [row for row, include in zip(event_rows, keep) if include]

    epochs = mne.Epochs(
        raw,
        clean_events,
        event_id=event_id,
        tmin=-1.5,
        tmax=3.0,
        baseline=(-1.5, -1.4),
        picks=ROI,
        preload=True,
        reject_by_annotation=True,
        detrend=None,
        verbose="error",
    )
    retained_selection = epochs.selection
    retained_rows = [clean_rows[index] for index in retained_selection]
    theta = theta_power_db(epochs)

    trial_output = []
    for row, value in zip(retained_rows, theta):
        trial_output.append({**row, "fm_theta_db": float(value)})
    with (RESULT_DIR / "trialwise_fm_theta.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trial_output[0]))
        writer.writeheader()
        writer.writerows(trial_output)

    condition_values = {
        condition: np.asarray([row["fm_theta_db"] for row in trial_output if row["condition"] == condition])
        for condition in CONDITIONS
    }
    means = {condition: float(values.mean()) for condition, values in condition_values.items()}
    counts = {condition: int(len(values)) for condition, values in condition_values.items()}
    contrasts = {
        "reward_negative_minus_positive_db": means["reward_negative"] - means["reward_positive"],
        "punishment_negative_minus_positive_db": means["punishment_negative"] - means["punishment_positive"],
    }
    summary = {
        "participant": "sub-s1",
        "original": original,
        "processed_sampling_frequency": raw.info["sfreq"],
        "roi": ROI,
        "ica_components": int(ica.n_components_),
        "automated_blink_components_removed": [int(index) for index in ica.exclude],
        "manual_bad_trials_reward": len(bad_by_task["reward"]),
        "manual_bad_trials_punishment": len(bad_by_task["punishment"]),
        "retained_epoch_counts": counts,
        "condition_mean_fm_theta_db": means,
        "contrasts": contrasts,
        "positive_control_direction_passed": contrasts["reward_negative_minus_positive_db"] > 0,
        "methodological_deviation": (
            "Original manual blink-ICA component selections were unavailable. This pilot uses "
            "a capped automated Fp1/Fp2 proxy and the authors' released bad-trial indices."
        ),
    }
    (RESULT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    labels = ["Reward +", "Reward −", "Punishment +", "Punishment −"]
    keys = ["reward_positive", "reward_negative", "punishment_positive", "punishment_negative"]
    plot_means = [means[key] for key in keys]
    sems = [condition_values[key].std(ddof=1) / np.sqrt(len(condition_values[key])) for key in keys]
    colors = ["#4C78A8", "#E45756", "#72B7B2", "#F58518"]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, plot_means, yerr=sems, color=colors, capsize=4)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Frontal-midline theta power (dB)")
    ax.set_title("Participant 1 feedback-locked positive-control pilot")
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=180)
    plt.close(fig)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
