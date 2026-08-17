import unittest

import numpy as np

from luppi_recreation.functional_embedding import (
    parcel_functional_connectivity,
    select_stimulation_parcel,
    summarize_functional_embedding,
)


class FunctionalEmbeddingTests(unittest.TestCase):
    def test_known_signed_matrix_produces_exact_strengths(self) -> None:
        connectivity = np.array(
            [
                [0.0, 0.5, -0.2, 0.0],
                [0.5, 0.0, -0.4, 0.1],
                [-0.2, -0.4, 0.0, 0.3],
                [0.0, 0.1, 0.3, 0.0],
            ]
        )
        result = summarize_functional_embedding(connectivity)
        np.testing.assert_allclose(result.positive_strength, [0.5, 0.6, 0.3, 0.4])
        np.testing.assert_allclose(result.negative_strength, [0.2, 0.4, 0.6, 0.0])
        np.testing.assert_allclose(result.total_absolute_strength, [0.7, 1.0, 0.9, 0.4])
        np.testing.assert_allclose(
            result.mixed_sign_strength, np.sqrt([0.1, 0.24, 0.18, 0.0])
        )

    def test_diagonal_is_excluded_even_if_supplied_as_one(self) -> None:
        connectivity = np.array([[1.0, -0.25], [-0.25, 1.0]])
        result = summarize_functional_embedding(connectivity)
        np.testing.assert_allclose(result.positive_strength, 0.0)
        np.testing.assert_allclose(result.negative_strength, 0.25)

    def test_global_signal_regression_removes_shared_component(self) -> None:
        rng = np.random.default_rng(8)
        global_signal = rng.normal(size=500)
        independent = rng.normal(size=(500, 3))
        signals = independent + 3 * global_signal[:, None]
        without_gsr = parcel_functional_connectivity(signals)
        with_gsr = parcel_functional_connectivity(signals, global_signal=global_signal)
        self.assertGreater(np.mean(without_gsr[np.triu_indices(3, 1)]), 0.8)
        self.assertLess(abs(np.mean(with_gsr[np.triu_indices(3, 1)])), 0.1)

    def test_stimulation_parcel_uses_unique_maximum_overlap(self) -> None:
        atlas = np.zeros((5, 5, 5), dtype=int)
        atlas[:3] = 4
        atlas[3:] = 9
        stimulation = np.zeros_like(atlas, dtype=bool)
        stimulation[1:4] = True
        brain = atlas > 0
        self.assertEqual(select_stimulation_parcel(atlas, stimulation, brain), 4)

    def test_asymmetric_connectivity_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "symmetric"):
            summarize_functional_embedding(np.array([[0.0, 0.2], [0.1, 0.0]]))


if __name__ == "__main__":
    unittest.main()
