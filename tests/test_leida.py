import numpy as np
import pytest

from luppi_recreation.leida import (
    cluster_projective_states,
    leading_phase_eigenvectors,
    projective_angular_distances,
    summarize_leida_landscape,
)


def test_leading_vector_matches_full_phase_locking_eigendecomposition():
    rng = np.random.default_rng(2)
    phases = rng.uniform(-np.pi, np.pi, size=(12, 7))
    vectors, dominance = leading_phase_eigenvectors(phases)
    for timepoint in range(phases.shape[1]):
        matrix = np.cos(
            phases[:, timepoint, None] - phases[None, :, timepoint]
        )
        values, reference = np.linalg.eigh(matrix)
        similarity = abs(np.dot(vectors[timepoint], reference[:, -1]))
        assert similarity == pytest.approx(1.0)
        assert dominance[timepoint] == pytest.approx(values[-1] / phases.shape[0])


def test_perfect_alignment_has_unit_dominance():
    phases = np.tile(np.arange(5, dtype=float), (10, 1))
    _, dominance = leading_phase_eigenvectors(phases)
    np.testing.assert_allclose(dominance, 1.0)


def test_invalid_phase_shape_rejected():
    with pytest.raises(ValueError):
        leading_phase_eigenvectors(np.ones(10))


def test_projective_clustering_treats_sign_flips_as_identical():
    first = np.array([1.0, 0.0, 0.0])
    second = np.array([0.0, 1.0, 0.0])
    vectors = np.vstack([first, -first, first, second, -second, second])
    labels, _ = cluster_projective_states(vectors, n_states=2, seed=3)
    assert labels[0] == labels[1] == labels[2]
    assert labels[3] == labels[4] == labels[5]
    assert labels[0] != labels[3]


def test_projective_distance_identifies_antipodes():
    vectors = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0]])
    distances = projective_angular_distances(vectors)
    assert distances[0, 1] == pytest.approx(0.0)
    assert distances[0, 2] == pytest.approx(np.pi / 2)


def test_fixed_landscape_has_one_effective_dimension():
    vectors = np.tile([1.0, 0.0, 0.0], (30, 1))
    result = summarize_leida_landscape(
        vectors, repetition_time=1.0, recurrence_exclusion=2
    )
    assert result.repertoire_dispersion == pytest.approx(0.0)
    assert result.effective_dimension == pytest.approx(1.0)
    assert result.mean_speed == pytest.approx(0.0)
