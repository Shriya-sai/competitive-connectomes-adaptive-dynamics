"""Tests for locating the compiled upstream Hopf extension."""

import unittest
from pathlib import Path

import numpy as np

from luppi_recreation.hopf_backend import load_hopf_extension


class HopfBackendTests(unittest.TestCase):
    def test_loads_extension_and_runs_tiny_simulation(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        upstream_root = project_root / "upstream" / "competitive-cooperative-hopf"
        hopf = load_hopf_extension(upstream_root)

        result = hopf.simulate(
            np.eye(3, dtype=np.float64) * 0.001,
            np.array([0.03, 0.04, 0.05], dtype=np.float64),
            10,
            0.72,
            0.001,
            -0.02,
            1,
        )

        self.assertEqual(result.shape, (3, 10))
        self.assertTrue(np.isfinite(result).all())

    def test_seed_controls_stochastic_simulation(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        upstream_root = project_root / "upstream" / "competitive-cooperative-hopf"
        hopf = load_hopf_extension(upstream_root)
        connectivity = np.eye(3, dtype=np.float64) * 0.001
        frequencies = np.array([0.03, 0.04, 0.05], dtype=np.float64)

        first = hopf.simulate(connectivity, frequencies, 20, 0.72, 0.001, -0.02, 1, 7)
        repeated = hopf.simulate(
            connectivity, frequencies, 20, 0.72, 0.001, -0.02, 1, 7
        )
        different = hopf.simulate(
            connectivity, frequencies, 20, 0.72, 0.001, -0.02, 1, 8
        )

        np.testing.assert_array_equal(first, repeated)
        self.assertFalse(np.array_equal(first, different))


if __name__ == "__main__":
    unittest.main()
