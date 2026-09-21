"""Run deterministic, data-free checks of core measurement instruments."""

import numpy as np

from luppi_recreation.connectivity_nulls import shuffle_reciprocal_sign_patterns
from luppi_recreation.dynamics import phase_dynamics


def main() -> None:
    time = np.arange(2000, dtype=float)
    carrier = 2 * np.pi * 0.03 * time
    offsets = np.linspace(0, 2 * np.pi, 100, endpoint=False)[:, None]
    modulation = (1 - np.cos(2 * np.pi * time / 500)) / 2
    signals = {
        "synchronized": np.repeat(np.cos(carrier)[None], 100, axis=0),
        "dispersed": np.cos(carrier + offsets),
        "switching": np.cos(carrier + offsets * modulation),
    }
    results = {name: phase_dynamics(values, trim=100) for name, values in signals.items()}
    for name, result in results.items():
        print(f"{name:14s} synchrony={result.synchrony:.6f} "
              f"metastability={result.metastability:.6f}")
    if not (results["synchronized"].synchrony > 0.999
            and results["dispersed"].synchrony < 1e-8
            and results["switching"].metastability > 0.20):
        raise RuntimeError("Synthetic phase instrument check failed")
    rng = np.random.default_rng(7)
    weights = rng.normal(size=(20, 20))
    np.fill_diagonal(weights, 0)
    shuffled = shuffle_reciprocal_sign_patterns(weights, rng)
    np.testing.assert_array_equal(np.abs(weights), np.abs(shuffled))
    if np.count_nonzero(weights < 0) != np.count_nonzero(shuffled < 0):
        raise RuntimeError("Sign-count preservation failed")
    print("PASS: phase instruments and magnitude-preserving signed null")


if __name__ == "__main__":
    main()
