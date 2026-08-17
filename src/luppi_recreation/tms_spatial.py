"""Frozen spatial response measurements for the empirical TMS-fMRI bridge."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import distance_transform_edt


@dataclass(frozen=True)
class SpatialResponse:
    """Local and parcelwise-remote summaries of one TMS contrast map."""

    local_signed_beta: float
    local_absolute_beta: float
    remote_mean_absolute_beta: float
    remote_mean_positive_beta: float
    remote_mean_negative_magnitude: float
    remote_response_extent: float
    n_remote_parcels: int
    remote_labels: np.ndarray
    remote_parcel_betas: np.ndarray
    remote_parcel_z_scores: np.ndarray


def measure_tms_spatial_response(
    beta_map: np.ndarray,
    z_map: np.ndarray,
    atlas_labels: np.ndarray,
    stimulation_mask: np.ndarray,
    brain_mask: np.ndarray,
    *,
    voxel_sizes_mm: tuple[float, float, float],
    exclusion_buffer_mm: float = 10.0,
    extent_z_threshold: float = 3.1,
) -> SpatialResponse:
    """Measure local response and remote parcelwise propagation.

    Parcels touching the stimulation sphere or its physical-distance buffer are
    excluded. Remaining parcels receive equal weight regardless of voxel count.
    """

    beta = np.asarray(beta_map, dtype=np.float64)
    z_values = np.asarray(z_map, dtype=np.float64)
    atlas = np.asarray(atlas_labels)
    stimulation = np.asarray(stimulation_mask, dtype=bool)
    brain = np.asarray(brain_mask, dtype=bool)
    shapes = {array.shape for array in (beta, z_values, atlas, stimulation, brain)}
    if len(shapes) != 1 or beta.ndim != 3:
        raise ValueError("all spatial inputs must share one three-dimensional shape")
    if not np.all(np.isfinite(beta[brain])) or not np.all(np.isfinite(z_values[brain])):
        raise ValueError("beta and z maps must be finite inside the brain mask")
    if not np.any(stimulation & brain):
        raise ValueError("stimulation mask does not overlap the brain mask")
    if len(voxel_sizes_mm) != 3 or any(value <= 0 for value in voxel_sizes_mm):
        raise ValueError("voxel_sizes_mm must contain three positive values")
    if exclusion_buffer_mm < 0 or extent_z_threshold <= 0:
        raise ValueError("buffer must be non-negative and z threshold positive")

    local = stimulation & brain
    local_signed = float(np.mean(beta[local]))
    distance_from_local = distance_transform_edt(
        ~local, sampling=voxel_sizes_mm
    )
    exclusion = distance_from_local <= exclusion_buffer_mm

    labels = np.unique(atlas[(atlas > 0) & brain])
    remote_labels: list[int] = []
    parcel_betas: list[float] = []
    parcel_z_scores: list[float] = []
    for label in labels:
        parcel = (atlas == label) & brain
        if np.any(parcel & exclusion):
            continue
        remote_labels.append(int(label))
        parcel_betas.append(float(np.mean(beta[parcel])))
        parcel_z_scores.append(float(np.mean(z_values[parcel])))

    if not remote_labels:
        raise ValueError("no remote parcels remain after local exclusion")
    parcel_betas_array = np.asarray(parcel_betas)
    parcel_z_array = np.asarray(parcel_z_scores)
    positive = np.clip(parcel_betas_array, 0, None)
    negative_magnitude = np.clip(-parcel_betas_array, 0, None)
    return SpatialResponse(
        local_signed_beta=local_signed,
        local_absolute_beta=abs(local_signed),
        remote_mean_absolute_beta=float(np.mean(np.abs(parcel_betas_array))),
        remote_mean_positive_beta=float(np.mean(positive)),
        remote_mean_negative_magnitude=float(np.mean(negative_magnitude)),
        remote_response_extent=float(
            np.mean(np.abs(parcel_z_array) >= extent_z_threshold)
        ),
        n_remote_parcels=len(remote_labels),
        remote_labels=np.asarray(remote_labels, dtype=int),
        remote_parcel_betas=parcel_betas_array,
        remote_parcel_z_scores=parcel_z_array,
    )
