import numpy as np

from scripts.export_brain_dynamics_ui import build_payload, quantize_trajectory, sampled_indices, schematic_positions


def test_schematic_positions_are_deterministic_and_bounded() -> None:
    first = schematic_positions(100)
    second = schematic_positions(100)
    assert first == second
    assert len(first) == 100
    assert all(0 <= node["x"] <= 1 and 0 <= node["y"] <= 1 for node in first)


def test_ui_payload_aggregates_only_reference_conditions() -> None:
    connectivity = np.array([[0.0, 0.5], [-0.4, 0.0]])
    rows = [
        {
            "cooperative_gain": "1.0",
            "competitive_gain": "1.0",
            "site": "central_A",
            "duration_seconds": "7.2",
            "delta_a": "0.03",
            "direct_response": "1.0",
            "propagation": "2.0",
            "phase_reconfiguration": "3.0",
            "recovery_time_seconds": "4.0",
        },
        {
            "cooperative_gain": "0.5",
            "competitive_gain": "0.5",
            "site": "central_A",
            "duration_seconds": "7.2",
            "delta_a": "0.03",
            "direct_response": "9.0",
            "propagation": "9.0",
            "phase_reconfiguration": "9.0",
            "recovery_time_seconds": "9.0",
        },
    ]
    config = {
        "perturbations": {"resolved_zero_based_site_sets": {"central_A": [0]}},
        "randomization": {"confirmation_seeds": [1]},
    }
    payload = build_payload(connectivity, rows, np.array([[1.0, 2.0], [9.0, 9.0]]), config)
    assert len(payload["responses"]) == 1
    assert payload["responses"][0]["condition"] == "fitted-signed"
    assert payload["responses"][0]["regional_response"] == [1.0, 2.0]


def test_literal_trajectory_sampling_preserves_pulse_boundaries() -> None:
    indices = sampled_indices(pre=100, pulse=10, recovery=200)
    assert 99 in indices
    assert list(indices[(indices >= 100) & (indices < 110)]) == list(range(100, 110))
    assert 110 in indices
    assert indices[-1] < 310


def test_trajectory_quantization_has_bounded_error() -> None:
    trajectory = np.array([[0.0, -0.2, 0.5], [0.1, -0.5, 0.3]])
    scale, values = quantize_trajectory(trajectory)
    restored = np.asarray(values).reshape(trajectory.shape[1], trajectory.shape[0]).T * scale / 32767
    assert scale == 0.5
    assert np.max(np.abs(restored - trajectory)) <= scale / 32767
