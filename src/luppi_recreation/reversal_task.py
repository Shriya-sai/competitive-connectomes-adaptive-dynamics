"""Empirical probabilistic rule-reversal task and neutral RL benchmark."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class ReversalSchedule:
    cue: np.ndarray
    rewarded_action: np.ndarray
    correct_strategy_action: np.ndarray
    reversal: np.ndarray
    block_index: np.ndarray
    trial_in_block: np.ndarray

    @property
    def n_trials(self) -> int:
        return int(self.cue.size)


def load_released_schedule(path: str | Path) -> ReversalSchedule:
    """Load the experimental schedule shared across released participants."""
    with Path(path).open() as handle:
        next(handle)
        raw = [row[:8] for row in csv.reader(handle, delimiter="\t") if row]
    if len(raw) != 540:
        raise ValueError(f"Expected 540 trials, found {len(raw)}")

    trial_type = np.asarray([int(row[2]) for row in raw])
    reversal = np.asarray([int(row[7]) for row in raw], dtype=bool)
    block_index = np.repeat(np.arange(12), 45)
    trial_in_block = np.tile(np.arange(1, 46), 12)
    cue = np.where(np.isin(trial_type, (1, 2)), 0, 1)
    rewarded_action = np.where(np.isin(trial_type, (1, 4)), 1, 0)

    cue_one_go_before_reversal = block_index % 2 == 0
    cue_one_go_now = np.logical_xor(cue_one_go_before_reversal, reversal)
    correct_strategy_action = np.where(cue == 0, cue_one_go_now, ~cue_one_go_now).astype(int)

    for start in range(0, 540, 45):
        boundary = np.flatnonzero(reversal[start:start + 45])
        if boundary.size == 0 or not 20 <= int(boundary[0]) <= 25:
            raise ValueError("Unexpected reversal structure")

    return ReversalSchedule(
        cue=cue,
        rewarded_action=rewarded_action,
        correct_strategy_action=correct_strategy_action,
        reversal=reversal,
        block_index=block_index,
        trial_in_block=trial_in_block,
    )


def aligned_strategy_curve(values: np.ndarray, schedule: ReversalSchedule) -> np.ndarray:
    """Average 20 pre- and 20 post-reversal values across twelve blocks."""
    values = np.asarray(values, dtype=float)
    if values.shape != (schedule.n_trials,):
        raise ValueError("values must have one entry per trial")
    windows = []
    for block in range(12):
        indices = np.flatnonzero(schedule.block_index == block)
        local_reversal = np.flatnonzero(schedule.reversal[indices])[0]
        windows.append(values[indices[local_reversal - 20:local_reversal + 20]])
    return np.mean(windows, axis=0)


def simulate_q_learner(
    schedule: ReversalSchedule,
    learning_rate: float,
    inverse_temperature: float,
    seed: int,
    reset_each_block: bool = True,
) -> dict[str, np.ndarray]:
    """Run a two-cue, two-action model-free Q learner on the frozen schedule."""
    rng = np.random.default_rng(seed)
    q_values = np.zeros((2, 2), dtype=float)
    actions = np.empty(schedule.n_trials, dtype=int)
    rewards = np.empty(schedule.n_trials, dtype=float)
    probabilities = np.empty(schedule.n_trials, dtype=float)

    for trial in range(schedule.n_trials):
        if reset_each_block and schedule.trial_in_block[trial] == 1:
            q_values.fill(0.0)
        cue = int(schedule.cue[trial])
        logits = inverse_temperature * q_values[cue]
        logits -= np.max(logits)
        probability_go = float(np.exp(logits[1]) / np.exp(logits).sum())
        action = int(rng.random() < probability_go)
        reward = float(action == schedule.rewarded_action[trial])
        q_values[cue, action] += learning_rate * (reward - q_values[cue, action])
        actions[trial] = action
        rewards[trial] = reward
        probabilities[trial] = probability_go

    correct_strategy = (actions == schedule.correct_strategy_action).astype(float)
    return {
        "actions": actions,
        "rewards": rewards,
        "probability_go": probabilities,
        "correct_strategy": correct_strategy,
        "aligned_curve": aligned_strategy_curve(correct_strategy, schedule),
    }
