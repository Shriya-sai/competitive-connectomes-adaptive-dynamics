# Critical comparison of empirical validation routes

## Bottom line

The earlier Wang + `ds000052` proposal is feasible, but it is not strong enough to serve as a decisive validation of the Hopf-to-adaptive-flexibility bridge. Its largest weakness is design confounding: in `ds000052`, reversed contingencies occur in the later blocks, so reversal is entangled with time, practice, fatigue and run order.

There are two different empirical goals, and they favour different datasets:

- **Exact reversal-learning validity:** Wang behaviour plus public reversal-learning EEG is the strongest immediately actionable route.
- **Same-person connectome-to-task validity:** AOMIC PIOP2 is the strongest accessible route, but it substitutes response inhibition/cognitive control for reversal learning.

No route found provides both goals simultaneously.

## Critical weaknesses of Wang + `ds000052`

### 1. Reversal is confounded with block order

Participants first completed two classification-learning blocks and then two reversed-contingency blocks. A difference between the early and late runs could therefore reflect reversal, ordinary learning, habituation, fatigue, motion drift, scanner drift or task familiarity. With no verified counterbalanced reversal order, those explanations cannot be cleanly separated.

### 2. It is not the same reversal process as Wang

Wang contains 12 within-block contingency reversals and resolves adaptation trial by trial. `ds000052` places reversal between blocks. The former measures repeated flexible updating; the latter is closer to comparing acquisition with later relearning.

### 3. The sample is very small

The dataset contains 13 participants. Participant-level inference will be imprecise, sensitivity to motion and outliers will be high, and complex individual-difference modelling is not justified.

### 4. There is no participant-specific structural connectome

T1 anatomy is available, but no diffusion MRI or verified resting fMRI is present. We could observe task dynamics, but could not ask whether each participant's structural topology generated those dynamics.

### 5. Task-evoked synchrony is not spontaneous Hopf synchrony

Common stimulus timing and the haemodynamic response can increase apparent inter-regional coordination. KOP, metastability and LEiDA differences may therefore reflect shared evoked responses rather than altered endogenous coupling. Event regression, matched temporal masks and suitable phase-randomized/event-preserving nulls would be mandatory.

### 6. Cross-dataset triangulation breaks the individual-level chain

The Wang participants supply behaviour; `ds000052` participants supply continuous BOLD; the Luppi subject supplies the fitted connectome. Agreement across them is convergent evidence, not proof that a person's cooperative–competitive topology causes their adaptive behaviour.

### 7. Researcher degrees of freedom remain large

Filtering, parcellation, nuisance regression, global-signal treatment, event regression, window definition and landscape metrics can materially change dynamic-fMRI results. Predictions must be frozen before the empirical contrast is examined.

## Alternatives

### Route A — Wang behaviour + Wang fMRI derivatives only

**Strengths:** exact task, same participants, high behavioural richness, immediately available, low computational burden.

**Weaknesses:** condition-level maps collapse temporal dynamics; original analysis choices constrain what can be tested; no raw continuous BOLD or individual structural connectivity.

**Best claim:** the model reproduces behaviour and is spatially consistent with released task contrasts—not that it reproduces neural state transitions.

### Route B — Wang + `ds000052` continuous fMRI

**Strengths:** exact broad construct, public BOLD, event-related acquisition, accessible pilot.

**Weaknesses:** block-order confound, N=13, different task, no dMRI/rest, cross-participant triangulation.

**Best claim:** an independent historical reversal dataset shows a directionally compatible change in fMRI dynamics.

### Route C — Wang + public reversal EEG (`ds004295`)

This dataset contains 26 participants, 66-channel EEG, trial events and reward-gain/punishment-avoidance reversal tasks.

**Strengths:** exact reversal construct, millisecond temporal resolution, trial-resolved feedback dynamics, positive and negative reinforcement conditions, public BIDS data.

**Weaknesses:** scalp EEG is not regional BOLD; source localization is uncertain; it cannot directly validate 100-region Hopf topology or structural connections.

**Best claim:** the model's predicted timing and coordination changes around negative feedback and switching agree with an independent physiological modality.

### Route D — AOMIC PIOP2 multimodal MRI

PIOP2 provides T1, diffusion MRI, resting fMRI, task fMRI and event annotations for 226 included participants. Its stop-signal task measures response inhibition.

**Strengths:** same-person structural and functional data, adult sample, open raw and preprocessed BIDS data, much larger N, strong quality control.

**Weaknesses:** no reversal learning or exploration–exploitation manipulation. Stopping an initiated response is related to flexibility but is not equivalent to learning that reward contingencies changed.

**Best claim:** individual connectome organization predicts how brain dynamics reconfigure during cognitive control. This validates the general connectome-to-adaptive-control bridge, not the reversal-specific hypothesis.

### Route E — ABCD multimodal MRI

ABCD contains structural MRI, diffusion MRI, resting fMRI, task fMRI and behaviour at very large scale. Relevant tasks include monetary incentive delay and stop-signal tasks.

**Strengths:** exceptional sample size, longitudinal data and same-person multimodality.

**Weaknesses:** no reversal task; children/adolescents rather than adults; controlled-access and substantial governance/computational burden; multisite and developmental confounds.

**Best claim:** cooperative–competitive network features relate to reward processing or inhibitory control across development—not direct reversal-learning validation.

### Route F — Obtain Fouragnan simultaneous EEG-fMRI data

The study acquired simultaneous EEG-fMRI from 20 participants during criterion-triggered probabilistic reversal learning.

**Strengths:** closest conceptual match; trialwise behaviour, high temporal resolution and whole-brain haemodynamics in the same participants.

**Weaknesses:** no public raw release was located; access would require author contact and may be impossible; no verified dMRI/rest; N=20.

**Best claim if obtained:** within-person cross-modal validation of switching dynamics, though still not a participant-specific structural-connectome test.

## Comparison test

Each route was scored from 0 to 5 on eight criteria. Scores are an explicit decision aid, not empirical measurements. Two weighting schemes were used because one universal score would hide the scientific trade-off.

| Route | Reversal-specific score | Connectome-bridge score |
|---|---:|---:|
| Wang + reversal EEG | **4.00** | 3.30 |
| Wang + `ds000052` | 3.95 | 3.05 |
| Wang derivatives only | 3.85 | 3.25 |
| Fouragnan raw data, if obtained | 3.75 | 3.25 |
| AOMIC PIOP2 | 3.05 | **4.10** |
| ABCD | 2.60 | 3.60 |

### Reversal-specific weighting

- construct match: 30%
- continuous neural dynamics: 15%
- behavioural richness: 15%
- same-person multimodality: 10%
- sample size: 10%
- access: 10%
- confound control: 5%
- implementation feasibility: 5%

### Connectome-bridge weighting

- same-person multimodality: 25%
- continuous neural dynamics: 15%
- sample size: 15%
- construct match: 10%
- behavioural richness: 10%
- access: 10%
- confound control: 10%
- implementation feasibility: 5%

## Recommended strategy

Do not make `ds000052` the centrepiece. Use a layered design:

1. **Primary exact-task validation:** Wang behaviour, with its released fMRI derivatives as same-participant spatial constraints.
2. **Primary physiological switching validation:** reversal EEG `ds004295`, using preregistered feedback-locked and switch-locked measures.
3. **Optional historical fMRI sensitivity analysis:** `ds000052`, explicitly labelled exploratory because of the block-order confound.
4. **Independent connectome bridge:** a small preregistered AOMIC PIOP2 analysis asking whether cooperative–competitive topology predicts reconfiguration during response inhibition.
5. **High-value access attempt:** contact the Fouragnan authors for de-identified raw EEG-fMRI, task events and behaviour. This is worth attempting, but the project must not depend on receiving it.

This design separates two claims that the earlier route blurred:

- **Does the proposed mechanism resemble physiological switching during reversal?** Wang + reversal EEG.
- **Can individual structural/intrinsic network organization constrain adaptive task reconfiguration?** AOMIC.

If both succeed, the evidence converges. If only one succeeds, we learn exactly which half of the proposed bridge remains unsupported.

## Sources

- Wang et al.: https://www.nature.com/articles/s41467-025-63995-x
- `ds000052`: https://openfmri.org/dataset/ds000052/
- reversal EEG `ds004295`: https://openneuro.org/datasets/ds004295
- AOMIC: https://nilab-uva.github.io/AOMIC.github.io/
- AOMIC data paper: https://www.nature.com/articles/s41597-021-00870-6
- ABCD imaging documentation: https://docs.abcdstudy.org/documentation/imaging/
- Fouragnan et al.: https://www.nature.com/articles/ncomms9107
