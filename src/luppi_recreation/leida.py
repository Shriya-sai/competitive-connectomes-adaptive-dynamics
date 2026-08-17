"""Leading Eigenvector Dynamics Analysis of regional phase signals."""

from dataclasses import dataclass

import numpy as np

from .dynamics import instantaneous_phase


@dataclass(frozen=True)
class LeadingEigenvectorDynamics:
    """Instantaneous dominant phase-locking patterns."""

    phases: np.ndarray
    eigenvectors: np.ndarray
    dominance: np.ndarray


@dataclass(frozen=True)
class LeidaLandscape:
    """Continuous geometric summary of a LEiDA trajectory."""

    repertoire_dispersion: float
    effective_dimension: float
    mean_speed: float
    speed_variability: float
    mean_central_distance: float
    mean_nearest_recurrence_distance: float


def leading_phase_eigenvectors(phases: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the leading eigenvector of cos(phi_i-phi_j) at each timepoint.

    The phase-locking matrix is exactly the sum of two rank-one matrices,
    ``cos(phi) cos(phi).T + sin(phi) sin(phi).T``. Its dominant eigenvector is
    therefore calculated from an economical region-by-two SVD rather than by
    constructing every full region-by-region matrix.

    Eigenvector signs are arbitrary mathematically. They are oriented here so
    the largest-magnitude regional entry is positive, making repeated output
    deterministic without changing the represented phase partition.
    """

    phases = np.asarray(phases, dtype=np.float64)
    if phases.ndim != 2 or phases.shape[0] < 2 or phases.shape[1] < 1:
        raise ValueError("phases must have shape (at least 2 regions, timepoints)")
    if not np.all(np.isfinite(phases)):
        raise ValueError("phases must contain only finite values")

    n_regions, n_timepoints = phases.shape
    eigenvectors = np.empty((n_timepoints, n_regions), dtype=np.float64)
    dominance = np.empty(n_timepoints, dtype=np.float64)
    for timepoint in range(n_timepoints):
        basis = np.column_stack(
            (np.cos(phases[:, timepoint]), np.sin(phases[:, timepoint]))
        )
        left, singular, _ = np.linalg.svd(basis, full_matrices=False)
        vector = left[:, 0]
        pivot = int(np.argmax(np.abs(vector)))
        if vector[pivot] < 0:
            vector = -vector
        eigenvectors[timepoint] = vector
        dominance[timepoint] = singular[0] ** 2 / n_regions
    return eigenvectors, dominance


def leida(signals: np.ndarray, *, trim: int = 0) -> LeadingEigenvectorDynamics:
    """Calculate instantaneous leading phase-locking patterns from signals."""

    if not isinstance(trim, int) or trim < 0:
        raise ValueError("trim must be a non-negative integer")
    phases = instantaneous_phase(signals)
    eigenvectors, dominance = leading_phase_eigenvectors(phases)
    if 2 * trim >= phases.shape[1] - 1:
        raise ValueError("trim removes too many timepoints")
    if trim:
        return LeadingEigenvectorDynamics(
            phases[:, trim:-trim], eigenvectors[trim:-trim], dominance[trim:-trim]
        )
    return LeadingEigenvectorDynamics(phases, eigenvectors, dominance)


def cluster_projective_states(
    eigenvectors: np.ndarray,
    *,
    n_states: int,
    seed: int = 42,
    max_iterations: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """Cluster eigenvector axes while treating ``v`` and ``-v`` as identical.

    This projective spherical k-means assigns observations using absolute
    cosine similarity. Vectors are sign-aligned only while updating each
    centroid, preventing arbitrary eigensolver signs from creating states.
    """

    vectors = np.asarray(eigenvectors, dtype=np.float64)
    if vectors.ndim != 2 or vectors.shape[0] < 2 or vectors.shape[1] < 2:
        raise ValueError("eigenvectors must have shape (timepoints, regions)")
    if not np.all(np.isfinite(vectors)):
        raise ValueError("eigenvectors must contain only finite values")
    if not isinstance(n_states, int) or not 2 <= n_states <= vectors.shape[0]:
        raise ValueError("n_states must lie between 2 and the number of vectors")

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("eigenvectors must be non-zero")
    vectors = vectors / norms
    rng = np.random.default_rng(seed)

    # Projective k-means++ initialization with distance 1-|cosine|.
    chosen = [int(rng.integers(vectors.shape[0]))]
    closest = 1 - np.abs(vectors @ vectors[chosen[0]])
    while len(chosen) < n_states:
        probabilities = closest**2
        if probabilities.sum() == 0:
            candidates = np.setdiff1d(np.arange(vectors.shape[0]), chosen)
            chosen.append(int(rng.choice(candidates)))
        else:
            chosen.append(int(rng.choice(vectors.shape[0], p=probabilities / probabilities.sum())))
        closest = np.minimum(closest, 1 - np.abs(vectors @ vectors[chosen[-1]]))
    centroids = vectors[chosen].copy()

    previous = None
    for _ in range(max_iterations):
        labels = np.argmax(np.abs(vectors @ centroids.T), axis=1)
        if previous is not None and np.array_equal(labels, previous):
            break
        previous = labels.copy()
        for state in range(n_states):
            members = vectors[labels == state]
            if members.size == 0:
                centroids[state] = vectors[int(rng.integers(vectors.shape[0]))]
                continue
            signs = np.sign(members @ centroids[state])
            signs[signs == 0] = 1
            centroid = np.mean(members * signs[:, None], axis=0)
            centroids[state] = centroid / np.linalg.norm(centroid)
    return labels.astype(int), centroids


def projective_angular_distances(eigenvectors: np.ndarray) -> np.ndarray:
    """Pairwise angular distances with antipodal vectors identified.

    Distances range from zero (same axis, including opposite vector signs) to
    pi/2 (orthogonal phase-locking patterns).
    """

    vectors = np.asarray(eigenvectors, dtype=np.float64)
    if vectors.ndim != 2 or vectors.shape[0] < 2 or vectors.shape[1] < 2:
        raise ValueError("eigenvectors must have shape (timepoints, regions)")
    if not np.all(np.isfinite(vectors)):
        raise ValueError("eigenvectors must contain only finite values")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("eigenvectors must be non-zero")
    normalized = vectors / norms
    similarity = np.clip(np.abs(normalized @ normalized.T), 0, 1)
    return np.arccos(similarity)


def summarize_leida_landscape(
    eigenvectors: np.ndarray,
    *,
    repetition_time: float,
    recurrence_exclusion: int = 20,
) -> LeidaLandscape:
    """Summarize a continuous LEiDA trajectory without discrete states."""

    if repetition_time <= 0:
        raise ValueError("repetition_time must be positive")
    if not isinstance(recurrence_exclusion, int) or recurrence_exclusion < 0:
        raise ValueError("recurrence_exclusion must be a non-negative integer")
    vectors = np.asarray(eigenvectors, dtype=np.float64)
    distances = projective_angular_distances(vectors)
    if 2 * recurrence_exclusion + 1 >= vectors.shape[0]:
        raise ValueError("recurrence_exclusion is too large for the trajectory")
    normalized = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    upper = np.triu_indices(vectors.shape[0], k=1)
    dispersion = float(np.mean(distances[upper]))
    consecutive = np.diag(distances, k=1) / repetition_time

    scatter = normalized.T @ normalized / normalized.shape[0]
    eigenvalues, eigenbasis = np.linalg.eigh(scatter)
    eigenvalues = np.clip(eigenvalues, 0, None)
    effective_dimension = float(eigenvalues.sum() ** 2 / np.sum(eigenvalues**2))
    central_axis = eigenbasis[:, -1]
    central_distance = np.arccos(
        np.clip(np.abs(normalized @ central_axis), 0, 1)
    )

    recurrence = distances.copy()
    indices = np.arange(vectors.shape[0])
    recurrence[
        np.abs(indices[:, None] - indices[None, :]) <= recurrence_exclusion
    ] = np.inf
    nearest_recurrence = np.min(recurrence, axis=1)
    return LeidaLandscape(
        repertoire_dispersion=dispersion,
        effective_dimension=effective_dimension,
        mean_speed=float(np.mean(consecutive)),
        speed_variability=float(np.std(consecutive, ddof=0)),
        mean_central_distance=float(np.mean(central_distance)),
        mean_nearest_recurrence_distance=float(np.mean(nearest_recurrence)),
    )
