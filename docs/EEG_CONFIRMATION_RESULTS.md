# Frozen EEG Switching Confirmation Results

## Status

The frozen three-participant confirmation gate was run on OpenNeuro ds004295 participants `sub-s2`, `sub-s3`, and `sub-s4`. The overall confirmation gate **did not pass**. This is a technical and directional gate, not a significance test.

## Frozen primary question

On negative-feedback reward trials, is theta phase-pattern reconfiguration greater during the first 10 trials after a reversal than during the 10 stable trials before it?

The analysis required at least five clean negative-feedback trials in each participant-level period and a positive early-minus-stable direction in at least two of three confirmation participants.

## Integrity and controls

- All six `.set`/`.fdt` files passed remote-size integrity checks; single-part ETags also passed MD5 checks.
- Artifact rejection imbalance remained below 20 percentage points for all three participants.
- The reward frontal-midline theta positive control passed in two of three participants.
  - `sub-s2`: -0.200 dB, failed direction
  - `sub-s3`: +0.489 dB, passed direction
  - `sub-s4`: +0.986 dB, passed direction
- Current-source-density computation used a least-squares sphere fitted only to the 64 finite scalp-electrode coordinates. EOG channels were excluded from CSD because their coordinates were undefined.

## Primary endpoint

| Participant | Stable trials | Early trials | Stable | Early | Early - stable | Status |
|---|---:|---:|---:|---:|---:|---|
| `sub-s2` | 11 | 10 | 0.964811 | 0.961936 | -0.002875 | Sufficient; negative direction |
| `sub-s3` | 4 | 13 | — | — | — | Insufficient stable trials |
| `sub-s4` | 12 | 11 | 0.964106 | 0.970253 | +0.006147 | Sufficient; positive direction |

Only one of the two evaluable participants showed the predicted direction. Therefore the requirement of at least two positive participants was not met.

## Interpretation

This result does **not** establish that reversal learning increases the chosen EEG reconfiguration measure. It also does not establish the opposite: the confirmation sample was very small, one participant was unevaluable under the frozen trial rule, and the two evaluable effects had opposite signs.

The result is still useful. Data integrity, artifact balance, CSD processing, and the theta positive control were mostly successful, while the primary endpoint showed two weaknesses that should be investigated openly in a new exploratory phase:

1. Negative-feedback-only windows can leave very few trials around individual reversals.
2. Reconfiguration values clustered near 1.0, suggesting that the current instantaneous phase-pattern distance may have a ceiling or scaling problem and may be insufficiently sensitive to the behavioral contrast.

Neither issue should be repaired by changing the frozen gate after seeing the result. Any alternative estimator, window, feedback-matching scheme, or trial-pooling rule must be labeled exploratory and validated on synthetic data before a new held-out confirmation.

## Next exploratory steps

1. Diagnose the near-ceiling behavior of the phase-pattern metric using known synthetic states and time-shift/surrogate nulls.
2. Compare bounded/circular alternatives, including time-resolved phase-locking-vector similarity and LEiDA state-distribution distances.
3. Quantify reliability by reversal episode and by trial count.
4. Freeze the best validated estimator before testing additional untouched participants from ds004295.
5. Only after an EEG measure survives that process should it be related to Hopf-model cooperation/competition parameters.

## Exploratory instrument audit (post-confirmation)

The exact frozen phase-reconfiguration equation was subsequently tested on 64-channel synthetic theta signals with five known reconfiguration levels. This audit was performed after—and does not alter—the failed frozen confirmation.

- Under ideal equal-frequency theta signals, the metric recovered the known ordering perfectly. Its null was approximately zero and its dynamic range was 0.996.
- Phase noise alone and volume mixing alone did not destroy the ordering in the tested conditions.
- Modest regional frequency heterogeneity (SD 0.35 Hz around 6 Hz) raised the nominal zero-change condition to 0.950 and compressed the dynamic range to 0.051.
- The combined realistic condition raised the zero-change condition to 0.959 and compressed the dynamic range to 0.038.

These synthetic near-ceiling values closely match the empirical values around 0.96–0.97. The current estimator compares a short baseline phase pattern with instantaneous phase differences across a long response interval. When regional theta frequencies differ, ordinary phase drift is therefore counted as reconfiguration even without an imposed change in the underlying offset pattern.

This identifies a measurement-construct problem: the estimator is mathematically valid as total instantaneous phase departure, but it is not sufficiently specific or sensitive for the intended question about reversal-related network reorganization. The failed empirical gate remains a valid failure of that prespecified test; it should not be interpreted as a clean rejection of the biological hypothesis.

Audit artifacts:

- `scripts/audit_eeg_reconfiguration_instrument.py`
- `results/eeg_reconfiguration_instrument_audit/audit_summary.json`
- `results/eeg_reconfiguration_instrument_audit/trial_metrics.csv`
- `figures/eeg_reconfiguration_instrument_audit.png`

## Reproducible artifacts

- Frozen protocol: `docs/EEG_SWITCHING_ANALYSIS_PROTOCOL.md`
- Configuration: `configs/eeg_switching_analysis.json`
- Analysis script: `scripts/run_eeg_switching_confirmation.py`
- Machine-readable gate: `results/reversal_eeg_confirmation/gate_summary.json`
- Episode table: `results/reversal_eeg_confirmation/episode_metrics.csv`
- Figure: `figures/reversal_eeg_confirmation.png`
