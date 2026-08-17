# Frozen protocol: EEG network reorganization during reversal learning

**Protocol status:** Frozen before inspecting any switch-locked network result
**Development participant:** `sub-s1` (used only to validate preprocessing and the published theta direction)
**Confirmation subset:** `sub-s2`, `sub-s3`, `sub-s4`
**Full analyzed sample if the confirmation gate passes:** 23 published participants

## Scientific question

When reward contingencies reverse, does the brain temporarily reorganize its theta-band coordination, and does the magnitude of that reorganization predict how quickly a participant adopts the newly advantageous choice?

This is a physiological test of the proposed transition from stable exploitation, through coordination release/reorganization, to a new stable strategy. It is not a test of anatomical cooperative or competitive connections because scalp EEG does not identify the sign or location of the Hopf model's regional couplings.

## Primary hypotheses

### H1 — Reversal-related reorganization

During negative-feedback trials in the early post-reversal period, theta-band scalp coordination will show:

1. lower mean global phase synchrony than during feedback-matched stable exploitation;
2. higher within-epoch variability of global synchrony; and
3. greater change in the phase-relationship pattern relative to the pre-feedback baseline.

The third quantity—phase-pattern reconfiguration—is the primary endpoint. Mean synchrony and within-epoch variability are co-primary mechanistic descriptors but will not independently determine whether the confirmation gate passes.

### H2 — Reorganization predicts adaptation

Within participants, reversal episodes with greater early phase-pattern reconfiguration will have shorter behavioral adoption latency.

### H3 — Re-stabilization

After behavioral adoption, coordination measures will move back toward their pre-reversal stable values. This is secondary because some reversal blocks may not contain enough clean post-adoption negative-feedback trials.

## Why feedback matching is mandatory

Negative reward feedback already increases frontal-midline theta. Early post-reversal periods also naturally contain more negative outcomes. Comparing all early post-reversal trials with all stable trials would therefore confound network reorganization with feedback valence.

The primary H1 comparison uses **negative-feedback trials only**. Positive-feedback trials provide a secondary sensitivity analysis. Reward and punishment tasks are estimated separately before any combined estimate.

## Behavioral definitions

### Reversal points

- Task performed first: trials 82, 150 and 225.
- Task performed second: trials 86, 160 and 223.

### Old and new preferred stimulus

For each reversal episode:

1. The old preferred stimulus is the modal stimulus choice during the 20 trials immediately before reversal.
2. The candidate new stimulus is the opposite stimulus.

This definition is necessary because the public action arrays do not explicitly label ground-truth optimality.

### Adoption trial

The adoption trial is the first post-reversal trial beginning a six-trial window in which the candidate new stimulus is selected on at least five trials. The adoption must occur before the next reversal. Episodes without adoption are retained for H1 but marked right-censored and excluded from the simple H2 latency correlation; a censored sensitivity model will include them.

### Analysis periods

- **Stable pre-reversal:** trials −10 through −1.
- **Early updating:** trials 0 through +9, where trial 0 is the first trial under the new contingency.
- **Post-adoption:** adoption trial through adoption +9, truncated before the next reversal.

## EEG preprocessing

The frozen preprocessing follows the successful participant-1 pilot:

1. Read continuous EEGLAB `.set`/`.fdt` data.
2. Downsample from 1024 Hz to 512 Hz.
3. Average reference.
4. Apply a 50 Hz notch filter.
5. Fit extended-infomax ICA to a 1–100 Hz copy, using a fixed random seed of 42 and decimation of 4.
6. Detect blink candidates using Fp1 and Fp2 as proxy EOG channels; remove at most two components at the fixed threshold of 3.0.
7. Apply the ICA solution to data filtered from 0.1–100 Hz.
8. Exclude the authors' released participant/task-specific bad-trial indices.
9. Do not add outcome-dependent rejection thresholds.

The unavailable original manual ICA choices are a known methodological deviation. A no-ICA and one-component-versus-two-component sensitivity analysis will test whether conclusions depend on the automated approximation.

## Sensor-space protection against volume conduction

Average-referenced scalp synchrony can be inflated by instantaneous field spread. Before the novel network metrics are computed:

1. assign the standard 10–20 electrode montage;
2. apply a surface-Laplacian/current-source-density transform;
3. verify that every analyzed EEG channel has a valid position;
4. repeat the primary endpoint with theta weighted phase-lag index as a sensitivity analysis.

The CSD result is primary. No sensor-space result will be described as communication between specific anatomical brain regions.

## Frozen signal windows and metrics

### Frequency band

- Primary: theta, 4–8 Hz.
- Negative-control band: alpha, 8–12 Hz.

### Epoch

- Feedback locked: −1.5 to +3.0 seconds.
- Baseline reference window: −0.30 to −0.20 seconds.
- Network-response window: +0.20 to +1.50 seconds.

The longer network window is intentionally different from the published 250–500 ms power window: phase coordination requires multiple theta cycles for a stable estimate.

### Metric 1 — Global phase synchrony

For analytic theta phase \(\phi_k(t)\) at sensor \(k\):

\[
R(t)=\left|\frac{1}{K}\sum_{k=1}^{K}e^{i\phi_k(t)}\right|.
\]

Per trial, record mean \(R(t)\) in the response window.

### Metric 2 — Within-epoch synchrony variability

Per trial, record the standard deviation of \(R(t)\) within the response window. This is an EEG-timescale coordination-variability measure; it will not be called whole-brain metastability without qualification.

### Metric 3 — Phase-pattern reconfiguration (primary endpoint)

At each time point, create the pairwise phase-difference representation. Calculate its circular/cosine distance from the trial's mean baseline phase-difference pattern, then average the distance within the response window.

This metric is invariant to a common global phase rotation and directly quantifies how much the relative sensor-phase organization departs from baseline.

### Sensitivity metric — Debiased theta wPLI

Estimate debiased weighted phase-lag index across trials within each participant, task, period and feedback condition. Summarize the mean across predefined frontocentral-to-posterior channel pairs. This measure reduces zero-lag volume-conduction sensitivity but is not single-trial, so it is a group-period sensitivity analysis rather than the H2 predictor.

## Statistical unit and tests

Participants are the inferential units. Trials and reversal episodes are repeated observations, not independent samples.

### H1 confirmation test

1. Compute each participant's mean early-updating minus stable-pre difference using negative-feedback trials.
2. Test the participant-level difference with a two-sided exact/sign-flip permutation test.
3. Report the mean paired difference, standardized paired effect and 95% participant-bootstrap confidence interval.
4. Analyze reward and punishment tasks separately. Reward is the primary task because participant 1 passed the published reward theta direction; punishment is confirmatory-secondary.

### H2 test

Fit a participant-centered episode-level model:

\[
\text{adoption latency} \sim \text{early reconfiguration} + \text{task} + (1|\text{participant}).
\]

The directional prediction is a negative reconfiguration coefficient. Participant-cluster bootstrap intervals will be reported. A Spearman correlation between participant-mean reconfiguration and participant-mean latency is a transparent secondary summary.

### Multiple endpoints

Phase-pattern reconfiguration is the single primary endpoint. Mean synchrony, variability, wPLI and alpha-band analyses are secondary or sensitivity outcomes. No result will be promoted to primary after inspection.

## Nulls and falsification checks

1. **Feedback-valence match:** primary comparisons contain negative feedback only.
2. **Pre-feedback null:** the same period contrast should not appear in the −1.3 to −0.3 second pre-feedback interval.
3. **Alpha-band negative control:** a theta-specific effect should be weaker or absent at 8–12 Hz.
4. **Within-task circular reversal shift:** shift reversal labels by a random offset that preserves task order and autocorrelation; repeat at participant level.
5. **No-ICA sensitivity:** repeat the primary endpoint without component removal.
6. **Artifact-load sensitivity:** include each participant's rejected-trial proportion as a participant-level covariate/descriptive check.
7. **Minimum-data rule:** a participant-period cell requires at least five clean trials; otherwise that task-specific comparison is missing, not imputed.

## Staged decision gates

### Gate A — Confirmation subset

Run `sub-s2`, `sub-s3` and `sub-s4` without changing parameters.

Pass if:

- all three recordings pass file and channel integrity checks;
- at least two participants retain the minimum number of negative-feedback trials in both stable and updating periods;
- preprocessing produces finite metrics without an outcome-specific rejection imbalance greater than 20 percentage points;
- the participant-level reward-task reconfiguration direction is positive in at least two of three participants.

This is a pipeline/direction gate, not a significance test.

### Gate B — Full sample

If Gate A passes, download and analyze the remaining published participants. Freeze the code version and configuration hash before inspecting the aggregate result.

### Failure interpretation

- Failure of the published reward-theta control across the confirmation subset blocks novel inference and triggers preprocessing diagnosis.
- Passing theta but failing network reconfiguration is an informative constraint: feedback processing is measurable, but the proposed coordination-release mechanism is unsupported.
- A reconfiguration effect that disappears after feedback matching is evidence that the unadjusted result was valence-driven.

## Permitted claim if successful

> Human reversal updating is accompanied by a feedback-matched change in theta-band scalp coordination, and the magnitude of this physiological reorganization covaries with behavioral adaptation.

## Claims that remain prohibited

- EEG proves that negative structural connections caused switching.
- Scalp sensors identify cooperative versus competitive anatomical edges.
- The Luppi participant's connectome predicts these participants' behavior.
- Trial counts substitute for participant-level replication.
