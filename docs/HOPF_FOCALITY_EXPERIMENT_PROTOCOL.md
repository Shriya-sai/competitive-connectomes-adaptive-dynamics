# Hopf Perturbation Focality Experiment — Frozen Stage 2 Protocol

## Question

**How do perturbation focality and cooperative–competitive regime jointly determine local response, outward propagation, relational phase reconfiguration, spatial reach, and recovery?**

This protocol is frozen before focality simulations. It tests 1, 5, 10, and 20 targeted regions using nested central and peripheral A/B families.

## Nested targets

Each target family is an ordered twenty-region list obtained mechanically from the frozen signed connectome. The first `N` entries define focality `N`. The ten-region member exactly reproduces the corresponding target used previously. Consequently, changing focality adds regions without replacing earlier ones.

Central A/B are alternating entries among the forty highest absolute-strength regions. Peripheral A/B are alternating entries among the forty lowest. Centrality is connectivity-defined and must not be described as a named biological network.

## Two dose questions

The strong sustained parent pulse is retained: duration 28.8 seconds and base absolute magnitude 0.03.

1. **Constant per-region:** every targeted region receives `|delta_a| = 0.03`. Total intervention grows with focality.
2. **Constant total:** every targeted region receives `|delta_a| = 0.03/N`. Total absolute intervention remains 0.03.

Positive and negative pulses are separate. These designs distinguish recruiting more regions from redistributing a fixed intervention budget.

## Measurements

Measurements remain uncombined: targeted RMS, outside RMS, total response energy, per-target and per-untargeted response, amplitude-qualified phase within targets/across the boundary/within untargeted regions, recovery, residual displacement, and spatial reach. Phase values are means per edge-time, never sums, so focality does not win mechanically by creating more edges.

Spatial reach is the fraction of untargeted regions whose pulse RMS exceeds 5% of the median targeted-region RMS in that pair.

A conservative descriptive system-level label requires both: within-untargeted phase at least 25% of the larger local/boundary phase, and spatial reach of at least 25%. This threshold is not proof of a whole-brain transition; the continuous components remain primary.

## Development and confirmation

Seeds 400–404 are used only for a 640-pair development gate. Seeds 500–529 are untouched confirmation seeds for 11,520 pairs. Confirmation is released only if paired pre-pulse identity, nested sets, both dose calculations, finite outputs, and zero uncoupled propagation all pass.

## Analysis

Dose schemes and signs remain separate. Focality trends are evaluated within gain × family × sign × seed cells. Log–log slopes describe total response scaling as sublinear (`<0.8`), approximately linear (`0.8–1.2`), or superlinear (`>1.2`). These are descriptive conventions fixed before outcomes.

No composite flexibility score or overall winner is permitted.
