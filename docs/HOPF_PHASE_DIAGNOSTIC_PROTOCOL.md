# Hopf Phase-Reconfiguration Diagnostic — Frozen Exploratory Audit

## Purpose and status

This audit was frozen before rerunning time-resolved trajectories for the diagnostic. It investigates why the completed phase-reconfiguration panel differed from signal displacement and propagation. It is exploratory and cannot revise the parent confirmation result.

Six prespecified reference conditions are retained: uncoupled `(0,0)`, cooperative-only `(1,0)`, competitive-only `(0,1)`, fitted signed `(1,1)`, competition-dominant `(1,1.5)`, and cooperation-dominant `(1.5,1)`. Every parent-protocol site, signed amplitude, duration, and confirmation seed is included. No favorable subset may be selected.

## Questions

1. Does the gain pattern differ between the pulse and an equally long early-recovery window?
2. Does it occur within perturbed regions, within unperturbed regions, or across their boundary?
3. Does it survive exclusion of edge-times at which analytic phase is poorly supported by control-signal amplitude?
4. Does a common-mode signal response explain why large displacement produces little relative-phase change?

## Frozen signal processing

Control and intervention trajectories are filtered from 0.01–0.1 Hz with a second-order zero-phase Butterworth filter applied to the complete recorded trajectory before windowing. Analytic amplitude and phase are obtained by Hilbert transform.

The four spatial edge classes are: within perturbed regions, within unperturbed regions, cross-boundary, and all edges.

## Amplitude qualification

For each channel, the validity threshold is its 20th percentile control analytic amplitude during the 72-second pre-pulse baseline. An edge-time is valid only when both constituent channels exceed their own thresholds in the control trajectory. Intervention amplitude is never used to define validity. A cell must retain at least 25% of its edge-times; otherwise it is reported as insufficient rather than assigned a favorable value.

Qualified phase distance is:

`1 - mean cos[(phi_i - phi_j)_intervention - (phi_i - phi_j)_control]`

over valid edge-times within the prespecified spatial class and window.

## Matched windows and common mode

Phase distance, direct response, and outside-region propagation are calculated over the exact pulse interval and over an immediately following recovery interval of identical duration. Late recovery is summarized over the final 28.8 seconds.

Common-mode fraction is the energy of the regional-mean intervention-minus-control signal divided by total regional response energy. It ranges from zero for a response whose regional mean cancels to one for a perfectly shared response.

## Diagnostic interpretation

- **Genuine dissociation:** the pulse-matched gain pattern survives amplitude qualification and is not explained by common-mode fraction alone.
- **Phase-estimation artefact:** the pattern substantially collapses after qualification and tracks the fraction of invalid edge-times.
- **Spatial localization:** the qualified effect survives predominantly within one prespecified edge class.
- **Mixed/inconclusive:** no single explanation is clearly supported.

No cutoff is permitted to be optimized after outcomes are seen. This audit may demote phase reconfiguration or refine its interpretation, but it cannot manufacture a new confirmation claim.
