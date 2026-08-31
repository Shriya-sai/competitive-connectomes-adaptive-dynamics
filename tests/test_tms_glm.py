import unittest

import numpy as np
import pandas as pd

from luppi_recreation.tms_glm import (
    MOTION_COLUMNS,
    audit_tms_design,
    build_tms_design,
    estimate_ols_contrasts,
)


class TmsGlmTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame_times = np.arange(167) * 2.4
        self.events = pd.DataFrame(
            {
                "onset": np.arange(12.0, 389.0, 6.0),
                "duration": 0.0,
                "trial_type": "TMS_pulse",
            }
        )
        rng = np.random.default_rng(7)
        self.confounds = pd.DataFrame(index=np.arange(167))
        for parameter in ("trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"):
            values = np.cumsum(rng.normal(0, 0.002, size=167))
            self.confounds[parameter] = values
            self.confounds[f"{parameter}_derivative1"] = np.diff(values, prepend=values[0])
        self.confounds = self.confounds.loc[:, MOTION_COLUMNS]
        self.confounds["framewise_displacement"] = 0.0

    def test_design_is_full_rank_and_includes_censor_spike(self) -> None:
        self.confounds.loc[40, "framewise_displacement"] = 0.7
        design = build_tms_design(self.frame_times, self.events, self.confounds)
        audit = audit_tms_design(design)
        self.assertTrue(audit.full_rank)
        self.assertEqual(audit.censored_volumes, 1)
        self.assertIn("censor_040", design)

    def test_known_tms_effect_is_recovered(self) -> None:
        design = build_tms_design(self.frame_times, self.events, self.confounds)
        rng = np.random.default_rng(19)
        true_effect = np.array([0.75, -0.4, 0.0])
        signal = np.outer(design["TMS_pulse"], true_effect)
        signal += rng.normal(0, 0.0001, size=signal.shape)
        recovered = estimate_ols_contrasts(design, signal)
        np.testing.assert_allclose(recovered, true_effect, atol=0.03)

    def test_source_event_spelling_is_canonicalized(self) -> None:
        events = self.events.copy()
        events["trial_type"] = "TMSpulse"
        design = build_tms_design(self.frame_times, events, self.confounds)
        self.assertIn("TMS_pulse", design.columns)
        self.assertNotIn("TMSpulse", design.columns)

    def test_missing_motion_parameter_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing frozen motion confounds"):
            build_tms_design(
                self.frame_times,
                self.events,
                self.confounds.drop(columns="rot_z_derivative1"),
            )


if __name__ == "__main__":
    unittest.main()
