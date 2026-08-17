# Hopf Phase-Reconfiguration Diagnostic — Results

## Decision

The unusual phase panel reflects a **genuine but spatially localized partial dissociation**, with a meaningful amplitude-estimation qualification. It is not primarily explained by unreliable low-amplitude Hilbert phase or by common-mode cancellation.

This is an exploratory measurement audit of the completed perturbation experiment. It does not revise or upgrade the parent confirmation claim.

## Design

The audit reran 5,760 pairs across all sites, pulse signs, durations, and thirty confirmation seeds for six prespecified gain conditions. Phase was measured over the exact pulse, an equally long early-recovery window, and late recovery. Raw and amplitude-qualified estimates were calculated for within-perturbed, within-unperturbed, cross-boundary, and all-edge relationships.

## Amplitude qualification

Amplitude qualification reduced the numerical phase distances substantially. For example, pulse all-edge medians changed from:

| Condition | Raw | Qualified |
|---|---:|---:|
| Uncoupled | 0.000440 | 0.000217 |
| Cooperative-only | 0.000293 | 0.0000668 |
| Competitive-only | 0.000115 | 0.0000848 |
| Fitted signed | 0.000391 | 0.0000923 |
| Competition-dominant | 0.0000945 | 0.0000771 |
| Cooperation-dominant | 0.000331 | 0.0000609 |

However, raw and qualified trial scores retained strong rank agreement (`Spearman rho = 0.857`). Qualified phase was essentially unrelated to invalid edge-time fraction (`rho = -0.092`). Therefore low-amplitude phase estimates inflated absolute values but did not generate the main ordering by themselves.

## Common mode and direct response

Qualified phase was only weakly related to common-mode fraction (`rho = -0.119`) and moderately related to direct-response magnitude (`rho = 0.392`). Large signal displacement therefore does not imply proportionally large relative-phase reorganization, and shared regional motion does not sufficiently explain the phase pattern.

This supports a real distinction between:

- how far regional signals move;
- how far the response spreads in amplitude; and
- how their timing relationships reorganize.

## Spatial localization

Phase change was concentrated within directly perturbed regions and across the perturbed/unperturbed boundary. Within-unperturbed phase change was much smaller in every condition.

For qualified pulse phase:

- Uncoupled: within-perturbed `0.001269`, cross-boundary `0.001144`, within-unperturbed `0`.
- Cooperative-only: `0.000299`, `0.000234`, `0.0000217`.
- Competitive-only: `0.000448`, `0.000384`, `0.00000525`.
- Fitted signed: `0.000401`, `0.000330`, `0.0000336`.
- Cooperation-dominant: `0.000248`, `0.000197`, `0.0000266`.
- Competition-dominant: cross-boundary `0.000188` slightly exceeded within-perturbed `0.000175`; within-unperturbed remained only `0.0000290`.

The uncoupled model can display cross-boundary phase distance without propagation because the perturbed oscillators change relative to untouched oscillators even though no causal influence reaches them. Thus cross-boundary phase difference must not automatically be called network transmission. Nonzero phase change among unperturbed regions is the stricter signature of propagated relational reorganization, and that component was consistently small.

## Temporal result

Phase effects often increased during matched early recovery, particularly for uncoupled and competitive-only networks, while late-recovery phase largely collapsed in cooperative regimes. Competitive-only and competition-dominant regimes retained larger late-recovery phase effects, consistent with their slower or censored recovery in the parent experiment.

## Revised interpretation

The parent phase panel should remain secondary, but it need not be discarded. Its defensible interpretation is:

> Perturbations reorganize relative-phase relationships primarily within stimulated regions and at their boundary with the rest of the network. This relational change is partially independent of response magnitude and propagation. Cooperation–competition balance affects its timing and persistence, but phase reconfiguration inside untouched regions is comparatively weak.

The original all-edge metric diluted this localization by averaging thousands of largely unchanged unperturbed–unperturbed edges together with the affected edge classes. This explains why its gain map looked different and numerically small.

## Limitations

- The audit is exploratory and reuses the same confirmation seeds.
- Amplitude qualification uses one prespecified percentile; it was not optimized, but it remains a methodological choice.
- Cross-boundary phase distance does not itself establish causal propagation.
- These findings remain properties of one fitted connectome and intervention mechanism.

## Outputs

- Pair-level audit: `results/hopf_phase_diagnostic/diagnostic_pairs.csv`
- Analysis summary: `results/hopf_phase_diagnostic/analysis_summary.json`
- Condition summary: `results/hopf_phase_diagnostic/condition_summary.csv`
- Figure: `figures/hopf_phase_diagnostic.png`
