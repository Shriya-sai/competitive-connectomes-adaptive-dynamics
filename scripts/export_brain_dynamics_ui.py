"""Export frozen Hopf perturbation results for the static interactive UI."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/hopf_perturbation_response.json"
MODEL = ROOT / "results/single_subject_optimization/signed.npz"
RUNS = ROOT / "results/hopf_perturbation_response/confirmation/confirmation_pairs.csv"
PROFILES = ROOT / "results/hopf_perturbation_response/confirmation/regional_response_profiles.npz"
OUTPUT = ROOT / "ui/data/brain-dynamics-demo.json"

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


def main() -> None:
    config = json.loads(CONFIG.read_text())
    connectivity = np.load(MODEL)["generative_connectivity"]
    rows = list(csv.DictReader(RUNS.open()))
    profiles = np.load(PROFILES)["profiles"]
    payload = build_payload(connectivity, rows, profiles, config)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    print(
        f"Wrote {len(payload['nodes'])} regions, {len(payload['edges'])} edges, "
        f"and {len(payload['responses'])} response profiles to {OUTPUT}"
    )


if __name__ == "__main__":
    main()
