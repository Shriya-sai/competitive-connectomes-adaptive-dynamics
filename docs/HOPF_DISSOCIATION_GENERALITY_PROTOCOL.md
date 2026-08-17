# Generality of the Hopf Response–Phase Dissociation — Frozen Stage 1 Analysis

## Status

Frozen before inspecting subgroup results. This is a factorial analysis of the existing 5,760 diagnostic pairs; no new simulation is required. It remains exploratory and cannot modify the completed parent confirmation.

## Question

**How general is the dissociation between signal displacement, amplitude propagation, and relative-phase reconfiguration across perturbation sign, strength, duration, connectivity-defined target centrality, matched A/B target set, and gain regime?**

Focality remains fixed at ten regions and is explicitly outside Stage 1.

## Measurements

- Displacement: direct-region RMS intervention-minus-control response during the pulse.
- Propagation: outside-region RMS response during the pulse.
- Phase: amplitude-qualified all-edge phase distance during the same pulse.
- Localization: qualified phase within perturbed regions, across the boundary, and within unperturbed regions.

All measurements use the exact same pulse interval.

## Why correlations, not ratios

The dissociation is quantified using Spearman association between phase and displacement and between phase and propagation within every prespecified factor level. Phase-to-propagation ratios are prohibited because propagation can be exactly or nearly zero, making the ratio unstable and scientifically misleading.

Dissociation does not require zero correlation. It means phase is not almost reducible to response magnitude. Absolute `rho >= 0.8` is prespecified as strong coupling.

## Generality rule

For every level of sign, absolute strength, duration, centrality, and A/B target:

1. absolute phase–displacement `rho` must remain below 0.8;
2. absolute phase–propagation `rho` must remain below 0.8; and
3. `max(within-perturbed phase, cross-boundary phase)` must exceed within-unperturbed phase in at least 95% of individual pairs.

If every level passes, the dissociation is labelled general across the already sampled perturbation families. If only some pass, it is conditional. This rule says nothing about unsampled focalities, named functional networks, other connectomes, or alternative perturbation mechanisms.

Gain-regime strata will be reported to reveal mechanism-specific exceptions, but they do not control the generality label across perturbation families.

## Factor summaries

All levels will be reported for positive/negative sign, weak/strong magnitude, brief/sustained duration, central/peripheral targeting, A/B matched sets, and all six gain regimes. Medians and paired seed-matched differences are descriptive. No subgroup may be selected using significance or preferred direction, and no composite score is permitted.
