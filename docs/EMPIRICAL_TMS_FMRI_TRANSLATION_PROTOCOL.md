# Empirical Translation: Resting Architecture and TMS-evoked Propagation

## Dataset choice

Primary candidate: OpenNeuro `ds005498`, version 2.0.0, described in Glick et al. (2025), *Concurrent single-pulse TMS-fMRI dataset to reveal the causal connectome in healthy and patient populations*.

- Dataset: https://doi.org/10.18112/openneuro.ds005498.v2.0.0
- Data descriptor: https://doi.org/10.1038/s41597-025-05377-y
- Processing/QC code: https://github.com/braindynamicslab/sptmsfmri

The release contains 152 participants, eight-minute resting-state fMRI, and concurrent single-pulse TMS-fMRI at up to 11 cortical sites. Each stimulation run contains 68 jittered pulses at 120% of motor threshold. Not every participant completed every site.

The official GitHub repository contains MRIQC/QC scripts, stimulation masks and timing resources, but not a complete analysis-ready fMRI preprocessing workflow. We must therefore specify and validate our own preprocessing pipeline rather than describe the released code as one.

### Pilot integrity and timing audit

`sub-NTHC1035` contains a 240-volume resting run (TR 2.0 s) and eleven 167-volume TMS runs (TR 2.4 s). All 26 archived files match their public S3 manifest sizes after one truncated transfer was detected and corrected. Preprocessing is pinned to `nipreps/fmriprep:25.2.5` with FreeSurfer surface reconstruction disabled. The published image is AMD64-only and therefore runs through Docker emulation on this ARM64 Mac.

The shared MATLAB timing file contains 68 continuous pulse onsets from 11.8 to 388.6 seconds. The accompanying 162-line binary vector is not the acquired run length: it ends at the final pulse and omits five trailing zero-only volumes. Event modeling will use the MATLAB onsets. If the first three acquired volumes are discarded, 7.2 seconds must be subtracted from every onset.

### FreeSurfer licence gate

The FreeSurfer registration form repeatedly rejected its own reCAPTCHA. A
development attempt with fMRIPrep's supported `--force no-bbr` option still
failed: fMRIPrep 25.2.5 performs a global FreeSurfer licence check even when
surface reconstruction and BBR are disabled. No synthetic or borrowed licence
will be used. The standardized preprocessing route remains paused pending a
licence issued by FreeSurfer support; event construction and model
specification can proceed independently in the meantime.

### Licence-free volumetric contingency

After the registration form, support email and subscribed mailing-list route
failed to provide a licence, AFNI `26.1.04` was selected for a bounded
volumetric pilot. AFNI's `sswarper2` performs T1w skull stripping and nonlinear
normalization to its `MNI152_2009_template_SSW` reference, which is derived from
MNI152 nonlinear 2009c asymmetric space. The official AMD64 container is pinned
by tag and runs through Docker emulation on the ARM64 host. Anatomical
normalization is executed and visually quality-controlled before any functional
workflow is specified or any TMS response is inspected. fMRIPrep remains the
preferred sensitivity pipeline if a valid FreeSurfer licence is later issued.

#### Anatomical pilot result (sub-NTHC1035)

The pinned AFNI `26.1.04` `sswarper2` workflow completed on the session-1 T1w
image and produced the expected native-space skull-stripped anatomy, affine
transform, nonlinear warp and MNI2009c-normalized anatomy. All deliverable NIfTI
arrays were finite. The normalized anatomy has the template grid
(`193 x 229 x 193`, 1 mm isotropic); the native skull-strip preserves the input
grid (`184 x 256 x 256`, `1 x 0.9375 x 0.9375` mm).

Visual QC was accepted after inspecting the final edge-overlay montage and the
native-space skull-strip montage. Template edges followed the cortical envelope,
ventricles, cerebellum and medial/superior cortex without a gross orientation
error or implausible deformation. The skull-strip retained brain tissue without
obvious skull inclusion or major cortical loss. The large initial affine
translation (approximately 36 mm, predominantly anterior-posterior) therefore
did not indicate a failed registration; the subsequent affine refinement was
small (approximately 0.5 mm and 0.2 degrees), and the final visual result was
acceptable. This anatomical QC gate passes for the pilot subject.

The highest-resolution nonlinear passes were costly under AMD64 emulation. The
level-7 and fully refined montages were visually similar, but the fully refined
run is retained as the reference result. Any faster cap used during later
expansion must first be treated as a sensitivity analysis against this reference,
not silently substituted.

## Empirical question

**Does independently estimated resting network embedding predict whether a matched localized TMS event produces primarily local BOLD response or broader downstream propagation?**

This tests the most reproducible Stage 3 result. It does not test phase reconfiguration, because the temporal resolution and haemodynamic response of fMRI cannot validate the Hopf phase metric directly.

## Frozen conceptual predictions

1. Greater target negative-strength or mixed-sign resting embedding will predict greater absolute remote TMS-evoked propagation after accounting for local response.
2. Lower total absolute embedding (peripherality) will predict greater local susceptibility relative to remote propagation.
3. Positive strength, negative strength, and their interaction will explain more held-out propagation variance than unsigned total strength alone.

Failure of these predictions would weaken the proposed empirical bridge even if the Hopf mechanism remains internally valid.

## Terminology constraint

Negative resting-state functional correlation is not equivalent to a direct inhibitory or competitive anatomical connection. Empirical predictors will be called **positive functional embedding**, **negative functional embedding**, and **mixed-sign embedding**. Connection to the model's cooperative–competitive interpretation will remain a model-level analogy unless independently supported.

## Cohort sequence

1. Develop preprocessing and measurement on `sub-NTHC1035` through `sub-NTHC1038`, the first four ascending NTHC BIDS labels with rest and all 11 stimulation runs. This subset is explicitly non-inferential.
2. Freeze exclusions, parcellation, nuisance regression, event model, outcomes, and statistical model.
3. Primary confirmation in the non-trauma healthy-control cohort.
4. Secondary generalization to trauma-exposed healthy and symptomatic cohorts, with cohort interactions reported rather than pooled silently.

## Independent resting architecture

For each participant:

1. preprocess the resting run using a fully specified reproducible pipeline;
2. parcellate to the Schaefer atlas resolution supplied for stimulation sites;
3. estimate parcelwise resting functional connectivity;
4. for each stimulated parcel calculate positive strength, absolute negative strength, total absolute strength, and mixed-sign strength;
5. calculate predictors both with and without global-signal regression as a mandatory sensitivity analysis.

Architecture must be estimated only from rest—not from the TMS run being predicted.

### Frozen embedding definitions

Resting functional connectivity is the Pearson correlation matrix among the
cleaned Schaefer-100 parcel time series, with the diagonal set to zero. The
target is the unique parcel having the greatest voxel overlap with the released
stimulation sphere. Positive embedding is the sum of its positive
off-diagonal correlations; negative embedding is the sum of the absolute
values of its negative correlations; total absolute embedding is their sum;
and mixed-sign embedding is their geometric mean. The geometric mean is
descriptive and becomes zero if either signed component is absent. Confirmatory
models retain positive strength, negative strength and their explicit
interaction rather than replacing them with the mixed score. All quantities
are recomputed in a mandatory analysis that regresses the cleaned whole-brain
global signal from parcel time series. Negative correlation remains a
functional statistical relationship, not evidence of direct inhibition.

## TMS response outcomes

For each participant × stimulation-site run, fit an event-related BOLD model using the recorded pulse timings.

Primary outcomes:

- **local susceptibility:** absolute evoked beta in the stimulated parcel;
- **absolute remote propagation:** weighted mean absolute evoked beta outside the stimulated parcel;
- **propagation conditional on local response:** remote response with local response included as a covariate;
- **response extent:** number or fraction of remote parcels passing a threshold anchored to baseline variance, not to the local-response denominator.

Positive and negative BOLD betas will also be retained separately. Absolute propagation is primary because the Hopf result concerned response magnitude, while signed BOLD direction has a different interpretation.

### Frozen first-level model

The estimand is the mean response across all 68 pulses; pulse-specific effects
are prohibited because 41 of 67 inter-pulse intervals are 4.8 seconds or
shorter and their haemodynamic responses overlap. Events are modeled as
zero-duration impulses convolved with the canonical SPM haemodynamic response.
The design includes a 0.01 Hz cosine high-pass basis, six rigid-body motion
parameters and their first derivatives, and one-volume censor regressors for
fMRIPrep motion outliers or framewise displacement above 0.5 mm. The empirical
voxelwise fit will use an AR(1) noise model. The design must be full-rank and
must pass the synthetic known-effect recovery test before empirical fitting.

### Frozen spatial response instrument

The released binary stimulation sphere defines the local ROI. Local
susceptibility is the absolute value of its mean signed beta, with the signed
mean retained. Remote propagation is calculated in the Schaefer 2018
100-parcel, seven-network atlas at 2 mm resolution, matching the number of Hopf
regions without implying parcel identity. Any parcel touching the stimulation
sphere or a further 10 mm Euclidean buffer is excluded to prevent spatial
spillover from being labeled propagation. Each remaining parcel receives equal
weight; the primary measure is mean absolute parcel beta, with positive beta
and negative-beta magnitude retained separately. Response extent is secondary
and equals the fraction of remote parcels whose absolute parcel-mean z score is
at least 3.1. Propagation conditional on local response is not a single-map
quantity: it will be estimated across participant-site observations by adding
local susceptibility as a covariate.

## Primary statistical model

The observational unit is participant × stimulation site. Use a hierarchical model or an equivalent mixed-effects regression:

`remote propagation ~ positive embedding + negative embedding + positive×negative + local response + TMS intensity + motion + discomfort + site + cohort + (1|participant)`

The primary confirmation begins with the healthy-control cohort. Site is included to prevent fixed anatomical differences from masquerading as individual network-embedding effects. Predictors are standardized within site where appropriate.

Compare by nested, participant-grouped cross-validation:

- unsigned model: total absolute strength;
- signed-additive model: positive plus negative strength;
- signed-interaction model: positive, negative, and their interaction.

The signed interpretation is supported only if it improves held-out prediction and coefficient directions are stable across folds and GSR sensitivity analyses.

For local susceptibility, test whether total absolute embedding is negatively associated with local response after the same covariate controls.

## Failure criteria

The empirical bridge is not supported if:

- signed embedding fails to improve participant-held-out prediction over unsigned strength;
- effects reverse materially across nuisance-regression choices;
- apparent prediction disappears after site, motion, intensity, discomfort, and local response are controlled;
- results depend on one stimulation site or one cohort;
- A/B-style resampling of participants or sites produces unstable coefficient directions.

## Scope

Even a positive result would establish an architecture–perturbation relationship, not reversal learning or adaptive behaviour. It would validate the mechanistic bridge needed before asking whether this response profile predicts behavioural adaptation.
