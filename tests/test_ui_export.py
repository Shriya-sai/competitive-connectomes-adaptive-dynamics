import numpy as np

from scripts.export_brain_dynamics_ui import build_payload, schematic_positions


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
