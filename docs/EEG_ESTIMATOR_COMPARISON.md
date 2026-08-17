# Exploratory EEG Reconfiguration Estimator Comparison

## Purpose

Following the failed frozen EEG gate and identification of a phase-drift ceiling, four replacement estimators were compared on 64-channel synthetic theta signals with known reconfiguration levels. This work is exploratory and does not modify the frozen result.

Equal 1.3-second pre/post windows were used. Each observation was paired with a zero-change counterfactual generated with identical regional frequencies, phase noise, sensor noise and volume mixing. The reported score was observed distance minus this matched expected-drift distance.

## Candidates

1. Equal-window PLV-matrix distance
2. Equal-window wPLI-matrix distance
3. Projective LEiDA mean-projector distribution distance
4. Riemannian distance between shrinkage covariance matrices

## Findings

- **PLV matrix:** remained close to zero but was effectively blind to the imposed phase-offset topology change. Magnitude-only PLV measures coupling consistency rather than the phase arrangement of interest.
- **wPLI matrix:** showed modest monotonic sensitivity under ideal signals, phase noise and volume mixing, but failed under regional frequency heterogeneity and the combined realistic condition.
- **LEiDA distribution:** was highly sensitive under ideal, phase-noise and volume-mixing conditions, but frequency drift dominated the state-distribution distance. Matched scalar subtraction did not restore reliable ordering.
- **Riemannian covariance:** was the strongest overall candidate. It was perfectly monotonic under isolated frequency drift and achieved Spearman 0.90 under combined realistic confounds. However, its combined-condition dynamic range was small and the highest change level was not strictly ordered. It also measures broadband multivariate covariance organization rather than phase topology specifically.

## Decision

None of the four raw distances is ready to become the new primary endpoint. Riemannian covariance should remain a serious secondary/parallel candidate, while wPLI may serve as a conservative lagged-coupling endpoint. PLV magnitude should not be used to test phase-topology reconfiguration, and short-window LEiDA requires explicit drift correction before reuse.

The next primary development target is a trial-specific oscillator-evolution model:

1. Estimate each channel's ordinary phase trajectory from the pre-feedback interval.
2. Extrapolate the expected post-feedback phase configuration.
3. Measure the residual between observed and predicted post-feedback organization.
4. Validate prediction error on stable pseudo-events where no reversal-related change is expected.
5. Ask whether reversal trials show more residual reconfiguration than matched stable pseudo-events.

This directly implements the scientific question: **How much more does the observed phase configuration change than would be expected from ordinary oscillator evolution?**

## Artifacts

- `scripts/compare_eeg_reconfiguration_estimators.py`
- `results/eeg_reconfiguration_estimator_comparison/summary.json`
- `results/eeg_reconfiguration_estimator_comparison/trial_metrics.csv`
- `figures/eeg_reconfiguration_estimator_comparison.png`
