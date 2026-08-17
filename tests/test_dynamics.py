import unittest

import numpy as np

from luppi_recreation.dynamics import (
    bandpass_signals,
    instantaneous_phase,
    kuramoto_order_parameter,
    phase_dynamics,
)


class PhaseDynamicsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.n_regions = 100
        self.n_timepoints = 2000
        self.time = np.arange(self.n_timepoints, dtype=np.float64)
        self.carrier = 2 * np.pi * 0.03 * self.time

    def test_hilbert_phase_recovers_relative_sinusoid_phase(self) -> None:
        offset = np.pi / 3
        signals = np.vstack((np.cos(self.carrier), np.cos(self.carrier + offset)))
        phases = instantaneous_phase(signals)
        relative = np.angle(np.exp(1j * (phases[1] - phases[0])))
        central = relative[100:-100]
        self.assertAlmostEqual(float(np.angle(np.mean(np.exp(1j * central)))), offset, places=6)

    def test_synchronized_signals_have_unit_synchrony_and_no_metastability(self) -> None:
        signal = np.cos(self.carrier)
        result = phase_dynamics(np.repeat(signal[None, :], self.n_regions, axis=0), trim=100)
        self.assertGreater(result.synchrony, 0.999)
        self.assertLess(result.metastability, 1e-10)

    def test_evenly_dispersed_signals_have_near_zero_synchrony(self) -> None:
        offsets = np.linspace(0, 2 * np.pi, self.n_regions, endpoint=False)
        signals = np.cos(self.carrier[None, :] + offsets[:, None])
        result = phase_dynamics(signals, trim=100)
        self.assertLess(result.synchrony, 1e-10)
        self.assertLess(result.metastability, 1e-10)

    def test_switching_phase_configuration_has_high_metastability(self) -> None:
        offsets = np.linspace(0, 2 * np.pi, self.n_regions, endpoint=False)
        modulation = (1 - np.cos(2 * np.pi * self.time / 500)) / 2
        phases = self.carrier[None, :] + offsets[:, None] * modulation[None, :]
        signals = np.cos(phases)
        result = phase_dynamics(signals, trim=100)
        self.assertGreater(result.metastability, 0.20)
        self.assertGreater(np.max(result.order_parameter[100:-100]), 0.9)
        self.assertLess(np.min(result.order_parameter[100:-100]), 0.15)

    def test_known_phases_produce_expected_kuramoto_values(self) -> None:
        phases = np.array([[0.0, 0.0], [0.0, np.pi]])
        np.testing.assert_allclose(kuramoto_order_parameter(phases), [1.0, 0.0], atol=1e-15)

    def test_bandpass_retains_in_band_and_suppresses_out_of_band_components(self) -> None:
        repetition_time = 0.72
        time_seconds = self.time * repetition_time
        in_band = np.cos(2 * np.pi * 0.04 * time_seconds)
        low_drift = 2 * np.cos(2 * np.pi * 0.003 * time_seconds)
        high_noise = 2 * np.cos(2 * np.pi * 0.20 * time_seconds)
        filtered = bandpass_signals(
            np.vstack((in_band + low_drift + high_noise,) * 2), repetition_time
        )[0]
        central = slice(100, -100)
        correlation = np.corrcoef(filtered[central], in_band[central])[0, 1]
        self.assertGreater(correlation, 0.99)

    def test_bandpass_rejects_invalid_frequency_bounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "Nyquist"):
            bandpass_signals(np.ones((2, 100)), 0.72, filter_high=1.0)

    def test_rejects_constant_signal(self) -> None:
        with self.assertRaisesRegex(ValueError, "must vary"):
            instantaneous_phase(np.ones((3, 20)))


if __name__ == "__main__":
    unittest.main()
