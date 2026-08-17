# Hopf Paired-Perturbation Instrument — Development Gate

## Decision

The frozen development gate passed using seeds 200–204. Confirmation seeds were not accessed during development.

| Check | Result | Decision |
|---|---:|---|
| Development intervention pairs | 640 | Complete |
| Zero-pulse maximum difference | 0.0 | Pass |
| Maximum pre-pulse paired difference | 0.0 | Pass |
| Finite trajectories | 640/640 | Pass |
| Absolute-magnitude monotonicity | 100% | Pass; required 80% |
| Genuine disjoint site-label test | Passed | Pass |

The instrument therefore isolates a causal pulse response exactly under matched state and noise, detects stronger perturbations monotonically, and handles perturbed-versus-outside region labels correctly.

## Descriptive sanity checks

Direct response ranged from `8.17e-06` to `0.0261`; propagation ranged from zero to `0.00193`; and phase reconfiguration ranged from `2.31e-06` to `0.0191`. All values were finite. Recovery was right-censored at 144 seconds in 328/640 pairs. This censoring is retained as information rather than changing the frozen recovery definition.

Passing this gate validates the paired perturbation instrument. It does not support any hypothesis about which cooperative–competitive gain condition will show which response profile.
