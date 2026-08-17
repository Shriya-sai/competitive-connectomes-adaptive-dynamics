"""Null models for testing the anatomical placement of effective connections."""

import numpy as np
from scipy.optimize import linear_sum_assignment


def shuffle_reciprocal_edge_pairs(
    connectivity: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Permute reciprocal weight pairs among the matrix's occupied edges.

    The two directed weights belonging to an undirected anatomical edge remain
    together. Their orientation is independently flipped with probability 0.5.
    Consequently, the exact multiset of directed weights, the occupied
    anatomical-edge mask, and reciprocal-pair structure are all preserved.
    """

    connectivity = np.asarray(connectivity, dtype=np.float64)
    if connectivity.ndim != 2 or connectivity.shape[0] != connectivity.shape[1]:
        raise ValueError("connectivity must be a square matrix")
    if np.any(np.diag(connectivity) != 0):
        raise ValueError("connectivity must have a zero diagonal")

    upper_i, upper_j = np.triu_indices_from(connectivity, k=1)
    occupied = (connectivity[upper_i, upper_j] != 0) | (
        connectivity[upper_j, upper_i] != 0
    )
    edge_i = upper_i[occupied]
    edge_j = upper_j[occupied]
    if not np.all(
        (connectivity[edge_i, edge_j] != 0)
        & (connectivity[edge_j, edge_i] != 0)
    ):
        raise ValueError("each occupied edge must contain both directed weights")

    pairs = np.column_stack(
        (connectivity[edge_i, edge_j], connectivity[edge_j, edge_i])
    )
    pairs = pairs[rng.permutation(len(pairs))].copy()
    flip = rng.random(len(pairs)) < 0.5
    pairs[flip] = pairs[flip, ::-1]

    shuffled = np.zeros_like(connectivity)
    shuffled[edge_i, edge_j] = pairs[:, 0]
    shuffled[edge_j, edge_i] = pairs[:, 1]
    return shuffled


def shuffle_values_within_mask(
    connectivity: np.ndarray,
    mask: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Shuffle selected directed weights while leaving all other cells fixed."""

    connectivity = np.asarray(connectivity, dtype=np.float64)
    mask = np.asarray(mask, dtype=bool)
    if connectivity.shape != mask.shape:
        raise ValueError("connectivity and mask must have the same shape")
    shuffled = connectivity.copy()
    shuffled[mask] = rng.permutation(connectivity[mask])
    return shuffled


def magnitude_matched_positive_mask(connectivity: np.ndarray) -> np.ndarray:
    """Select one unique positive weight matched to each negative magnitude."""

    connectivity = np.asarray(connectivity, dtype=np.float64)
    negative_magnitudes = np.abs(connectivity[connectivity < 0])
    positive_indices = np.flatnonzero(connectivity > 0)
    positive_magnitudes = connectivity.ravel()[positive_indices]
    if len(positive_magnitudes) < len(negative_magnitudes):
        raise ValueError("not enough positive weights to match all negative weights")

    costs = np.abs(negative_magnitudes[:, None] - positive_magnitudes[None, :])
    _, matched_columns = linear_sum_assignment(costs)
    mask = np.zeros(connectivity.size, dtype=bool)
    mask[positive_indices[matched_columns]] = True
    return mask.reshape(connectivity.shape)


def shuffle_reciprocal_sign_patterns(
    connectivity: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Permute reciprocal sign patterns while keeping every magnitude in place."""

    connectivity = np.asarray(connectivity, dtype=np.float64)
    if connectivity.ndim != 2 or connectivity.shape[0] != connectivity.shape[1]:
        raise ValueError("connectivity must be a square matrix")
    if np.any(np.diag(connectivity) != 0):
        raise ValueError("connectivity must have a zero diagonal")

    upper_i, upper_j = np.triu_indices_from(connectivity, k=1)
    occupied = (connectivity[upper_i, upper_j] != 0) | (
        connectivity[upper_j, upper_i] != 0
    )
    edge_i = upper_i[occupied]
    edge_j = upper_j[occupied]
    if not np.all(
        (connectivity[edge_i, edge_j] != 0)
        & (connectivity[edge_j, edge_i] != 0)
    ):
        raise ValueError("each occupied edge must contain both directed weights")

    sign_patterns = np.column_stack(
        (np.sign(connectivity[edge_i, edge_j]), np.sign(connectivity[edge_j, edge_i]))
    )
    sign_patterns = sign_patterns[rng.permutation(len(sign_patterns))].copy()
    flip = rng.random(len(sign_patterns)) < 0.5
    sign_patterns[flip] = sign_patterns[flip, ::-1]

    shuffled = connectivity.copy()
    shuffled[edge_i, edge_j] = (
        np.abs(connectivity[edge_i, edge_j]) * sign_patterns[:, 0]
    )
    shuffled[edge_j, edge_i] = (
        np.abs(connectivity[edge_j, edge_i]) * sign_patterns[:, 1]
    )
    return shuffled
