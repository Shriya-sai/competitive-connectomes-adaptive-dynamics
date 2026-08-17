# Minimal Relative-Phase Prediction Instrument — Frozen Synthetic Protocol

## Status

Frozen before implementing or running the synthetic validation described below. This is post-confirmation instrument development and does not alter the failed EEG confirmation gate.

## Scientific construct

**Trial-level neural phase reconfiguration is the excess change in inter-regional relative-phase topology following an event, beyond the change predicted by continuing that trial's pre-event oscillator dynamics.**

## Minimal operationalization

For every channel, unwrap pre-event theta phase and fit a linear model

`phase_i(t) = intercept_i + angular_velocity_i * t`.

Extrapolate that model after the event. At every response time, calculate the circular discrepancy between every observed and predicted regional phase difference:

`E(t) = 1 - mean_{i<j} cos[(phase_i-phase_j)_observed - (phase_i-phase_j)_predicted]`.

The primary object is the complete time-resolved curve `E(t)`, not one trial average. A common absolute phase error shared by all channels cancels from the relative-phase topology.

No nonlinear dynamics, empirical tuning, channel selection, learned correction or model-family search is permitted in this first instrument.

## Synthetic factors

- Phase-topology perturbation magnitude: 0, 0.25, 0.50, 0.75, 1.00
- Perturbation onset: 0, 0.20, 0.50 and 0.80 seconds
- Regional frequency SD around 6 Hz: 0, 0.15, 0.35 and 0.60 Hz
- Post-event regional frequency change SD: 0, 0.10 and 0.30 Hz
- Smooth phase-noise SD: 0, 0.15, 0.35 and 0.60 radians
- Sensor/amplitude-noise SD: 0.01, 0.05, 0.10 and 0.25
- Zero-lag source mixing: 0, 0.20, 0.40 and 0.60
- Baseline duration: 0.30, 0.60, 1.00 and 1.30 seconds
- Oscillatory amplitude: 0.5, 1.0 and 2.0
- Prediction horizons inspected: 0.10, 0.30, 0.60, 0.90 and 1.30 seconds

Testing proceeds through clean one-factor tests, selected interactions and one combined realistic condition. It does not require the full Cartesian product.

## Crucial zero-reconfiguration condition

The zero condition contains heterogeneous oscillators undergoing uninterrupted ordinary evolution with no imposed topology change. The original frozen metric is expected to report near-ceiling reconfiguration; the new prediction-residual curve should remain low within its valid horizon.

## Frozen validity gate

A prediction horizon is valid only if all conditions hold across repeated synthetic realizations:

1. Zero-condition median `E(t) <= 0.10` and 95th percentile `<= 0.25`.
2. Known perturbation magnitude has Spearman ordering `rho >= 0.80`.
3. Full perturbation versus zero has standardized separation `Cohen's d >= 1.0`.
4. Split-seed test–retest ordering is `rho >= 0.80`.
5. Median perturbation-onset localization error is `<= 0.10 seconds` in clean timing tests.
6. In zero-change trials, elapsed time alone does not drive the mean curve above the null thresholds.

The instrument passes its development gate if at least one valid horizon reaches 0.30 seconds or longer under the combined realistic condition. The longest passing horizon becomes the candidate horizon; no longer horizon may be used merely because it produces a preferred empirical result.

## Benchmark and stopping rule

The old frozen metric and Riemannian covariance geometry are benchmarks, not ingredients in the predictor. If the simple phase predictor fails the frozen synthetic gate, phase-specific metric search stops for this dataset. The fallback construct becomes broader multivariate neural-state reorganization measured using covariance geometry.

Model-based residual phase dynamics remains reserved and is not implemented in this protocol.
