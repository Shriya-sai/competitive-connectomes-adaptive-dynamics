# EEG Phase-Prediction Technical Confirmation — Frozen Protocol

## Status and purpose

This protocol was frozen before computing any result from the new technical-confirmation participants. The earlier analyses of `sub-s1` through `sub-s4` were used for development or diagnosis and are ineligible for this test. The untouched set is `sub-s6`, `sub-s8`, and `sub-s10`. Participants `sub-s5`, `sub-s7`, and `sub-s9` remain excluded according to the released metadata.

This is a deliberately small technical confirmation. It asks whether the newly validated instrument produces the predicted direction in new empirical data. It is not powered to establish a population effect and cannot identify anatomical cooperative or competitive couplings from scalp EEG.

## Frozen construct

**Trial-level neural phase reconfiguration is the excess change in inter-regional relative-phase topology following an event, beyond the change predicted by continuing that trial's pre-event oscillator dynamics.**

For each scalp channel, a straight line is fitted to unwrapped theta phase during the 1.3 seconds immediately before feedback. That oscillator-specific phase trajectory is extrapolated after feedback. At each time point:

`E(t) = 1 - mean_(i<j) cos{[(phi_i-phi_j)_observed - (phi_i-phi_j)_predicted]}`.

The frozen trial endpoint is the arithmetic mean of `E(t)` from 50 through 300 ms after feedback. The first 50 ms are excluded to reduce event-boundary/filter contamination. The endpoint stops at 300 ms because synthetic validation showed that prediction remains trustworthy through 300 ms but not at 600 ms or longer.

## Frozen empirical question

On negative-feedback reward trials, is excess theta relative-phase reconfiguration larger in the first ten trials following a reversal than at feedback-matched stable pseudo-events well before reversal?

- Early updating: trials 0 through 9 relative to each reversal.
- Stable comparison: trials -30 through -11 relative to each reversal.
- Event: the actual feedback onset in both periods.
- Feedback: negative reward feedback only.

Using real feedback events in the stable period supplies the crucial empirical control: ordinary post-feedback oscillator evolution, sensory input, and negative-feedback processing occur without the immediate reversal-update context.

## Preprocessing lock

The existing frozen pipeline is retained: resample to 512 Hz; average reference; 50-Hz notch; fit extended-infomax ICA on a 1–100 Hz copy with seed 42, decimation 4, and 99% explained variance; identify at most two blink components using Fp1/Fp2 at threshold 3.0; apply ICA to 0.1–100 Hz data; apply the released bad-trial indices; and transform the 64 finite scalp electrodes to current-source density while excluding EOG channels from CSD. Theta is 4–8 Hz.

A trial must contain the complete -1.3-to-0-second prediction baseline and 0.05-to-0.30-second response window and survive the fixed exclusions. Each participant must retain at least five negative-feedback trials in both periods.

## Frozen aggregation

Reversal episodes are pooled within participant and period. Because stable and early periods can retain different trial counts, the larger cell is subsampled without replacement to the smaller cell's size in 1,000 deterministic balanced resamples using seed 42. The participant endpoint is the mean early-minus-stable contrast across these resamples. Participants receive equal weight.

This balancing is not permission to select a favorable resample: all 1,000 fixed-seed resamples contribute to the participant estimate.

## Decision gate

The directional technical gate passes only if:

1. at least two of the three frozen participants retain the minimum trial count in both cells;
2. at least two of three participants have a positive early-minus-stable phase-prediction contrast;
3. the reward-theta positive control passes in at least two participants; and
4. stable-versus-early artifact-retention imbalance remains within 20 percentage points.

Passing supports the narrow statement that the construct-aligned measure transfers directionally to new empirical participants. Failing does not justify changing the window, participant set, or estimator.

## Prespecified secondary endpoint

Riemannian shrinkage-covariance distance is retained as a broader secondary measure using equal 250-ms windows (-300 to -50 ms and +50 to +300 ms). It measures multivariate neural-state reorganization, not specifically relative-phase topology, and cannot rescue or redefine a failed primary endpoint.

## Stopping rule

No additional phase metric will be searched if this gate fails. Model-based residual phase dynamics remains reserved and unimplemented. Any later change requires a new versioned protocol and a new untouched participant set.
