"""Export frozen Hopf perturbation results for the static interactive UI."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from luppi_recreation import load_hopf_extension


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/hopf_perturbation_response.json"
MODEL = ROOT / "results/single_subject_optimization/signed.npz"
RUNS = ROOT / "results/hopf_perturbation_response/confirmation/confirmation_pairs.csv"
PROFILES = ROOT / "results/hopf_perturbation_response/confirmation/regional_response_profiles.npz"
OUTPUT = ROOT / "ui/data/brain-dynamics-demo.json"
TRAJECTORY_OUTPUT = ROOT / "ui/data/brain-dynamics-trajectories.json"
UPSTREAM = ROOT / "upstream/competitive-cooperative-hopf"
TRAJECTORY_SEED = 300

REFERENCE_CONDITIONS = {
    (0.0, 0.0): "uncoupled",
    (1.0, 0.0): "cooperative-only",
    (0.0, 1.0): "competitive-only",
    (1.0, 1.0): "fitted-signed",
}


def schematic_positions(regions: int) -> list[dict[str, float | int | str]]:
    """Create a deterministic bilateral layout; coordinates are not anatomical."""
    output = []
    per_side = regions // 2
    golden_angle = math.pi * (3 - math.sqrt(5))
    for index in range(regions):
        side_index = index % per_side
        hemisphere = "left" if index < per_side else "right"
        radius = math.sqrt((side_index + 0.5) / per_side)
        angle = side_index * golden_angle
        center_x = 0.29 if hemisphere == "left" else 0.71
        x = center_x + 0.22 * radius * math.cos(angle)
        y = 0.50 + 0.42 * radius * math.sin(angle)
        output.append(
            {
                "id": index,
                "label": f"Region {index + 1}",
                "hemisphere": hemisphere,
                "x": round(x, 6),
                "y": round(y, 6),
            }
        )
    return output


def strongest_edges(connectivity: np.ndarray, count: int = 500) -> list[dict[str, float | int]]:
    """Retain the strongest directed edge per unordered pair for legible playback."""
    candidates = []
    for first in range(connectivity.shape[0]):
        for second in range(first + 1, connectivity.shape[1]):
            forward = connectivity[first, second]
            reverse = connectivity[second, first]
            weight = forward if abs(forward) >= abs(reverse) else reverse
            if weight:
                candidates.append((abs(weight), first, second, float(weight)))
    candidates.sort(reverse=True)
    return [
        {
            "source": first,
            "target": second,
            "weight": round(weight, 7),
        }
        for _, first, second, weight in candidates[:count]
    ]


def build_payload(
    connectivity: np.ndarray,
    rows: list[dict[str, str]],
    profiles: np.ndarray,
    config: dict[str, object],
) -> dict[str, object]:
    if len(rows) != len(profiles):
        raise ValueError("run rows and regional profiles must align")
    grouped: dict[tuple[str, str, float, float], list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        gains = (float(row["cooperative_gain"]), float(row["competitive_gain"]))
        condition = REFERENCE_CONDITIONS.get(gains)
        if condition is None:
            continue
        key = (
            condition,
            row["site"],
            float(row["duration_seconds"]),
            float(row["delta_a"]),
        )
        grouped[key].append(index)

    response_profiles = []
    metric_names = (
        "direct_response",
        "propagation",
        "phase_reconfiguration",
        "recovery_time_seconds",
    )
    for key in sorted(grouped):
        indices = grouped[key]
        condition, site, duration, amplitude = key
        record = {
            "condition": condition,
            "site": site,
            "duration_seconds": duration,
            "amplitude": amplitude,
            "regional_response": np.round(np.median(profiles[indices], axis=0), 7).tolist(),
            "metrics": {
                metric: round(
                    float(np.median([float(rows[index][metric]) for index in indices])),
                    7,
                )
                for metric in metric_names
            },
        }
        response_profiles.append(record)

    sites = config["perturbations"]["resolved_zero_based_site_sets"]
    return {
        "schema_version": "1.0.0",
        "title": "Competitive Connectomes Perturbation Explorer",
        "provenance": {
            "model": "single-subject fitted signed Hopf connectivity",
            "confirmation_seeds": len(config["randomization"]["confirmation_seeds"]),
            "aggregation": "median across paired confirmation seeds",
            "layout": "deterministic bilateral schematic; not anatomical coordinates",
            "animation": "regional response-amplitude playback; not a simulated time series",
        },
        "nodes": schematic_positions(connectivity.shape[0]),
        "edges": strongest_edges(connectivity),
        "site_sets": sites,
        "responses": response_profiles,
    }


def sampled_indices(pre: int, pulse: int, recovery: int) -> np.ndarray:
    """Keep a short baseline and the full pulse, then sample recovery at 2.88 s."""
    baseline = np.append(np.arange(max(0, pre - 14), pre, 2), pre - 1)
    pulse_window = np.arange(pre, pre + pulse)
    recovery_window = np.arange(pre + pulse, pre + pulse + recovery, 4)
    return np.unique(np.concatenate((baseline, pulse_window, recovery_window)))


def quantize_trajectory(delta: np.ndarray) -> tuple[float, list[int]]:
    """Encode a trajectory as signed 16-bit units with a recorded scale."""
    scale = float(np.max(np.abs(delta)))
    if scale == 0:
        return 0.0, [0] * delta.size
    encoded = np.rint(delta / scale * 32767).astype(np.int16)
    return scale, encoded.T.reshape(-1).astype(int).tolist()


def build_trajectories(
    connectivity: np.ndarray,
    frequencies: np.ndarray,
    config: dict[str, object],
) -> dict[str, object]:
    """Run one untouched confirmation seed for literal intervention-control playback."""
    positive, negative = np.clip(connectivity, 0, None), np.clip(connectivity, None, 0)
    hopf = load_hopf_extension(UPSTREAM)
    tr = float(config["model"]["repetition_time_seconds"])
    pre = int(round(config["simulation_schedule"]["recorded_preperturbation_seconds"] / tr))
    recovery = int(round(config["simulation_schedule"]["recorded_recovery_seconds"] / tr))
    records = []
    sites = config["perturbations"]["resolved_zero_based_site_sets"]
    total = len(REFERENCE_CONDITIONS) * len(sites) * len(config["perturbations"]["duration_seconds"]) * len(config["perturbations"]["delta_a"])
    completed = 0
    for gains, condition in REFERENCE_CONDITIONS.items():
        signed_model = gains[0] * positive + gains[1] * negative
        for site, regions in sites.items():
            mask = np.zeros(connectivity.shape[0]); mask[regions] = 1.0
            for duration in config["perturbations"]["duration_seconds"]:
                pulse = int(round(duration / tr))
                indices = sampled_indices(pre, pulse, recovery)
                times = np.round((indices - pre) * tr, 3).tolist()
                for amplitude in config["perturbations"]["delta_a"]:
                    control, intervention = hopf.simulate_paired_perturbation(
                        signed_model, frequencies, mask, pre, pulse, recovery, tr,
                        config["model"]["noise_strength"],
                        config["model"]["baseline_bifurcation_parameter"],
                        amplitude,
                        config["simulation_schedule"]["discarded_burn_in_seconds"],
                        config["model"]["noise_type"], TRAJECTORY_SEED,
                    )
                    delta = np.asarray(intervention)[:, indices] - np.asarray(control)[:, indices]
                    scale, values = quantize_trajectory(delta)
                    records.append({"condition": condition, "site": site,
                        "duration_seconds": duration, "amplitude": amplitude,
                        "times_seconds": times, "scale": scale,
                        "values_int16_time_major": values})
                    completed += 1
                    if completed % 16 == 0:
                        print(f"generated {completed}/{total} literal trajectories", flush=True)
    return {"schema_version": "1.0.0", "seed": TRAJECTORY_SEED,
        "quantity": "intervention minus paired control BOLD signal",
        "sampling": "full pulse; recovery every four TRs; short pre-pulse identity context",
        "quantization": "int16 values multiplied by scale/32767",
        "regions": connectivity.shape[0], "trajectories": records}


def main() -> None:
    config = json.loads(CONFIG.read_text())
    model = np.load(MODEL)
    connectivity = model["generative_connectivity"]
    rows = list(csv.DictReader(RUNS.open()))
    profiles = np.load(PROFILES)["profiles"]
    payload = build_payload(connectivity, rows, profiles, config)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    trajectories = build_trajectories(connectivity, model["regional_frequencies"], config)
    TRAJECTORY_OUTPUT.write_text(json.dumps(trajectories, separators=(",", ":")) + "\n")
    print(
        f"Wrote {len(payload['nodes'])} regions, {len(payload['edges'])} edges, "
        f"and {len(payload['responses'])} response profiles to {OUTPUT}"
    )


if __name__ == "__main__":
    main()
