"""Tests for loading the released single-subject data."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.io import savemat

from luppi_recreation.data import load_single_subject


class LoadSingleSubjectTests(unittest.TestCase):
    def test_loads_valid_matrices(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            savemat(path / "SC.mat", {"SC": np.eye(3)})
            savemat(path / "FMRI.mat", {"FMRI": np.ones((3, 20))})

            data = load_single_subject(path)

            self.assertEqual(data.structural_connectivity.shape, (3, 3))
            self.assertEqual(data.bold.shape, (3, 20))
            self.assertEqual(data.n_regions, 3)
            self.assertEqual(data.n_timepoints, 20)

    def test_rejects_mismatched_region_counts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            savemat(path / "SC.mat", {"SC": np.eye(3)})
            savemat(path / "FMRI.mat", {"FMRI": np.ones((4, 20))})

            with self.assertRaisesRegex(ValueError, "same number of regions"):
                load_single_subject(path)


if __name__ == "__main__":
    unittest.main()
