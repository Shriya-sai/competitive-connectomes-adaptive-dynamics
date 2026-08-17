"""Load the released single-subject data and print a concise inventory."""

from pathlib import Path

import numpy as np

from luppi_recreation import load_single_subject


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = (
    PROJECT_ROOT
    / "upstream"
    / "competitive-cooperative-hopf"
    / "data"
    / "matlab"
    / "single"
)


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    sc = data.structural_connectivity

    print(f"Regions: {data.n_regions}")
    print(f"BOLD timepoints: {data.n_timepoints}")
    print(f"SC shape: {sc.shape}")
    print(f"BOLD shape: {data.bold.shape}")
    print(f"SC density: {np.count_nonzero(sc) / sc.size:.3f}")
    print(f"SC symmetric: {np.allclose(sc, sc.T)}")
    print(f"SC diagonal is zero: {np.allclose(np.diag(sc), 0.0)}")


if __name__ == "__main__":
    main()
