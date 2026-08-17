"""Estimate and summarize frequencies for the released single subject."""

from pathlib import Path

import numpy as np

from luppi_recreation import extract_regional_frequencies, load_single_subject


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = (
    PROJECT_ROOT
    / "upstream"
    / "competitive-cooperative-hopf"
    / "data"
    / "matlab"
    / "single"
)
OUTPUT_PATH = PROJECT_ROOT / "results" / "single_subject_frequencies.npy"


def main() -> None:
    data = load_single_subject(DATA_DIRECTORY)
    frequencies = extract_regional_frequencies(
        data.bold,
        repetition_time=0.72,
        filter_low=0.008,
        filter_high=0.09,
        smoothing_sigma=0.01,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUTPUT_PATH, frequencies)

    print(f"Frequencies calculated: {frequencies.size}")
    print(f"Minimum frequency: {frequencies.min():.6f} Hz")
    print(f"Median frequency: {np.median(frequencies):.6f} Hz")
    print(f"Maximum frequency: {frequencies.max():.6f} Hz")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
