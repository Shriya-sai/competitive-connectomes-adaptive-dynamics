"""Frozen first-level design utilities for the TMS-fMRI empirical pilot."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from nilearn.glm.first_level import make_first_level_design_matrix


MOTION_COLUMNS = tuple(
    f"{parameter}{suffix}"
    for parameter in ("trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z")
    for suffix in ("", "_derivative1")
)


@dataclass(frozen=True)
class DesignAudit:
    """Numerical checks that must pass before fitting an empirical GLM."""

    n_timepoints: int
    n_regressors: int
    rank: int
    condition_number: float
    tms_max_nuisance_correlation: float
    censored_volumes: int

    @property
    def full_rank(self) -> bool:
        return self.rank == self.n_regressors


def build_tms_design(
    frame_times: np.ndarray,
    events: pd.DataFrame,
    confounds: pd.DataFrame,
    *,
    high_pass_hz: float = 0.01,
    fd_threshold_mm: float = 0.5,
) -> pd.DataFrame:
    """Build the frozen mean-response GLM with motion and censor regressors."""

    frame_times = np.asarray(frame_times, dtype=np.float64)
    if frame_times.ndim != 1 or frame_times.size < 20:
        raise ValueError("frame_times must contain at least 20 samples")
    if len(confounds) != frame_times.size:
        raise ValueError("confounds must have one row per acquired volume")
    missing = sorted(set(MOTION_COLUMNS) - set(confounds.columns))
    if missing:
        raise ValueError(f"missing frozen motion confounds: {missing}")
    if "framewise_displacement" not in confounds:
        raise ValueError("missing framewise_displacement")
    required_events = {"onset", "duration", "trial_type"}
    if not required_events.issubset(events.columns):
        raise ValueError(f"events must contain {sorted(required_events)}")

    nuisance = confounds.loc[:, MOTION_COLUMNS].fillna(0.0).astype(float).copy()
    fd = confounds["framewise_displacement"].fillna(0.0).to_numpy(float)
    flagged = set(np.flatnonzero(fd > fd_threshold_mm).tolist())
    for column in confounds.columns:
        if column.startswith("motion_outlier"):
            flagged.update(np.flatnonzero(confounds[column].fillna(0).to_numpy() > 0).tolist())
    for index in sorted(flagged):
        nuisance[f"censor_{index:03d}"] = np.eye(frame_times.size, dtype=float)[:, index]

    return make_first_level_design_matrix(
        frame_times,
        events=events,
        hrf_model="spm",
        drift_model="cosine",
        high_pass=high_pass_hz,
        add_regs=nuisance.to_numpy(),
        add_reg_names=list(nuisance.columns),
    )


def audit_tms_design(design: pd.DataFrame) -> DesignAudit:
    """Summarize estimability and task-versus-nuisance separation."""

    if "TMS_pulse" not in design or "constant" not in design:
        raise ValueError("design must contain TMS_pulse and constant columns")
    matrix = design.to_numpy(dtype=float)
    nuisance_names = [
        name for name in design.columns if name not in {"TMS_pulse", "constant"}
    ]
    correlations = [
        abs(float(np.corrcoef(design["TMS_pulse"], design[name])[0, 1]))
        for name in nuisance_names
        if float(np.std(design[name])) > 0
    ]
    return DesignAudit(
        n_timepoints=matrix.shape[0],
        n_regressors=matrix.shape[1],
        rank=int(np.linalg.matrix_rank(matrix)),
        condition_number=float(np.linalg.cond(matrix)),
        tms_max_nuisance_correlation=max(correlations, default=0.0),
        censored_volumes=sum(name.startswith("censor_") for name in design.columns),
    )


def estimate_ols_contrasts(design: pd.DataFrame, signals: np.ndarray) -> np.ndarray:
    """Estimate the TMS coefficient for time-by-feature synthetic signals."""

    signals = np.asarray(signals, dtype=np.float64)
    if signals.ndim == 1:
        signals = signals[:, None]
    if signals.ndim != 2 or signals.shape[0] != len(design):
        raise ValueError("signals must have shape (timepoints, features)")
    coefficients = np.linalg.lstsq(design.to_numpy(), signals, rcond=None)[0]
    return coefficients[design.columns.get_loc("TMS_pulse")]
