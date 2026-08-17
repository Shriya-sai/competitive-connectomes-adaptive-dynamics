"""Windowed-functional-connectivity tools for recurrent-state analysis."""

from dataclasses import dataclass

import numpy as np
from scipy.cluster.vq import kmeans2


@dataclass(frozen=True)
class WindowedConnectivity:
    """Functional-connectivity observations derived from sliding windows."""

    matrices: np.ndarray
    features: np.ndarray
    starts: np.ndarray
    centers: np.ndarray


def windowed_functional_connectivity(
    signals: np.ndarray, *, window_size: int, step: int = 1
) -> WindowedConnectivity:
    """Calculate one regional correlation matrix per sliding time window."""

    signals = np.asarray(signals, dtype=np.float64)
    if signals.ndim != 2 or signals.shape[0] < 2:
        raise ValueError("signals must have shape (at least 2 regions, timepoints)")
    if not np.all(np.isfinite(signals)):
        raise ValueError("signals must contain only finite values")
    if not isinstance(window_size, int) or window_size < 3:
        raise ValueError("window_size must be an integer of at least 3")
    if window_size > signals.shape[1]:
        raise ValueError("window_size cannot exceed the recording length")
    if not isinstance(step, int) or step < 1:
        raise ValueError("step must be a positive integer")

    starts = np.arange(0, signals.shape[1] - window_size + 1, step)
    matrices = np.empty((starts.size, signals.shape[0], signals.shape[0]))
    upper_triangle = np.triu_indices(signals.shape[0], k=1)
    features = np.empty((starts.size, upper_triangle[0].size))
    for index, start in enumerate(starts):
        matrix = np.corrcoef(signals[:, start : start + window_size])
        if not np.all(np.isfinite(matrix)):
            raise ValueError("every region must vary within every window")
        matrices[index] = matrix
        features[index] = matrix[upper_triangle]
    centers = starts + (window_size - 1) / 2
    return WindowedConnectivity(matrices, features, starts, centers)


def cluster_connectivity_states(
    features: np.ndarray, *, n_states: int, seed: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    """Cluster vectorized windowed-FC observations with deterministic k-means."""

    features = np.asarray(features, dtype=np.float64)
    if features.ndim != 2 or features.shape[0] < 2:
        raise ValueError("features must have shape (windows, connections)")
    if not np.all(np.isfinite(features)):
        raise ValueError("features must contain only finite values")
    if not isinstance(n_states, int) or not 2 <= n_states <= features.shape[0]:
        raise ValueError("n_states must lie between 2 and the number of windows")

    rng = np.random.default_rng(seed)
    centroids, labels = kmeans2(
        features, n_states, iter=100, minit="++", rng=rng
    )
    return labels.astype(int), centroids


def adjusted_rand_index(labels_true: np.ndarray, labels_pred: np.ndarray) -> float:
    """Return the label-permutation-invariant adjusted Rand index."""

    labels_true = np.asarray(labels_true)
    labels_pred = np.asarray(labels_pred)
    if labels_true.ndim != 1 or labels_pred.ndim != 1:
        raise ValueError("labels must be one-dimensional")
    if labels_true.size != labels_pred.size or labels_true.size < 2:
        raise ValueError("label arrays must have equal length of at least 2")

    _, true_inverse = np.unique(labels_true, return_inverse=True)
    _, pred_inverse = np.unique(labels_pred, return_inverse=True)
    table = np.zeros(
        (true_inverse.max() + 1, pred_inverse.max() + 1), dtype=np.int64
    )
    np.add.at(table, (true_inverse, pred_inverse), 1)

    choose_two = lambda values: np.sum(values * (values - 1) / 2)
    observed = choose_two(table)
    true_pairs = choose_two(table.sum(axis=1))
    pred_pairs = choose_two(table.sum(axis=0))
    total_pairs = labels_true.size * (labels_true.size - 1) / 2
    expected = true_pairs * pred_pairs / total_pairs
    maximum = (true_pairs + pred_pairs) / 2
    if maximum == expected:
        return 1.0 if np.array_equal(true_inverse, pred_inverse) else 0.0
    return float((observed - expected) / (maximum - expected))
