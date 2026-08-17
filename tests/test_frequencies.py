"""Tests for regional-frequency extraction."""

import unittest
from pathlib import Path

import numpy as np
from scipy.io import loadmat

from luppi_recreation.frequencies import extract_regional_frequencies


class ExtractRegionalFrequenciesTests(unittest.TestCase):
    def test_recovers_known_sinusoidal_frequencies(self) -> None:
        repetition_time = 0.72
        n_timepoints = 2000
        time = np.arange(n_timepoints) * repetition_time
        expected = np.array([0.02, 0.04, 0.07])
        bold = np.vstack(
            [np.sin(2.0 * np.pi * frequency * time) for frequency in expected]
        )

        observed = extract_regional_frequencies(bold, repetition_time)

        frequency_resolution = 1.0 / (n_timepoints * repetition_time)
        np.testing.assert_allclose(observed, expected, atol=2 * frequency_resolution)

    def test_returns_one_frequency_per_region(self) -> None:
        rng = np.random.default_rng(42)
        bold = rng.normal(size=(5, 500))

        observed = extract_regional_frequencies(bold, repetition_time=0.72)

        self.assertEqual(observed.shape, (5,))
        self.assertTrue(np.isfinite(observed).all())

    def test_rejects_frequency_bound_above_nyquist(self) -> None:
        bold = np.ones((2, 100))

        with self.assertRaisesRegex(ValueError, "Nyquist"):
            extract_regional_frequencies(
                bold,
                repetition_time=2.0,
                filter_low=0.01,
                filter_high=0.30,
            )

    def test_matches_upstream_matlab_reference_for_released_data(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        upstream_root = project_root / "upstream" / "competitive-cooperative-hopf"
        bold = loadmat(
            upstream_root / "data" / "matlab" / "single" / "FMRI.mat"
        )["FMRI"]
        reference = loadmat(
            upstream_root
            / "data"
            / "matlab"
            / "debug"
            / "debug_inputs.mat"
        )["regionalFrequencies"].squeeze()

        observed = extract_regional_frequencies(bold, repetition_time=0.72)

        np.testing.assert_allclose(observed, reference, rtol=0.0, atol=0.0)


if __name__ == "__main__":
    unittest.main()
