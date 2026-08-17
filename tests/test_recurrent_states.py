import numpy as np
import pytest

from luppi_recreation.recurrent_states import (
    adjusted_rand_index,
    cluster_connectivity_states,
    windowed_functional_connectivity,
)


def test_windowed_fc_shapes_and_centers():
    rng = np.random.default_rng(1)
    result = windowed_functional_connectivity(
        rng.normal(size=(4, 30)), window_size=10, step=5
    )
    assert result.matrices.shape == (5, 4, 4)
    assert result.features.shape == (5, 6)
    np.testing.assert_allclose(result.centers, [4.5, 9.5, 14.5, 19.5, 24.5])
    np.testing.assert_allclose(np.diagonal(result.matrices, axis1=1, axis2=2), 1)


def test_adjusted_rand_is_permutation_invariant():
    true = np.array([0, 0, 1, 1, 2, 2])
    permuted = np.array([2, 2, 0, 0, 1, 1])
    assert adjusted_rand_index(true, permuted) == pytest.approx(1.0)


def test_clustering_separates_obvious_feature_groups():
    features = np.vstack([np.zeros((5, 3)), np.full((5, 3), 10.0)])
    labels, centroids = cluster_connectivity_states(features, n_states=2, seed=4)
    assert adjusted_rand_index(np.repeat([0, 1], 5), labels) == pytest.approx(1.0)
    assert centroids.shape == (2, 3)


@pytest.mark.parametrize("window_size", [2, 31])
def test_invalid_window_size_rejected(window_size):
    with pytest.raises(ValueError):
        windowed_functional_connectivity(
            np.ones((3, 30)), window_size=window_size
        )
