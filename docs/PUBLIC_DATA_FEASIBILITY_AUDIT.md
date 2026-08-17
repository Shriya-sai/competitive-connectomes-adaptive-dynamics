# Public-data feasibility audit

## Candidate dataset

Wang et al. (2025), *Thalamic regulation of reinforcement learning strategies across prefrontal-striatal networks*.

- Study: https://www.nature.com/articles/s41467-025-63995-x
- OSF data: https://osf.io/6n7db/
- Analysis code: https://github.com/Bin-A-Wang2/ReversalLearning_Thalamic_regulations

## Confirmed study design

- 32 included human participants.
- Probabilistic tactile Go/NoGo reversal learning during fMRI.
- 12 blocks per participant, 45 trials per block, for 540 trials total.
- One reversal per block at a variable trial between trials 20 and 25.
- Reward probabilities were 0.70 versus 0.30 and reversed within each block.
- Three fMRI runs, approximately 16 minutes each; TR = 2.2 seconds.
- The study defines the ten trials before reversal as steady-state/exploitation and the ten trials after reversal as the switch period.

## Confirmed public files

### Behaviour

The OSF `Raw_behaviors` folder contains one approximately 16 KB text file per included participant plus a README. The released MATLAB code reads each file as a 540-trial matrix and uses it to reconstruct cue identity, cue and outcome timing, response, outcome class and reversal-aligned stage labels. Participant identifiers correspond to the processed-fMRI archives, so behavioural and neural data can be linked.

### Neural data

The OSF `Processed_fMRIdata` folder contains 32 participant-specific ZIP archives. Archive sizes range from approximately 349 MB to 827 MB and total roughly 19 GB. The paper states that raw imaging is withheld for privacy, but processed participant-level fMRI is public. The separate `Group_results` tree contains behavioural results and GLM, PPI, RSA and reinforcement-learning model-fit outputs.

### Code

Public MATLAB/SPM code documents the first-level GLM, event construction, RSA, PPI and DCM workflows. MATLAB is not required merely to parse the behavioural text files or NIfTI images; those portions can be translated to Python. Reproducing the authors' exact SPM analyses would require either MATLAB/SPM or a carefully validated Python equivalent.

## Feasibility decision

### Behavioural validation: feasible

The dataset can anchor model evaluation to real human reversal trajectories. Candidate empirical targets include:

- trial-aligned probability of the correct strategy;
- switch offset or latency;
- transition slope;
- lapse rate after switching;
- perseverative responses;
- steady-state versus switch-period performance;
- individual and block-level variability.

### Neural validation: feasible only in a narrower derivative-based form

Participant 04's archive was downloaded and inventoried without bulk extraction. It contains 426 NIfTI files: 325 beta maps, 32 contrast maps, 32 SPM t-statistic maps, residual/mask images and several ROI eigenvariate images. It also contains SPM, RSA, PPI and DCM model files. It does not contain continuous preprocessed four-dimensional BOLD runs or an evident set of trialwise beta maps.

Consequently, the task data cannot be passed through the Phase 3 KOP or continuous-LEiDA pipeline. Those instruments require an ordered regional time series. Neural validation must instead use the released condition-level beta/contrast maps, ROI eigenvariates, PPI/DCM results or representational geometry. Exact interpretation of each beta requires mapping it through the associated SPM design matrix and released analysis code.

## Important compatibility limits

- These participants are not the Luppi resting-state participant, so their task fMRI cannot be treated as a within-person continuation of the fitted Luppi connectome.
- The Luppi model uses a structural mask and fitted effective connectivity from a different dataset. Direct participant-specific model fitting is impossible unless compatible structural connectivity is present in the reversal dataset.
- A defensible test can still ask whether model variants reproduce group-level human behavioural and neural signatures, but it cannot claim participant-specific prediction from the Luppi connectome.
- Task BOLD contains evoked responses and differs from resting-state BOLD; preprocessing and null models must reflect that difference.
- Simulation seeds are not substitutes for the 32 biological participants. Human-level inference must use participants as the biological sampling unit.

## Recommended next gate

The behavioural portion of the pilot has passed for participant 04:

- exactly 540 data rows were recovered;
- the sequence divides into 12 blocks of 45 trials;
- every block contains one pre/post-reversal boundary;
- the first post-reversal trial ranged from trial 21 to 26 across blocks;
- response categories, reaction times and event timing are populated, with only three late-response trials in this participant.

The neural pilot is complete and rules out continuous task-landscape analysis with this release. Do not download the remaining approximately 19 GB at this stage. The next gate is to parse all 32 small behavioural files, reproduce the published human reversal curve and switching parameters in Python, and inspect participant 04's SPM design metadata to determine which condition-level neural contrasts can serve as secondary empirical targets.

## Final audit outcome

- **Primary empirical anchor:** strong, participant-level behavioural validation.
- **Secondary empirical anchor:** possible condition-level spatial or representational fMRI validation.
- **Not available:** continuous task-fMRI landscape dynamics, participant-specific structural connectomes or a direct within-person Luppi-to-reversal mapping.
- **Recommended project design:** treat human behaviour as the primary outcome; treat released fMRI derivatives as convergent secondary evidence; keep the Luppi-derived network experiment explicitly out-of-sample and mechanistic.

## Human behavioural baseline reconstructed

All deposited behavioural files were downloaded. The repository contains 33 files even though its README says 32; the authors' code resolves this discrepancy by explicitly excluding participant 30. The preregistered analysis set therefore follows the released `good subjects` vector of 32 participants.

Using the authors' latent-rule definition of correct strategy, the Python reconstruction produced the expected empirical trajectory: high stable performance immediately before reversal, a sharp post-reversal collapse, chance crossing after several trials and recovery to a new stable strategy.

- Mean accuracy over the ten trials immediately before reversal: `0.858` (between-participant SD `0.060`).
- Mean accuracy over the first ten trials after reversal: `0.576` (SD `0.095`).
- Estimated switch offset: `4.17` trials (SD `1.36`).
- Estimated transition slope: `1.96` (SD `3.15`).
- Estimated post-transition lapse parameter: `0.149` (SD `0.107`).

The reconstructed switch offset is close to the paper's reported `4.4 ± 1.6` trials. Slope and lapse estimates are directionally similar but not exact because the publication does not fully specify all numerical fitting constraints. The complete reversal-aligned curve, rather than any one fitted parameter, should therefore be the primary empirical target.
