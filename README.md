# Luppi et al. Recreation

Independent Python analysis pipeline built around the released C++ implementation from Luppi et al. (2026), with later experiments on competitive connectivity and adaptive exploration-exploitation.

## Project layout

- `upstream/` — unmodified upstream research code
- `src/luppi_recreation/` — reusable Python package
- `scripts/` — executable experiment and analysis scripts
- `configs/` — versioned experiment configurations
- `tests/` — automated correctness and regression tests
- `notebooks/` — exploratory analyses only
- `results/` — generated numerical outputs
- `figures/` — generated figures

## First milestone

Build the authors' C++ extension, load the released single-subject data in Python, and reproduce the cooperative-only versus cooperative-competitive functional-connectivity comparison.
