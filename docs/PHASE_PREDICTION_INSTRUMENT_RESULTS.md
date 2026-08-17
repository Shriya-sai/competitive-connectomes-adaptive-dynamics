# Minimal Relative-Phase Prediction Instrument — Synthetic Results

## Decision

The instrument **passed its frozen development gate as a short-horizon measure**. Its longest valid prediction horizon is **300 ms**. It must not be interpreted as a validated 600–1,300 ms phase forecast.

## Frozen construct

Trial-level neural phase reconfiguration is the excess change in inter-regional relative-phase topology following an event, beyond the change predicted by continuing that trial's pre-event oscillator dynamics.

## Instrument

For each region, a linear phase trajectory was fitted to the unwrapped pre-event theta phase. Regional phases were extrapolated after the event, and time-resolved relative-topology prediction error was calculated as:

`E(t) = 1 - mean_{i<j} cos[(phase_i-phase_j)_observed - (phase_i-phase_j)_predicted]`.

## Frozen horizon gate

| Horizon | Null median | Null 95th percentile | Magnitude rho | Full-vs-zero Cohen's d | Split-seed reliability | Decision |
|---:|---:|---:|---:|---:|---:|---|
| 100 ms | 0.0489 | 0.0640 | 1.00 | 76.38 | 1.00 | Pass |
| 300 ms | 0.0779 | 0.0986 | 1.00 | 92.18 | 1.00 | Pass |
| 600 ms | 0.1071 | 0.1301 | 1.00 | 59.42 | 1.00 | Fail: null median |
| 900 ms | 0.1305 | 0.1657 | 1.00 | 60.31 | 1.00 | Fail: null median |
| 1,300 ms | 0.1882 | 0.2615 | 1.00 | 29.29 | 1.00 | Fail: null median and 95th percentile |

The unusually large standardized separations reflect deliberately clean ground-truth perturbations in the synthetic generator and should not be treated as expected empirical effect sizes.

## Key construct-validity findings

- **True zero with frequency heterogeneity:** with regional frequency SD 0.35 Hz and no imposed topology change, the old frozen metric reported mean reconfiguration 0.859. The new predictor reported 0.000145 at 1.3 seconds.
- **Known magnitude:** the new score ordered all five imposed change levels perfectly at every inspected horizon in the combined realistic condition.
- **Timing:** median perturbation-onset localization error was 29.7 ms, passing the frozen 100 ms limit.
- **Prediction horizon:** combined-condition zero error increased with elapsed time. This validates the concern that small phase-prediction errors accumulate and establishes 300 ms as the maximum defensible horizon.
- **Baseline length:** in the combined zero-change condition at a 300 ms horizon, median error fell from 0.215 with a 300 ms baseline to 0.149 with 600 ms, 0.095 with 1.0 s and 0.076 with 1.3 s. The intended 1.3-second baseline is therefore important.
- **Noise boundary:** strong smooth phase noise was the main one-factor limitation. At 300 ms, median zero error rose from 0.014 at 0.15 rad to 0.072 at 0.35 rad and 0.199 at 0.60 rad.
- **Frequency changes:** an unexpected post-event frequency shift raised prediction error even without an instantaneous offset perturbation. This is consistent with the construct because frequency change produces an unpredicted relative-topology trajectory, but the score does not identify the underlying mechanism.

## Benchmark

Riemannian covariance preserved perfect magnitude ordering in this synthetic suite. It remains a parallel broader-state benchmark. The phase predictor adds construct specificity: it directly tests departure from trial-specific relative-phase continuation and correctly rejects ordinary fixed frequency heterogeneity.

## Methodological conclusion

The synthetic evidence supports a narrowly bounded instrument:

> Relative-phase prediction error during the first 300 ms after an event, using 1.3 seconds of pre-event theta phase to estimate each region's linear continuation.

No empirical stable-versus-updating result has yet been calculated with this new instrument. The proposed trial-level endpoint—mean `E(t)` from 50 through 300 ms—was separately tested before being frozen. Under the combined realistic synthetic condition it passed every prespecified criterion: null median `0.0625`, null 95th percentile `0.0789`, perturbation-magnitude Spearman `rho = 1.00`, split-seed ordering `rho = 1.00`, and full-change-versus-zero `Cohen's d = 96.22`. Timing specificity also passed: mean scores were `0.9602`, `0.3211`, `0.0010`, and `0.0001` for perturbations beginning at 0, 0.2, 0.5, and 0.8 seconds, respectively. Thus perturbations beginning outside the endpoint window did not create a false trial summary.

The empirical preprocessing, aggregation, controls, participant-level gate, and untouched technical-confirmation participants are now frozen in `docs/EEG_PHASE_PREDICTION_CONFIRMATION_PROTOCOL.md` and `configs/eeg_phase_prediction_confirmation.json`. The earlier failed gate remains unchanged.

## Artifacts

- Protocol: `docs/PHASE_PREDICTION_INSTRUMENT_PROTOCOL.md`
- Configuration: `configs/phase_prediction_instrument.json`
- Implementation: `scripts/validate_phase_prediction_instrument.py`
- Summary: `results/phase_prediction_instrument/validation_summary.json`
- Synthetic scores: `results/phase_prediction_instrument/synthetic_scores.csv`
- Timing results: `results/phase_prediction_instrument/timing_localization.csv`
- Figure: `figures/phase_prediction_instrument_validation.png`
