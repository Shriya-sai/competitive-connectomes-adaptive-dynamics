"""Fit cooperative-only and signed Hopf models to the released subject."""

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from luppi_recreation import (
    extract_regional_frequencies,
    load_hopf_extension,
    load_single_subject,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = PROJECT_ROOT / "upstream" / "competitive-cooperative-hopf"
DATA_DIRECTORY = UPSTREAM_ROOT / "data" / "matlab" / "single"
OUTPUT_DIRECTORY = PROJECT_ROOT / "results" / "single_subject_optimization"

CONFIG: dict[str, Any] = {
    "repetition_time": 0.72,
    "matlab_burnin": False,
    "learning_rate_fc": 0.001,
    "learning_rate_fc_lag": 0.0001,
    "max_connection": 0.15,
    "max_iterations": 2000,
    "convergence_threshold": 0.0005,
    "noise_strength": 0.001,
    "bifurcation_parameter": -0.02,
    "lag": 1,
    "l1_strength": 0.0001,
    "max_patience": 0,
}


def run_condition(
    hopf: Any,
    bold: np.ndarray,
    structural_connectivity: np.ndarray,
    frequencies: np.ndarray,
    condition: str,
) -> dict[str, Any]:
    cooperative_only = condition == "cooperative_only"
    result = hopf.optimize(
        bold,
        structural_connectivity,
        frequencies,
        CONFIG["repetition_time"],
        int(cooperative_only),
        int(CONFIG["matlab_burnin"]),
        CONFIG["learning_rate_fc"],
        CONFIG["learning_rate_fc_lag"],
        CONFIG["max_connection"],
        CONFIG["max_iterations"],
        CONFIG["convergence_threshold"],
        CONFIG["noise_strength"],
        CONFIG["bifurcation_parameter"],
        CONFIG["lag"],
        CONFIG["l1_strength"],
        CONFIG["max_patience"],
    )

    generative_connectivity = np.asarray(result[0], dtype=np.float64)
    fc_correlation = float(result[1])
    simulated_fc = np.asarray(result[2], dtype=np.float64)
    runtime_seconds = float(result[3])
    converged = bool(result[4])

    if not np.isfinite(generative_connectivity).all():
        raise ValueError(f"{condition} GEC contains non-finite values")
    if not np.isfinite(simulated_fc).all():
        raise ValueError(f"{condition} simulated FC contains non-finite values")

    negative_edges = int(np.count_nonzero(generative_connectivity < 0))
    nonzero_edges = int(np.count_nonzero(generative_connectivity))
    negative_fraction = negative_edges / nonzero_edges if nonzero_edges else 0.0

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUTPUT_DIRECTORY / f"{condition}.npz",
        generative_connectivity=generative_connectivity,
        simulated_fc=simulated_fc,
        regional_frequencies=frequencies,
    )

    return {
        "condition": condition,
        "cooperative_only": cooperative_only,
        "fc_correlation": fc_correlation,
        "runtime_seconds": runtime_seconds,
        "converged": converged,
        "negative_edges": negative_edges,
        "nonzero_edges": nonzero_edges,
        "negative_fraction": negative_fraction,
        "gec_minimum": float(generative_connectivity.min()),
        "gec_maximum": float(generative_connectivity.max()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--condition",
        choices=("both", "cooperative_only", "signed"),
        default="both",
    )
    args = parser.parse_args()

    data = load_single_subject(DATA_DIRECTORY)
    frequencies = extract_regional_frequencies(
        data.bold,
        repetition_time=CONFIG["repetition_time"],
    )
    hopf = load_hopf_extension(UPSTREAM_ROOT)

    conditions = (
        ["cooperative_only", "signed"]
        if args.condition == "both"
        else [args.condition]
    )
    summaries = []
    for condition in conditions:
        print(f"\n=== Running condition: {condition} ===", flush=True)
        summary = run_condition(
            hopf,
            data.bold,
            data.structural_connectivity,
            frequencies,
            condition,
        )
        summaries.append(summary)
        print(json.dumps(summary, indent=2), flush=True)

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    summary_path = OUTPUT_DIRECTORY / "summary.json"
    summary_path.write_text(
        json.dumps({"config": CONFIG, "results": summaries}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nSummary saved to: {summary_path}")


if __name__ == "__main__":
    main()
