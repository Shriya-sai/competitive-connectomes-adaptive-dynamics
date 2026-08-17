"""Resting-state functional embedding for the empirical TMS-fMRI bridge."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FunctionalEmbedding:
    """Positive, negative, unsigned and jointly mixed node strengths."""

    positive_strength: np.ndarray
    negative_strength: np.ndarray
    total_absolute_strength: np.ndarray
    mixed_sign_strength: np.ndarray


def parcel_functional_connectivity(
    time_series: np.ndarray,
    *,
    global_signal: np.ndarray | None = None,
) -> np.ndarray:
    """Return parcelwise Pearson FC, optionally after global-signal regression.

    Input time series must already have undergone the frozen temporal filtering,
    nuisance regression and censoring steps. Shape is timepoints by parcels.
    """

    signals = np.asarray(time_series, dtype=np.float64)
    if signals.ndim != 2 or signals.shape[0] < 20 or signals.shape[1] < 2:
        raise ValueError("time_series must have shape (at least 20 timepoints, parcels)")
    if not np.all(np.isfinite(signals)):
        raise ValueError("time_series must contain only finite values")
    if np.any(np.std(signals, axis=0) == 0):
        raise ValueError("every parcel time series must vary")
    if global_signal is not None:
        global_signal = np.asarray(global_signal, dtype=np.float64)
        if global_signal.shape != (signals.shape[0],):
            raise ValueError("global_signal must have one value per timepoint")
        if not np.all(np.isfinite(global_signal)) or np.std(global_signal) == 0:
            raise ValueError("global_signal must be finite and vary over time")
        design = np.column_stack((global_signal, np.ones(signals.shape[0])))
        signals = signals - design @ np.linalg.lstsq(design, signals, rcond=None)[0]
    connectivity = np.corrcoef(signals, rowvar=False)
    np.fill_diagonal(connectivity, 0.0)
    return connectivity


def summarize_functional_embedding(connectivity: np.ndarray) -> FunctionalEmbedding:
    """Calculate node strengths from a symmetric signed FC matrix."""

    connectivity = np.asarray(connectivity, dtype=np.float64)
    if connectivity.ndim != 2 or connectivity.shape[0] != connectivity.shape[1]:
        raise ValueError("connectivity must be a square matrix")
    if not np.all(np.isfinite(connectivity)):
        raise ValueError("connectivity must contain only finite values")
    if not np.allclose(connectivity, connectivity.T, atol=1e-10):
        raise ValueError("functional connectivity must be symmetric")
    if np.any(np.abs(connectivity) > 1 + 1e-10):
        raise ValueError("correlations must lie between -1 and 1")
    connectivity = connectivity.copy()
    np.fill_diagonal(connectivity, 0.0)
    positive = np.sum(np.clip(connectivity, 0, None), axis=1)
    negative = np.sum(np.clip(-connectivity, 0, None), axis=1)
    return FunctionalEmbedding(
        positive_strength=positive,
        negative_strength=negative,
        total_absolute_strength=positive + negative,
        mixed_sign_strength=np.sqrt(positive * negative),
    )


def select_stimulation_parcel(
    atlas_labels: np.ndarray,
    stimulation_mask: np.ndarray,
    brain_mask: np.ndarray,
) -> int:
    """Select the cortical parcel with maximum stimulation-sphere overlap."""

    atlas = np.asarray(atlas_labels)
    stimulation = np.asarray(stimulation_mask, dtype=bool)
    brain = np.asarray(brain_mask, dtype=bool)
    if atlas.shape != stimulation.shape or atlas.shape != brain.shape or atlas.ndim != 3:
        raise ValueError("atlas, stimulation mask and brain mask must share a 3D shape")
    labels, counts = np.unique(atlas[stimulation & brain & (atlas > 0)], return_counts=True)
    if labels.size == 0:
        raise ValueError("stimulation sphere does not overlap a labeled cortical parcel")
    maximum = np.max(counts)
    winners = labels[counts == maximum]
    if winners.size != 1:
        raise ValueError("stimulation sphere has a tied maximum parcel overlap")
    return int(winners[0])
