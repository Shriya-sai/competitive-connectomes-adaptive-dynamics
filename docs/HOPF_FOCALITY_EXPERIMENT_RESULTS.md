# Hopf Focality Experiment — Stage 2 Results

## Question

How do perturbation focality and cooperative/competitive gain jointly shape local response, propagation, phase reconfiguration, spatial reach, and recovery?

## Frozen design and quality control

- Focalities: 1, 5, 10, and 20 nested anatomical targets.
- Dose conventions: constant perturbation per region and constant total perturbation spread across targets.
- Six gain regimes, four anatomical target families, two signs, and 30 held-out confirmation seeds.
- Development: 640 paired simulations; all preregistered instrument gates passed.
- Confirmation: 11,520 paired simulations; all completed with finite trajectories.

## Main result

Focality has no context-free effect. Its apparent consequence reverses depending on what is held constant.

### Constant dose per targeted region

Adding targets also adds perturbation. Across gain regimes and anatomical families, increasing focality generally increased:

- propagation per untargeted region (median Spearman rho = 1.00),
- total response energy (rho = 1.00),
- cross-boundary phase displacement (rho = 0.80),
- phase displacement among untargeted regions (rho = 1.00), and
- residual displacement (rho = 1.00).

Total response energy scaled approximately as N^1.33 (median log-log slope). Thus the response increased superlinearly with the number of equally perturbed targets in the tested range.

### Constant total dose

Spreading the same total intervention across more targets weakened each target. Increasing focality generally decreased:

- response per targeted region (rho = -1.00),
- propagation per untargeted region (rho = -0.80),
- total response energy (rho = -1.00),
- cross-boundary phase displacement (rho = -1.00),
- phase displacement among untargeted regions (rho = -1.00), and
- residual displacement (rho = -0.80).

Total response energy scaled approximately as N^-0.65. A distributed intervention was therefore weaker than a focal intervention when total absolute dose was fixed.

## Interpretation

The scientifically meaningful contrast is not simply *focal versus distributed*. It is:

1. **Recruitment effect:** how response changes when more regions receive the same local perturbation.
2. **Dilution effect:** how response changes when a fixed intervention is divided among more regions.

Recruitment produced broader and stronger whole-network consequences. Dilution produced smaller amplitude and phase consequences. This distinction held across cooperative, competitive, fitted, and gain-dominant regimes, although the exact slopes varied by gain and anatomy.

The result also clarifies why perturbation focality cannot be interpreted without a dose convention. Saying “distributed perturbations propagate more” is true under constant per-region intensity here, but false under constant total dose.

## Measurement warning discovered in confirmation

The preregistered spatial-reach statistic counted untargeted regions exceeding 5% of the median targeted-region response. It increased with focality under both dose conventions (median rho = 1.00), even when absolute propagation decreased under constant total dose.

This is a denominator effect: distributing a fixed dose lowers targeted response, which lowers the reach threshold and makes it easier for small remote responses to qualify. Therefore:

- absolute propagation measures are the valid basis for the main conclusion;
- the relative spatial-reach statistic and the derived descriptive “system-level” label must not be treated as evidence of greater propagation;
- a future sensitivity analysis should add a threshold anchored to baseline variability or a fixed absolute reference, without replacing the frozen result.

The phase remote-fraction metric has a related ratio interpretation: it can rise while both local and remote phase effects shrink. Absolute cross-boundary and untargeted phase displacement must accompany it.

## Conclusion

Stage 2 supports a conditional principle: anatomical extent and cooperative/competitive gain shape the response landscape, but perturbation extent is inseparable from dose allocation. Broader recruitment amplifies network response when local strength is preserved; broader distribution attenuates it when total input is conserved.

This remains a mechanistic result from a fitted whole-brain model, not empirical evidence that biological stimulation will show identical scaling.
