import unittest

import numpy as np

from luppi_recreation.connectivity_nulls import (
    magnitude_matched_positive_mask,
    shuffle_reciprocal_edge_pairs,
    shuffle_reciprocal_sign_patterns,
    shuffle_values_within_mask,
)


class ConnectivityNullTests(unittest.TestCase):
    def test_shuffle_preserves_weights_mask_and_reciprocal_differences(self) -> None:
        connectivity = np.array(
            [
                [0.0, 1.0, 0.0, -2.0],
                [1.1, 0.0, 3.0, 0.0],
                [0.0, 3.1, 0.0, 4.0],
                [-2.1, 0.0, 4.1, 0.0],
            ]
        )
        shuffled = shuffle_reciprocal_edge_pairs(
            connectivity, np.random.default_rng(7)
        )

        np.testing.assert_array_equal(shuffled != 0, connectivity != 0)
        np.testing.assert_array_equal(
            np.sort(shuffled.ravel()), np.sort(connectivity.ravel())
        )

        upper = np.triu_indices_from(connectivity, k=1)
        original_differences = np.sort(
            np.abs(connectivity[upper] - connectivity.T[upper])
        )
        shuffled_differences = np.sort(
            np.abs(shuffled[upper] - shuffled.T[upper])
        )
        np.testing.assert_allclose(shuffled_differences, original_differences)

    def test_within_mask_shuffle_leaves_unselected_values_fixed(self) -> None:
        connectivity = np.array([[0.0, -1.0, 2.0], [-3.0, 0.0, 4.0], [5.0, -6.0, 0.0]])
        mask = connectivity < 0
        shuffled = shuffle_values_within_mask(
            connectivity, mask, np.random.default_rng(2)
        )

        np.testing.assert_array_equal(shuffled[~mask], connectivity[~mask])
        np.testing.assert_array_equal(
            np.sort(shuffled[mask]), np.sort(connectivity[mask])
        )

    def test_positive_matching_uses_negative_count_and_positive_cells(self) -> None:
        connectivity = np.array([[0.0, -1.0, 1.1], [-2.0, 0.0, 2.1], [8.0, 9.0, 0.0]])
        mask = magnitude_matched_positive_mask(connectivity)

        self.assertEqual(np.count_nonzero(mask), np.count_nonzero(connectivity < 0))
        self.assertTrue(np.all(connectivity[mask] > 0))

    def test_sign_shuffle_preserves_magnitudes_and_pair_categories(self) -> None:
        connectivity = np.array(
            [
                [0.0, 1.0, 0.0, -2.0],
                [1.1, 0.0, 3.0, 0.0],
                [0.0, -3.1, 0.0, -4.0],
                [-2.1, 0.0, -4.1, 0.0],
            ]
        )
        shuffled = shuffle_reciprocal_sign_patterns(
            connectivity, np.random.default_rng(9)
        )

        np.testing.assert_array_equal(np.abs(shuffled), np.abs(connectivity))
        self.assertEqual(np.count_nonzero(shuffled < 0), np.count_nonzero(connectivity < 0))

        def categories(matrix):
            i, j = np.triu_indices_from(matrix, k=1)
            occupied = (matrix[i, j] != 0) | (matrix[j, i] != 0)
            products = np.sign(matrix[i[occupied], j[occupied]]) * np.sign(
                matrix[j[occupied], i[occupied]]
            )
            both_negative = (matrix[i[occupied], j[occupied]] < 0) & (
                matrix[j[occupied], i[occupied]] < 0
            )
            return np.sum(products < 0), np.sum(both_negative)

        self.assertEqual(categories(shuffled), categories(connectivity))


if __name__ == "__main__":
    unittest.main()
