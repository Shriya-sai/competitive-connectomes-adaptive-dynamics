# Reversal EEG pilot audit (`ds004295`)

## Decision

The event-and-behaviour feasibility gate **passed**. The dataset supports a trial-resolved, feedback-locked physiological switching analysis after the raw EEG is acquired with an integrity-checked resumable client.

This does not validate the regional Hopf topology. EEG will test temporal and coordination predictions around reversal; regional/connectome claims remain assigned to fMRI and multimodal MRI analyses.

## Files inspected

- BIDS dataset, participant, channel and event metadata;
- all 26 participant event tables;
- the released behavioural MAT file;
- the authors' Q-learning code;
- the full task methods and reversal schedule in the associated paper.

No raw EEG binary was downloaded in this gate.

## Confirmed design

- 26 BIDS EEG recordings; 23 participants in the published analysis.
- Exclusions: `sub-s5`, `sub-s7`, and `sub-s9`, matching the released participant metadata.
- Two 280-trial probabilistic reversal tasks per analyzed participant.
- Reward task: monetary gain versus non-gain.
- Punishment task: noise-burst avoidance versus receipt of the noise burst.
- Feedback probabilities: 70/30 versus 30/70.
- Three reversals per task, hence six reversals per participant and 138 analyzed participant-task-reversal events.
- If a task was performed first, reversals occurred at trials 82, 150 and 225; if performed second, at 86, 160 and 223.
- Reward/punishment task order was counterbalanced and is recoverable from the EEG start markers.
- Continuous EEG: 66 channels, 1024 Hz for the pilot participant, approximately 4592 seconds.

## File-level validation results

- All 23 behavioral arrays were mapped uniquely to BIDS participant IDs by exact reward and punishment feedback sequences.
- Every non-excluded participant had 280 complete trials in each task.
- Selection, expectation and feedback timestamps were recoverable for every analyzed trial.
- Some recordings contained duplicate spatial choice markers. The parser therefore anchors trials to the one-per-trial feedback marker and retains the last choice and expectation preceding feedback.
- The event markers encode spatial button choices; the behavioral MAT arrays encode the stimulus-level action used by the authors' Q-learning analysis. Behavioral switching must use the MAT actions, not the raw left/right event marker.

## Behavioral sanity check

Using the dominant stimulus choice in the 20 trials before each reversal as a transparent proxy for the old preferred option:

- last ten pre-reversal trials choosing the old option: `0.777`;
- first two post-reversal trials choosing the opposite option: `0.391`;
- final ten trials before the next reversal choosing the new option: `0.770`.

This is the expected collapse-and-recovery pattern. It is a data-derived switching proxy, not ground-truth accuracy, because the released arrays do not explicitly label the optimal stimulus.

## Acquisition issue discovered

A test download of participant 1's EEGLAB `.set` header was interrupted. The S3 endpoint did not safely honour the attempted byte-range resume, producing an overlapping/corrupt local file. It was preserved as `sub-s1_task-task_eeg.set.partial-corrupt` and was not analyzed.

Before downloading the 1.24 GB participant signal or the 31.5 GB dataset, use an integrity-aware client such as the OpenNeuro CLI, DataLad/git-annex, or an S3 client that verifies object size and checksum. Never treat a completed HTTP command as proof of file integrity.

## One-participant preprocessing positive control

Participant 1's complete EEGLAB pair was subsequently acquired and verified:

- `.set`: 39,422,168 bytes and exact MD5/ETag match;
- `.fdt`: 1,241,382,912 bytes and exact remote-size match (multipart ETag, so not a simple MD5);
- MNE structural load: 66 channels, 4,702,208 samples, 1024 Hz, 4592 seconds and 1,704 annotations.

The Python pilot then:

- downsampled to 512 Hz;
- applied average reference, 50 Hz notch and 0.1–100 Hz filtering;
- fitted extended-infomax ICA to a 1–100 Hz copy and removed two capped Fp1/Fp2 blink-proxy candidates;
- applied the authors' 62 reward and 86 punishment bad-trial exclusions for this participant;
- formed −1.5 to 3.0 second feedback epochs;
- computed seven-cycle Morlet power at 4–8 Hz;
- normalized power to the −300 to −200 ms baseline;
- averaged 250–500 ms activity across Fz, F1, F2, FCz, FC1 and FC2.

Retained epochs were 94 reward-negative, 124 reward-positive, 69 punishment-negative and 125 punishment-positive trials.

The published-direction reward positive control passed: negative feedback produced `0.675 dB` more frontal-midline theta than positive feedback. The punishment contrast was `−1.230 dB` for this participant. The original paper did not find a robust punishment feedback-valence effect at the group level, so the participant-level negative direction is neither confirmation nor contradiction of that group result.

This result validates pipeline plausibility only. Trials are repeated observations within one person and cannot be treated as independent biological samples.

Outputs:

- preprocessing script: `scripts/preprocess_reversal_eeg_pilot.py`;
- integrity record: `results/reversal_eeg_pilot/download_integrity.json`;
- summary: `results/reversal_eeg_preprocessing_pilot/summary.json`;
- trialwise theta: `results/reversal_eeg_preprocessing_pilot/trialwise_fm_theta.csv`;
- figure: `figures/reversal_eeg_preprocessing_pilot.png`.

## Next analysis gate

1. Freeze the EEG preprocessing choices and define sensitivity variants for the unavailable manual ICA decisions.
2. Predefine switch-locked hypotheses, metrics, time windows and participant-level estimands.
3. Acquire and preprocess a small multi-participant confirmation subset.
4. Confirm that the reward theta direction is not unique to participant 1 before downloading all 23 analyzed participants.
5. Keep the EEG result separate from anatomical Hopf claims.

## Reproducible outputs

- Audit script: `scripts/audit_reversal_eeg_events.py`
- Summary: `results/reversal_eeg_pilot/audit_summary.json`
- Event completeness: `results/reversal_eeg_pilot/event_audit.csv`
- Behavioral-to-BIDS mapping: `results/reversal_eeg_pilot/behavioral_mat_mapping.csv`
- Reversal proxy values: `results/reversal_eeg_pilot/reversal_proxy_metrics.csv`

## Sources

- OpenNeuro dataset: https://openneuro.org/datasets/ds004295
- Dataset DOI: https://doi.org/10.18112/openneuro.ds004295.v1.0.0
- Associated paper: https://doi.org/10.1111/psyp.14235
