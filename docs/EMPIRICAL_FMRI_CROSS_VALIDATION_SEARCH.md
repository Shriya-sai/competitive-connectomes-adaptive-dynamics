# Empirical fMRI cross-validation search

## Why this search was necessary

The proposed Hopf-to-reversal-learning interface is a mechanistic hypothesis, not something that has already been validated biologically. A convincing empirical test would ideally contain, for the same participants:

1. trial-by-trial reversal-learning behaviour;
2. continuous task fMRI with event timings;
3. resting-state fMRI for intrinsic dynamics; and
4. diffusion MRI for participant-specific structural connectivity.

No public dataset located in this search could be verified to contain all four. The project should therefore use **triangulation across complementary datasets**, not imply that one dataset provides a complete within-person validation.

## Candidate audit

| Dataset | Behaviour | Continuous task BOLD | Structural MRI | Rest/dMRI | Reversal design | Decision |
|---|---:|---:|---:|---:|---|---|
| Wang et al. (2025) | Yes; 32 included participants, 540 trials, 12 reversals | No; processed SPM derivatives only | Not released as usable raw anatomy | Not released | Many within-run reversals | Primary behavioural anchor and secondary derivative-based neural constraint |
| OpenNeuro `ds000052` | Event information must be verified in the downloaded BIDS files | Yes; 52 functional runs across 13 participants | Yes; 25 T1w files reported | No verified rest or dMRI | Two acquisition blocks followed by two reversed-contingency blocks | Best available independent continuous-fMRI cross-validation candidate |
| Fouragnan et al. (2015) | Rich probabilistic reversal task, 20 participants | Acquired simultaneously with EEG | Acquired as part of the imaging study | No verified rest/dMRI | Criterion-triggered multiple reversals | Scientifically excellent, but no public raw-data release was located; not presently actionable |
| Sequential Inference VBM, `ds000222` | Probabilistic reversal behaviour | No task fMRI | T1-weighted MRI | No verified rest/dMRI | Reversal task | Behaviour/structural morphology only; not useful for dynamic fMRI validation |
| Reversal learning in FTD (Dryad) | Behavioural tables and task materials | Public archive appears not to contain raw imaging | Not verified | Not verified | Reversal learning | Useful contextual/clinical material, not a continuous-BOLD dataset |
| Williams et al. reversal reliability dataset | Open behavioural retest data; 150 participants | No | No | No | Repeated reversal task | Strong behavioural robustness dataset, but no neural cross-validation |

## Critical-review update

A subsequent critical comparison found that the Wang + `ds000052` route should not be the centrepiece. The reversal manipulation in `ds000052` is confounded with later block/run order, and a public reversal-learning EEG dataset provides a cleaner trial-resolved physiological test. AOMIC PIOP2 provides the strongest accessible same-person structural/rest/task bridge, although its stop-signal task is not reversal learning. See `docs/CRITICAL_ROUTE_COMPARISON.md` for the scored sensitivity analysis and revised layered recommendation.

## Recommended empirical architecture

### Track A — Wang: preserve the strongest behavioural test

Keep the 32-person reversal curve untouched as the primary behavioural target. Model choices should not be tuned directly against the final human curve. The released condition-level beta maps, contrasts, ROI eigenvariates, RSA, PPI and DCM outputs can constrain broad neural claims—for example, which regions and interactions distinguish stable rule use from updating—but cannot validate continuous KOP or LEiDA trajectories.

### Track B — `ds000052`: independent continuous-fMRI cross-verification

Use raw task BOLD to ask a deliberately narrower question:

> When reward contingencies reverse, do empirical regional dynamics change in the same direction as the model predicts when it moves from stable exploitation toward updating?

Candidate preregistered fMRI quantities are:

- change in regional phase-coherence or synchrony between initial and reversed blocks;
- change in metastability, with motion-matched and duration-matched sensitivity analyses;
- change in continuous LEiDA geometry rather than unstable hard state labels;
- changes in participation/integration of prefrontal, striatal and thalamic regions, subject to atlas coverage;
- whether signed versus cooperative-only simulations predict the *direction* of empirical changes.

This is cross-verification, not a direct fit: `ds000052` participants do not have the Luppi connectome, and its between-block contingency reversal differs from Wang's frequent within-block reversals.

## Validation firewall

To prevent the empirical target from silently becoming a tuning target:

1. Freeze the Hopf variants and the proposed task readout before examining fMRI group differences.
2. Predefine ROIs, preprocessing, temporal masks, metrics and expected directional effects.
3. Use one dataset for development and the other for confirmation; do not repeatedly revise the model after inspecting both.
4. Treat participants—not simulation seeds or fMRI volumes—as the inferential sample.
5. Report null and contradictory results as constraints on the bridge hypothesis.
6. Avoid participant-specific or causal claims because no verified public dataset links reversal behaviour, task BOLD and individual diffusion connectomes in the same people.

## Immediate next gate

Download only the small metadata and one participant from `ds000052` first. Confirm:

- BIDS validity and actual run lengths;
- whether `events.tsv` files retain trial identity, feedback, response and contingency condition;
- fMRI temporal resolution and spatial coverage;
- whether the reversal manipulation is identifiable without reconstructing unavailable task logs;
- data quality after modern preprocessing.

Only if that pilot passes should the full dataset be downloaded and a formal analysis plan frozen.

## Sources

- Wang et al. study and data-availability statement: https://www.nature.com/articles/s41467-025-63995-x
- Wang et al. OSF deposit: https://osf.io/6n7db/
- OpenFMRI/OpenNeuro `ds000052`: https://openfmri.org/dataset/ds000052/
- OpenNeuro `ds000052`: https://openneuro.org/datasets/ds000052
- Fouragnan et al. simultaneous EEG-fMRI study: https://www.nature.com/articles/ncomms9107
- Sequential Inference VBM (`ds000222`): https://openfmri.org/dataset/ds000222/
- FTD reversal-learning deposit: https://datadryad.org/dataset/doi:10.5061/dryad.tdz08kq0j
- Reversal-learning reliability behavioural dataset: https://researchdata.reading.ac.uk/1307/
