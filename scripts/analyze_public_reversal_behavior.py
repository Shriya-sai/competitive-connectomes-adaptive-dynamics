"""Reconstruct the public human reversal-learning baseline in Python."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "public_reversal_behavior"
RESULTS = ROOT / "results" / "public_reversal_behavior"
FIGURE = ROOT / "figures" / "public_reversal_behavior.png"
INCLUDED = (2, 3, 4, 5, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
            22, 23, 26, 27, 28, 29, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40)


def load_rows(subject: int) -> list[dict[str, int]]:
    path = DATA / f"Sub{subject:02d}_RL_Go_NoGo_results_all.txt"
    with path.open() as handle:
        next(handle)
        raw = [row[:8] for row in csv.reader(handle, delimiter="\t") if row]
    names = ("trial", "block", "trial_type", "cue_time", "rt", "outcome_time",
             "response_type", "reversal")
    return [dict(zip(names, map(int, row), strict=True)) for row in raw]


def chose_correct_strategy(row: dict[str, int], block_index: int) -> float:
    if row["response_type"] == 5:
        return np.nan
    actual_go = row["rt"] > 0
    cue_one = row["trial_type"] in (1, 2)
    cue_one_go_before_reversal = block_index % 2 == 0
    cue_one_go_now = cue_one_go_before_reversal != bool(row["reversal"])
    correct_go = cue_one_go_now if cue_one else not cue_one_go_now
    return float(actual_go == correct_go)


def aligned_blocks(rows: list[dict[str, int]]) -> np.ndarray:
    if len(rows) != 540:
        raise ValueError(f"Expected 540 trials, found {len(rows)}")
    blocks = [rows[start:start + 45] for start in range(0, 540, 45)]
    aligned = []
    for block_index, block in enumerate(blocks):
        transitions = [i for i, row in enumerate(block) if row["reversal"] == 1]
        if not transitions:
            raise ValueError("Block has no reversal")
        boundary = transitions[0]
        if not 20 <= boundary <= 25:
            raise ValueError(f"Unexpected reversal boundary {boundary}")
        pre = block[boundary - 20:boundary]
        post = block[boundary:boundary + 20]
        if len(pre) != 20 or len(post) != 20:
            raise ValueError("Insufficient reversal-aligned trials")
        aligned.append([chose_correct_strategy(row, block_index) for row in pre + post])
    return np.asarray(aligned, dtype=float)


def logistic(trial: np.ndarray, offset: float, slope: float, lapse: float) -> np.ndarray:
    exponent = np.clip(-slope * (trial - offset), -60, 60)
    return lapse + (1 - 2 * lapse) / (1 + np.exp(exponent))


def fit_switch(post_blocks: np.ndarray) -> tuple[float, float, float]:
    """Fit the first ten post-reversal trials as block-level Bernoulli data."""
    trials = np.tile(np.arange(1, 11, dtype=float), post_blocks.shape[0])
    choices = post_blocks[:, :10].reshape(-1)
    valid = np.isfinite(choices)
    trials, choices = trials[valid], choices[valid]

    def negative_log_likelihood(params: np.ndarray) -> float:
        probability = np.clip(logistic(trials, *params), 1e-8, 1 - 1e-8)
        return float(-np.sum(choices * np.log(probability) +
                             (1 - choices) * np.log(1 - probability)))

    result = minimize(
        negative_log_likelihood,
        x0=np.array([4.0, 1.0, 0.1]),
        method="L-BFGS-B",
        bounds=((-5.0, 15.0), (0.01, 20.0), (0.0, 0.49)),
    )
    if not result.success:
        raise RuntimeError(f"Switch fit failed: {result.message}")
    return tuple(float(value) for value in result.x)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    subject_curves = []
    records = []
    response_counts: Counter[int] = Counter()

    for subject in INCLUDED:
        rows = load_rows(subject)
        response_counts.update(row["response_type"] for row in rows)
        blocks = aligned_blocks(rows)
        curve = np.nanmean(blocks, axis=0)
        offset, slope, lapse = fit_switch(blocks[:, 20:30])
        subject_curves.append(curve)
        records.append({
            "subject": subject,
            "switch_offset": offset,
            "switch_slope": slope,
            "lapse_rate": lapse,
            "pre_reversal_accuracy": float(np.nanmean(curve[10:20])),
            "switch_period_accuracy": float(np.nanmean(curve[20:30])),
            "late_trials": sum(row["response_type"] == 5 for row in rows),
        })

    curves = np.asarray(subject_curves)
    mean_curve = np.nanmean(curves, axis=0)
    sem_curve = np.nanstd(curves, axis=0, ddof=1) / np.sqrt(len(INCLUDED))
    metric_names = ("switch_offset", "switch_slope", "lapse_rate",
                    "pre_reversal_accuracy", "switch_period_accuracy", "late_trials")
    summary = {
        "design": {
            "included_subjects": list(INCLUDED),
            "excluded_deposited_subject": 30,
            "subjects": len(INCLUDED),
            "trials_per_subject": 540,
            "blocks_per_subject": 12,
            "aligned_trials": list(range(-20, 0)) + list(range(1, 21)),
        },
        "metrics": {
            name: {
                "mean": float(np.mean([record[name] for record in records])),
                "sd": float(np.std([record[name] for record in records], ddof=1)),
            }
            for name in metric_names
        },
        "response_type_counts": dict(sorted(response_counts.items())),
        "group_mean_curve": mean_curve.tolist(),
        "group_sem_curve": sem_curve.tolist(),
        "interpretation": (
            "Human empirical target reconstructed independently of the Hopf-model results. "
            "Switch parameters use bounded nonlinear fits to each participant's mean first "
            "ten post-reversal trials and may not exactly match the authors' unpublished fit settings."
        ),
    }

    with (RESULTS / "subject_metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    x = np.r_[np.arange(-20, 0), np.arange(1, 21)]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.plot(x, mean_curve, color="#2E5D7B", linewidth=2.5, label="Human mean")
    ax.fill_between(x, mean_curve - sem_curve, mean_curve + sem_curve,
                    color="#2E5D7B", alpha=0.2, linewidth=0, label="SEM")
    ax.axvline(0, color="#A77A2D", linestyle="--", linewidth=1.8, label="Reversal")
    ax.axhline(0.5, color="#68717A", linestyle=":", linewidth=1.3, label="Chance")
    ax.set(xlabel="Trials relative to reversal", ylabel="Probability of correct strategy",
           ylim=(0, 1.02), title="Public human reversal-learning baseline (n = 32)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncol=4, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=180)
    plt.close(fig)

    print(json.dumps(summary["metrics"], indent=2))
    print(f"Saved results to {RESULTS}")
    print(f"Saved figure to {FIGURE}")


if __name__ == "__main__":
    main()
