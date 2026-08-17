"""Run a forward Hopf simulation using the released single-subject SC."""

from pathlib import Path

import numpy as np

from luppi_recreation import (
    extract_regional_frequencies,
    load_hopf_extension,
    load_single_subject,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = PROJECT_ROOT / "upstream" / "competitive-cooperative-hopf"
DATA_DIRECTORY = UPSTREAM_ROOT / "data" / "matlab" / "single"
OUTPUT_PATH = PROJECT_ROOT / "results" / "single_subject_initial_sc_simulation.npy"

REPETITION_TIME = 0.72
NOISE_STRENGTH = 0.001
BIFURCATION_PARAMETER = -0.02
NOISE_TYPE = 1


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    frequencies = extract_regional_frequencies(
        data.bold,
        repetition_time=REPETITION_TIME,
    )

    # Match the upstream MATLAB initialization: SC = 0.2 * SC / max(SC).
    sc = data.structural_connectivity
    if np.max(sc) <= 0:
        raise ValueError("Structural connectivity has no positive weights")
    initial_connectivity = 0.2 * sc / np.max(sc)

    hopf = load_hopf_extension(UPSTREAM_ROOT)
    simulated_bold = np.asarray(
        hopf.simulate(
            initial_connectivity,
            frequencies,
            data.n_timepoints,
            REPETITION_TIME,
            NOISE_STRENGTH,
            BIFURCATION_PARAMETER,
            NOISE_TYPE,
        ),
        dtype=np.float64,
    )

    expected_shape = data.bold.shape
    if simulated_bold.shape != expected_shape:
        raise ValueError(
            f"Expected simulated BOLD shape {expected_shape}, "
            f"received {simulated_bold.shape}"
        )
    if not np.isfinite(simulated_bold).all():
        raise ValueError("Simulated BOLD contains non-finite values")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUTPUT_PATH, simulated_bold)

    print("Hopf forward simulation completed")
    print(f"Simulated BOLD shape: {simulated_bold.shape}")
    print(f"Minimum activity: {simulated_bold.min():.6f}")
    print(f"Maximum activity: {simulated_bold.max():.6f}")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
