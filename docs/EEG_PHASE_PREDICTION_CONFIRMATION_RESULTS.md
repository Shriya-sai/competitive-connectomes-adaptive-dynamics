# EEG Phase-Prediction Technical Confirmation — Results

## Status

Completed under frozen protocol version 1.0.0 using previously untouched participants `sub-s6`, `sub-s8`, and `sub-s10`. The protocol hashes passed before any new EEG outcome was calculated. No estimator, window, participant, threshold, preprocessing choice, or decision rule was changed after outcome inspection.

## Frozen question

On negative-feedback reward trials, is excess theta relative-phase reconfiguration larger during the first ten trials after reversal than at feedback-matched stable pseudo-events 11–30 trials before reversal?

The primary trial score was mean prediction-residual relative-phase topology error from 50–300 ms after feedback. Participant estimates used 1,000 deterministic trial-balanced resamples.

## Primary results

| Participant | Stable trials | Early trials | Stable score | Early score | Early − stable | Direction |
|---|---:|---:|---:|---:|---:|---|
| `sub-s6` | 27 | 10 | 0.99408 | 0.98995 | -0.00413 | Negative |
| `sub-s8` | 18 | 11 | 0.98743 | 1.00122 | +0.01379 | Positive |
| `sub-s10` | 13 | 13 | 0.99277 | 0.99722 | +0.00446 | Positive |

The prespecified directional component was met: two of three participants had positive early-minus-stable contrasts. All three participants exceeded the minimum of five clean trials per period.

## Frozen controls and formal gate

| Requirement | Result | Decision |
|---|---:|---|
| Download integrity | 6/6 files size-verified | Pass |
| Sufficient primary cells | 3/3 participants | Pass |
| Positive primary direction | 2/3 participants | Pass |
| Reward-theta positive control | 3/3 participants | Pass |
| Retention imbalance no greater than 20 percentage points | 2/3 participants | **Fail** |

The retention-rate imbalance was 20.43 percentage points for `sub-s6`, 17.11 for `sub-s8`, and 5.42 for `sub-s10`. The `sub-s6` value exceeds the frozen ceiling by 0.43 percentage points. It is not rounded down and the ceiling is not revised.

**Formal protocol decision: the primary technical-confirmation gate failed.**

## Crucial construct-validity observation

The stable pseudo-event scores were already approximately 0.99 for all participants. Under this metric, a value near 1 indicates that observed relative-phase residuals are approximately dispersed rather than predictably aligned. Therefore the empirical baseline continuation model did not produce the low stable-control error expected of a useful excess-reconfiguration instrument.

This observation is more consequential than merely counting two positive contrasts. The differences are tiny relative to the approximately unit-valued stable error, and the predictor cannot cleanly distinguish reversal-related departure from its failure to forecast ordinary empirical theta-phase evolution. The synthetic validation established performance for the simulated confounds it contained, but those simulations did not adequately reproduce the nonstationarity or complexity of empirical scalp theta.

This is a diagnostic interpretation, not a new post-hoc gate. The formal gate already failed because of the frozen retention-balance rule.

## Prespecified Riemannian secondary endpoint

| Participant | Stable | Early | Early − stable |
|---|---:|---:|---:|
| `sub-s6` | 1.93049 | 1.82426 | -0.10623 |
| `sub-s8` | 1.63679 | 1.60059 | -0.03620 |
| `sub-s10` | 1.62294 | 1.58862 | -0.03433 |

All three Riemannian contrasts were negative. Thus the broader multivariate neural-state endpoint also did not support greater early post-reversal reorganization in this frozen sample. It cannot rescue or redefine the failed primary endpoint.

## Scientific conclusion

This test does **not** provide confirmatory empirical support for the claim that early reversal updating produces greater theta phase-topology reconfiguration than matched stable negative-feedback events. It also does not establish that the biological hypothesis is false. The primary instrument failed to provide a credible low-error empirical control, and the small technical sample is not a population-level test.

The appropriate stopping rule is now active: do not search additional phase metrics on these participants and do not retrofit the predictor. Model-based residual phase dynamics may only be pursued under a new versioned development protocol, with new synthetic conditions and another untouched empirical set. A broader covariance-based claim would likewise require a new prospectively frozen study rather than reinterpretation of the present negative secondary result.

## Outputs

- Configuration: `configs/eeg_phase_prediction_confirmation.json`
- Protocol lock: `results/eeg_phase_prediction_confirmation/protocol_lock.json`
- Integrity record: `results/eeg_phase_prediction_confirmation/download_integrity.json`
- Participant summaries: `results/eeg_phase_prediction_confirmation/sub-s*_summary.json`
- Trial scores: `results/eeg_phase_prediction_confirmation/trial_metrics.csv`
- Gate result: `results/eeg_phase_prediction_confirmation/gate_summary.json`
- Figure: `figures/eeg_phase_prediction_confirmation.png`
