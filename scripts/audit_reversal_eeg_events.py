"""Audit the public ds004295 reversal-learning EEG event release.

This script deliberately uses only the small BIDS event/metadata files and the
released behavioural MAT file. It does not download or analyse EEG signals.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.io import loadmat


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "public_reversal_eeg_pilot"
EVENT_DIR = PILOT / "events"
META_DIR = PILOT / "metadata"
RESULT_DIR = ROOT / "results" / "reversal_eeg_pilot"

MARKERS = {
    "S51": ("reward", "choice", 1),
    "S52": ("reward", "choice", 2),
    "S53": ("reward", "expectation", 0),
    "S54": ("reward", "expectation", 1),
    "S55": ("reward", "expectation", 2),
    "S56": ("reward", "expectation", 3),
    "S60": ("reward", "feedback", 0),
    "S61": ("reward", "feedback", 1),
    "S71": ("punishment", "choice", 1),
    "S72": ("punishment", "choice", 2),
    "S73": ("punishment", "expectation", 0),
    "S74": ("punishment", "expectation", 1),
    "S75": ("punishment", "expectation", 2),
    "S76": ("punishment", "expectation", 3),
    "S80": ("punishment", "feedback", 0),
    "S81": ("punishment", "feedback", 1),
}

START_MARKERS = {"S100": "reward", "S200": "punishment"}
EXPECTED_EXCLUSIONS = {"sub-s5", "sub-s7", "sub-s9"}


def normalized(value: str) -> str:
    return value.replace(" ", "")


def read_events(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def task_order(rows: list[dict[str, str]]) -> list[str]:
    starts = [
        (float(row["onset"]), START_MARKERS[normalized(row["value"])])
        for row in rows
        if normalized(row["value"]) in START_MARKERS
    ]
    return [task for _, task in sorted(starts)]


def extract_trials(rows: list[dict[str, str]], task: str) -> list[dict[str, float | int | str]]:
    relevant = []
    for row in rows:
        marker = normalized(row["value"])
        if marker in MARKERS and MARKERS[marker][0] == task:
            relevant.append((float(row["onset"]), MARKERS[marker]))

    # Feedback is the most reliable one-per-trial anchor. Some recordings contain
    # duplicate choice markers, so anchoring trials on choices would create false
    # extra trials. Retain the latest choice and expectation before each feedback.
    trials: list[dict[str, float | int | str]] = []
    current: dict[str, float | int | str] = {"task": task}
    for onset, (_, kind, value) in relevant:
        if kind == "choice":
            current["choice"] = value
            current["choice_onset"] = onset
        elif kind == "expectation":
            current[kind] = value
            current[f"{kind}_onset"] = onset
        elif kind == "feedback":
            current[kind] = value
            current[f"{kind}_onset"] = onset
            trials.append(current)
            current = {"task": task}
    return trials


def feedback_sequence(rows: list[dict[str, str]], task: str) -> np.ndarray:
    trials = extract_trials(rows, task)
    if any("feedback" not in trial for trial in trials):
        return np.asarray([], dtype=int)
    return np.asarray([trial["feedback"] for trial in trials], dtype=int)


def reversal_metrics(choices: np.ndarray, reversals: list[int]) -> list[dict[str, float | int]]:
    """Measure switching relative to the empirically dominant pre-reversal choice.

    Reversal numbers are one-based first trials under the new contingency. Because
    the public event markers encode left/right rather than stimulus identity, this
    is a transparent behavioural proxy and not a ground-truth accuracy score.
    """
    output = []
    boundaries = reversals + [len(choices) + 1]
    for index, reversal in enumerate(reversals):
        start = reversal - 1
        next_start = boundaries[index + 1] - 1
        pre = choices[max(0, start - 20) : start]
        old_choice = Counter(pre.tolist()).most_common(1)[0][0]
        new_choice = 1 if old_choice == 2 else 2
        output.append(
            {
                "reversal": reversal,
                "pre_last10_old_choice_rate": float(np.mean(choices[start - 10 : start] == old_choice)),
                "post_first2_new_choice_rate": float(np.mean(choices[start : start + 2] == new_choice)),
                "post_late10_new_choice_rate": float(
                    np.mean(choices[max(start, next_start - 10) : next_start] == new_choice)
                ),
            }
        )
    return output


def main() -> None:
    participant_rows = list(
        csv.DictReader((META_DIR / "participants.tsv").open(newline=""), delimiter="\t")
    )
    participant_info = {row["participant_id"]: row for row in participant_rows}

    event_paths = sorted(EVENT_DIR.glob("sub-*_task-task_events.tsv"))
    event_data = {
        path.name.split("_task-")[0]: read_events(path)
        for path in event_paths
    }

    mat = loadmat(META_DIR / "RevEx1_behavioralData.mat", squeeze_me=True, struct_as_record=False)
    mappings = []
    for index, (reward, punishment) in enumerate(zip(mat["REW_feedback"], mat["PUN_feedback"])):
        hits = [
            participant
            for participant, rows in event_data.items()
            if np.array_equal(np.asarray(reward, dtype=int), feedback_sequence(rows, "reward"))
            and np.array_equal(np.asarray(punishment, dtype=int), feedback_sequence(rows, "punishment"))
        ]
        mappings.append({"mat_index": index + 1, "participant_id": hits[0] if len(hits) == 1 else "AMBIGUOUS"})
    mat_index_by_participant = {
        row["participant_id"]: row["mat_index"] - 1
        for row in mappings
        if row["participant_id"] != "AMBIGUOUS"
    }

    summaries = []
    all_reversal_metrics = []
    for participant, rows in sorted(event_data.items(), key=lambda item: int(item[0].split("s")[-1])):
        order = task_order(rows)
        excluded = participant_info[participant]["Excluded"] != "n/a"
        for task in ("reward", "punishment"):
            trials = extract_trials(rows, task)
            first_task = order[0] == task
            reversals = [82, 150, 225] if first_task else [86, 160, 223]
            complete = sum(
                "choice" in trial and "expectation" in trial and "feedback" in trial
                for trial in trials
            )
            summaries.append(
                {
                    "participant_id": participant,
                    "task": task,
                    "task_order": 1 if first_task else 2,
                    "n_trials": len(trials),
                    "complete_trials": complete,
                    "reversals": ";".join(map(str, reversals)),
                    "excluded": excluded,
                }
            )
            if not excluded and len(trials) == 280 and complete == 280:
                # Event choice markers are spatial button presses; the released MAT
                # arrays recode the selected stimulus identity and are therefore the
                # correct source for reversal-aligned behavioural switching.
                mat_index = mat_index_by_participant[participant]
                mat_key = "REW_action" if task == "reward" else "PUN_action"
                choices = np.asarray(mat[mat_key][mat_index], dtype=int)
                for metric in reversal_metrics(choices, reversals):
                    all_reversal_metrics.append(
                        {"participant_id": participant, "task": task, **metric}
                    )

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with (RESULT_DIR / "event_audit.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    with (RESULT_DIR / "behavioral_mat_mapping.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["mat_index", "participant_id"])
        writer.writeheader()
        writer.writerows(mappings)
    with (RESULT_DIR / "reversal_proxy_metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_reversal_metrics[0]))
        writer.writeheader()
        writer.writerows(all_reversal_metrics)

    def mean(field: str) -> float:
        return float(np.mean([row[field] for row in all_reversal_metrics]))

    mapping_ids = {row["participant_id"] for row in mappings}
    report = {
        "bids_recordings": len(event_data),
        "analyzed_participants": len(mappings),
        "excluded_participants": sorted(set(event_data) - mapping_ids),
        "mapping_unique": all(row["participant_id"] != "AMBIGUOUS" for row in mappings),
        "all_nonexcluded_tasks_complete": all(
            row["n_trials"] == 280 and row["complete_trials"] == 280
            for row in summaries
            if not row["excluded"]
        ),
        "reversal_events_analyzed": len(all_reversal_metrics),
        "proxy_pre_last10_old_choice_rate": mean("pre_last10_old_choice_rate"),
        "proxy_post_first2_new_choice_rate": mean("post_first2_new_choice_rate"),
        "proxy_post_late10_new_choice_rate": mean("post_late10_new_choice_rate"),
        "gate_passed": (
            len(event_data) == 26
            and len(mappings) == 23
            and mapping_ids == set(event_data) - EXPECTED_EXCLUSIONS
            and all(row["participant_id"] != "AMBIGUOUS" for row in mappings)
            and all(
                row["n_trials"] == 280 and row["complete_trials"] == 280
                for row in summaries
                if not row["excluded"]
            )
        ),
        "important_limit": (
            "Switching values use the dominant pre-reversal stimulus choice as a data-derived "
            "proxy because the released arrays do not explicitly label ground-truth accuracy."
        ),
    }
    (RESULT_DIR / "audit_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
