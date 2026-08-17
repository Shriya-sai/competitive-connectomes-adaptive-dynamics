import unittest

import numpy as np

from luppi_recreation.tms_spatial import measure_tms_spatial_response


class TmsSpatialTests(unittest.TestCase):
    def setUp(self) -> None:
        shape = (31, 9, 9)
        self.beta = np.zeros(shape)
        self.z_map = np.zeros(shape)
        self.atlas = np.zeros(shape, dtype=int)
        self.atlas[:7] = 1
        self.atlas[10:17] = 2
        self.atlas[24:] = 3
        self.brain = self.atlas > 0
        self.stimulation = np.zeros(shape, dtype=bool)
        self.stimulation[3, 4, 4] = True

    def measure(self):
        return measure_tms_spatial_response(
            self.beta,
            self.z_map,
            self.atlas,
            self.stimulation,
            self.brain,
            voxel_sizes_mm=(2.0, 2.0, 2.0),
            exclusion_buffer_mm=10.0,
        )

    def test_local_only_effect_is_not_called_remote_propagation(self) -> None:
        self.beta[self.atlas == 1] = 2.0
        result = self.measure()
        self.assertEqual(result.local_absolute_beta, 2.0)
        self.assertEqual(result.remote_mean_absolute_beta, 0.0)
        np.testing.assert_array_equal(result.remote_labels, [2, 3])

    def test_positive_negative_and_extent_are_retained(self) -> None:
        self.beta[self.atlas == 2] = 1.5
        self.beta[self.atlas == 3] = -0.5
        self.z_map[self.atlas == 2] = 4.0
        self.z_map[self.atlas == 3] = -2.0
        result = self.measure()
        self.assertAlmostEqual(result.remote_mean_absolute_beta, 1.0)
        self.assertAlmostEqual(result.remote_mean_positive_beta, 0.75)
        self.assertAlmostEqual(result.remote_mean_negative_magnitude, 0.25)
        self.assertAlmostEqual(result.remote_response_extent, 0.5)

    def test_parcels_touching_buffer_are_excluded(self) -> None:
        self.stimulation[6, 4, 4] = True
        result = self.measure()
        np.testing.assert_array_equal(result.remote_labels, [3])

    def test_shape_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "share one"):
            measure_tms_spatial_response(
                self.beta[:-1],
                self.z_map,
                self.atlas,
                self.stimulation,
                self.brain,
                voxel_sizes_mm=(2.0, 2.0, 2.0),
            )


if __name__ == "__main__":
    unittest.main()
