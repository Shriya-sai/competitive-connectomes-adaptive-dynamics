# Project Outline: Competitive Connectomes and Adaptive Flexibility

## Research question

How do biologically inferred cooperative and competitive effective interactions jointly organize brain dynamics, and how might their balance support stable exploitation and adaptive exploration?

## Working hypothesis

Empirical brain dynamics emerge from the complementary spatial organization of cooperative and competitive effective interactions. Disrupting either component should impair model fit, while their relative balance may regulate the trade-off between stable maintenance and adaptive switching. Adaptive performance is expected to peak within an intermediate regime rather than at an extreme dominated by either interaction type.

## Data and software

- Public single-subject and three-subject data released with Luppi et al. (2026)
- Authors' C++ Hopf simulator and optimizer
- Independent open Python analysis pipeline; no MATLAB dependency
- Later validation may use larger public datasets, but this is not required for the initial project

## Phase 1 — Reproducible setup

**Objective:** Build a verified computational foundation.

**Status:** Complete.

- Create an isolated Python 3.12 environment.
- Clone and record the commit of the authors' repository.
- Build the `hopf` C++ extension.
- Confirm that `hopf.simulate()` and `hopf.optimize()` work.
- Inventory the released SC and BOLD data.
- Port regional-frequency extraction from MATLAB to Python and test it.

**Gate:** One successful optimization using the released single-subject data.

**Completed outputs:**

- Created and verified an isolated Python 3.12.9 environment.
- Recorded upstream repository commit `da592aab6784db5c6c59f29f6bcb2b3743f1afd7`.
- Built and smoke-tested the C++ Hopf extension without MATLAB.
- Ported regional-frequency extraction to Python and matched the released MATLAB reference exactly.
- Added optional simulation seed control while retaining the upstream default seed of 42.
- Added automated tests for data loading, frequency extraction, extension loading and stochastic seed control.

## Phase 2 — Core replication

**Objective:** Reproduce the main positive-only versus signed comparison.

**Status:** Complete for the released single subject, including an expanded mechanistic-null analysis.

- Fit a cooperative-only model.
- Fit a cooperative-competitive model with otherwise identical parameters.
- Compare empirical and simulated functional connectivity.
- Record convergence, runtime, inferred weights, negative-edge prevalence and variation across random runs.

**Gate:** The signed model shows a stable FC-fit advantage reasonably consistent with the repository benchmarks.

**Core result:**

- Cooperative-only fitted model: mean frozen-model FC correlation `0.482` across 30 noise seeds.
- Signed fitted model: mean frozen-model FC correlation `0.677` across the same 30 seeds.
- The signed model performed better in 30/30 matched stochastic runs.
- Simulation seeds are stochastic repetitions of one fitted subject, not independent biological subjects.

### Phase 2A — Frozen-model stochastic validation

**Question:** Is the signed-model advantage robust to stochastic neural noise rather than dependent on one lucky seed?

- Froze both optimized generative-connectivity matrices.
- Re-simulated both models across 30 matched random seeds.
- Confirmed a mean signed-minus-cooperative FC-correlation advantage of `0.196`.

**Conclusion:** The signed advantage is stable across stochastic forward simulations for this subject.

### Phase 2B — Whole-network weight-placement null

**Question:** Does the fitted anatomical placement of the complete signed weight set matter?

- Permuted reciprocal directed-weight pairs among occupied anatomical edges.
- Preserved the exact weight multiset, positive/negative counts, density, anatomical mask and reciprocal-pair asymmetry.
- Original fitted placement: mean FC correlation `0.682`.
- Mean of 100 shuffled placements: `0.067`; best shuffle: `0.116`.
- No shuffle matched the original (`p = 0.0099`).

**Conclusion:** The fitted weights are highly location-dependent. Because this null moves positive and negative weights together, it does not isolate either sign individually.

### Phase 2C — Sign-specific strength organization and ablation

**Questions:** Do the strength-to-location mappings of both signs matter, and must negative interactions remain negative?

- Shuffled all 767 negative strengths only among already-negative locations.
- Shuffled exactly 767 magnitude-matched positive strengths among their already-positive locations.
- Held every non-targeted weight fixed and used five matched simulation seeds.

**Results:**

- Original signed network: mean FC correlation `0.682`.
- Negative-strength shuffle: `0.562`, a mean loss of `0.119` (`p = 0.0099`).
- Matched positive-strength shuffle: `0.604`, a mean loss of `0.078` (`p = 0.0099`).
- Negative weights removed: `0.443`.
- Negative weights changed to positive at the same magnitudes and locations: `0.344`.

**Conclusion:** Both cooperative and competitive strength organization contribute to FC fit. Negative interactions must also retain their competitive sign. The larger negative-shuffle loss is a single-subject comparative result, not evidence that competition is universally more important.

### Phase 2D — Anatomical sign-map null

**Question:** With every connection magnitude fixed in place, does the anatomical assignment of cooperative and competitive roles matter?

- Permuted reciprocal sign-pattern pairs across occupied anatomical edges.
- Preserved every directed magnitude at its original location, the anatomical mask, positive/negative counts and the numbers of reciprocal `++`, mixed-sign and `--` patterns.
- Original sign map: mean FC correlation `0.682`.
- Mean of 100 randomized sign maps: `0.040`; best randomized map: `0.151`.
- No randomized sign map matched the original (`p = 0.0099`).

**Conclusion:** Topology, magnitudes and global sign balance are insufficient by themselves; the fitted cooperative and competitive roles form a coordinated anatomical configuration.

**Interpretive limit for all Phase 2 nulls:** These are frozen-model perturbations of a jointly optimized solution. They establish dependence within this fitted configuration, but do not prove that no differently reoptimized configuration could achieve a similar fit.

## Phase 3 — Dynamical validation

**Objective:** Reproduce and validate relevant brain-dynamics measures.

**Status:** Core dynamical characterization complete; preparing the adaptive-task phase.

- Calculate instantaneous phase and the Kuramoto order parameter.
- Calculate synchrony and metastability.
- Compare both models with empirical dynamics.
- Implement windowed FC, recurrent-state clustering, dwell time, state occupancy and transition entropy.
- Test all metrics on synthetic signals with known behavior.

**Completed measurement validation:**

- Implemented Hilbert instantaneous phase, the Kuramoto order parameter, mean synchrony and population-SD metastability.
- Added mathematical unit tests for known phases and synthetic oscillatory regimes.
- Correctly recovered synchronized signals (`synchrony = 1.000`, negligible metastability), evenly dispersed signals (`synchrony ≈ 0`), a switching regime (`synchrony = 0.523`, `metastability = 0.376`) and a random-phase control (`synchrony = 0.086`, `metastability = 0.044`).
- All seven predefined validation gates and all 18 project tests passed.

**Next Phase 3 step:** Define and verify the narrow-band preprocessing and boundary-handling choices before comparing empirical, cooperative-only and signed BOLD dynamics.

**Empirical/model phase-dynamics comparison:**

- Verified the human preprocessing band from the paper and released code: second-order Butterworth bandpass, `0.008–0.09 Hz`, with `TR = 0.72 s`.
- Applied identical detrending, zero-phase filtering and Hilbert/Kuramoto analysis to empirical and simulated BOLD.
- Empirical: mean synchrony `0.279`, maximum synchrony `0.704`, metastability `0.138`.
- Cooperative-only mean across 30 seeds: mean synchrony `0.395`, maximum synchrony `0.775`, metastability `0.170`.
- Signed mean across 30 seeds: mean synchrony `0.302`, maximum synchrony `0.655`, metastability `0.141`.
- The signed model was closer to empirical mean synchrony for 30/30 seeds and closer in metastability for 25/30 seeds. Maximum-synchrony accuracy was mixed (signed closer for 16/30 seeds).
- Conclusions were stable when excluding `0`, `20`, `50` or `100` samples from each time-series boundary.

**Interpretation:** The cooperative-only model exhibits excessive average coordination and excessive temporal variability in coordination. Competitive interactions moderate both, producing mean synchrony and metastability closer to the empirical signal. The fitted signed model tends to undershoot empirical maximum synchrony, so it does not dominate every dynamical metric.

**Recurrent-state and continuous-landscape work completed:**

- Validated windowed-FC clustering on synthetic signals, then stress-tested it across 768 combinations of noise, state duration and window size.
- Empirical k-means solutions were not uniquely stable. Consensus analysis supported several plausible granularities rather than one privileged number of states.
- Verified that Luppi et al. did not perform discrete state clustering, LEiDA or HMM analysis in the target paper.
- Implemented LEiDA with sign-invariant projective clustering. Correcting the eigenvector `v` versus `-v` ambiguity restored near-perfect synthetic recovery.
- No empirical 2–10-state solution passed every strict stability gate. Consequently, discrete states remain descriptive rather than the primary representation.
- Validated a continuous LEiDA landscape instrument measuring dispersion, effective dimension, central distance, speed, speed variability and recurrence.
- Across 30 frozen seeds, the signed model more accurately reproduced empirical dispersion, effective dimension and central distance, whereas the cooperative-only model was sometimes closer in speed-related measures.

**Cooperative–competitive gain experiment completed:**

- Independently varied cooperative and competitive gains while retaining the fitted anatomical placement of weights.
- Competition alone collapsed the modeled repertoire; cooperation alone remained incomplete.
- Low balanced gain produced an excessively expansive repertoire, the original balanced setting approached empirical geometry, and high balanced gain compressed the repertoire.
- Static FC and dynamical realism did not share a single optimum: stronger balanced coupling improved FC while worsening several landscape measures.

**Noise–bifurcation experiment completed:**

- Froze the signed connectome and cooperative–competitive gains, then varied noise strength and the Hopf bifurcation parameter.
- A promising exploratory setting (`a = -0.025`, noise `= 0.004`) was frozen and tested against the baseline (`a = -0.02`, noise `= 0.001`) using 30 entirely new paired seeds.
- The candidate improved empirical mean-speed proximity in 26/30 pairs and central-distance proximity in 25/30 pairs.
- It worsened effective dimension and dispersion in 20/30 pairs, recurrence in 29/30 pairs and FC in 30/30 pairs.
- A bifurcation-only control (`a = -0.025`, noise `= 0.001`) was nearly identical to the candidate, showing that added noise contributed little over the tested range.

**Revised Phase 3 conclusion:** Connectivity and cooperative–competitive balance strongly constrain the accessible dynamical landscape. The bifurcation parameter strongly affects movement through it, but also reshapes the landscape. Geometry and kinetics are therefore partially distinguishable but not independently adjustable in this model.

**Next step:** Freeze the Phase 3 model variants and enter Phase 4 by specifying and validating the reversal-learning task independently of the connectome comparison.

**Gate:** The metrics distinguish synchronized, independent, metastable and random signals correctly.

## Phase 4 — Adaptive task

**Objective:** Build an explicit exploration-exploitation problem.

**Empirical foundation established:**

- Identified and audited a public 32-participant probabilistic rule-reversal fMRI study with 540 trials and 12 reversals per participant.
- Downloaded all behavioural records and resolved a release inconsistency: participant 30 is deposited but excluded by the authors' explicit 32-participant analysis vector.
- Reconstructed the reversal-aligned human strategy curve in Python.
- Human performance averaged `0.858` over the ten trials before reversal and `0.576` over the first ten trials after reversal.
- Estimated human switch offset was `4.17 ± 1.36` trials, close to the published `4.4 ± 1.6`.
- A one-participant neural pilot showed that the public fMRI archives contain condition-level SPM/RSA/PPI/DCM derivatives but not continuous BOLD. Behaviour will therefore be the primary empirical target; neural derivatives will provide secondary spatial or representational evidence.

**Exact-task and neutral-model validation completed:**

- Implemented the released 540-trial schedule directly from the deposited experimental columns rather than constructing a generic reversal task.
- The learner receives cue, action and reward only; the reversal label is never exposed to it.
- A random-choice control remained at chance (`0.501`).
- A standard two-cue/two-action Q learner learned before reversal (`0.772` over the last ten pre-reversal trials), collapsed immediately afterward (`0.209` over the first two trials) and recovered (`0.735` over the final ten post-reversal trials).
- All four predefined task-validation gates passed on 500 confirmation seeds that were disjoint from the 100 parameter-selection seeds.
- The neutral Q learner did not fully match humans (`RMSE = 0.133` across the 40-point curve; humans reached `0.864` late post-reversal). This gap becomes a benchmark rather than something to hide.

**Next Phase 4 step:** Define how trial inputs, feedback and the readout interface with the frozen Hopf reservoir. Predefine training and test partitions and preserve the human curve as an untouched evaluation target before comparing connectivity variants.

**Empirical bridge audit added:** A targeted public-data search found no verified dataset combining repeated reversal behaviour, continuous task BOLD, resting fMRI and individual diffusion connectivity. The validation plan is therefore split into complementary tracks: Wang et al. remains the primary behavioural and derivative-based neural anchor, while OpenNeuro `ds000052` is the leading candidate for an independent continuous-task-fMRI cross-verification pilot. The Hopf variants and directional predictions must be frozen before group-level fMRI effects are inspected. See `docs/EMPIRICAL_FMRI_CROSS_VALIDATION_SEARCH.md`.

**Critical-review and EEG-pilot update:** The `ds000052` route was downgraded to an exploratory sensitivity analysis because reversal is confounded with later block/run order. Public reversal EEG (`ds004295`) is now the primary trial-resolved physiological switching route, while AOMIC PIOP2 is the candidate same-person structural/rest/task connectome bridge. The `ds004295` event-and-behaviour pilot passed: 23 analyzed participants were uniquely mapped, both 280-trial tasks were complete, all six reversals per participant were recoverable, and a collapse-and-recovery behavioral sanity check succeeded. See `docs/CRITICAL_ROUTE_COMPARISON.md` and `docs/REVERSAL_EEG_PILOT_AUDIT.md`.

**EEG preprocessing pilot completed:** Participant 1's 1.28 GB EEGLAB pair was acquired with verified object sizes and an exact MD5 match for the `.set` header. A declared Python approximation of the published preprocessing used the authors' manual bad-trial indices but automated blink-component selection because their manual ICA choices were unavailable. The reward positive-control direction passed: feedback-locked frontal-midline theta was `0.675 dB` higher after negative than positive reward feedback. This is a one-participant pipeline validation, not population inference. The next gate is to freeze switch-locked hypotheses and confirm preprocessing on a small participant subset before scaling to all 23.

**Switch-locked EEG protocol frozen:** The primary endpoint is feedback-matched theta phase-pattern reconfiguration after a current-source-density transform. Primary inference compares negative-feedback trials during early updating versus stable pre-reversal periods, preventing the known feedback-valence theta response from masquerading as reversal-related reorganization. Participant-level permutation and bootstrap inference is specified; mean synchrony, within-epoch variability, wPLI, alpha and pre-feedback analyses are secondary/null checks. The fixed confirmation subset is `sub-s2`, `sub-s3`, and `sub-s4`; parameters may not be retuned after inspecting their switch-locked results. See `docs/EEG_SWITCHING_ANALYSIS_PROTOCOL.md` and `configs/eeg_switching_analysis.json`.

- Construct a two-choice learning task.
- Reverse the correct stimulus-response mapping partway through.
- Train only a linear readout while keeping reservoir connectivity fixed.
- Measure learning, reversal cost, perseveration, unnecessary switching and recovery.

**Gate:** A standard control reservoir learns before reversal, declines after reversal and subsequently recovers.

## Phase 5 — Primary novel experiment

**Objective:** Test how cooperative and competitive connectivity jointly support adaptive stability and switching.

Compare:

1. Cooperative-only fitted connectivity
2. Biological signed fitted connectivity
3. Degree-preserving sign-shuffled connectivity
4. Matched random-topology controls

The precise null controls will be refined using the Phase 2 findings. In particular, whole-weight placement, within-sign strength placement and anatomical sign assignment must be treated as distinct manipulations.

Begin with the planned negative-weight-strength sweep using:

\[
G_{ij}^{(\lambda)} =
\begin{cases}
G_{ij}, & G_{ij} \geq 0 \\
\lambda G_{ij}, & G_{ij} < 0
\end{cases}
\]

Test values ranging from no competition through amplified competition. Match density, total weight, spectral radius, task inputs and readout training wherever possible.

Then perform a two-parameter cooperative–competitive gain sweep,

\[
G(\alpha,\beta)=\alpha G_{+}+\beta G_{-},
\]

to determine whether either interaction type can compensate for the other and whether a balanced regime produces distinct dynamical or adaptive behavior.

**Primary outcome:** Trials required to regain criterion performance after reversal.

**Prediction:** Extremes dominated by cooperation may produce excessive stability or perseveration, extremes dominated by competition may produce fragmentation or instability, and an intermediate joint regime may best balance retention with adaptive switching. This remains a hypothesis rather than an assumed outcome.

## Phase 6 — Gain/noise interaction

**Objective:** Test whether architecture and global state jointly regulate flexibility.

- Cross competition strength with spectral radius or a global gain/noise analogue.
- Map regimes of rigidity, adaptive flexibility and instability.
- Test whether metastability predicts adaptive performance nonlinearly.

**Interpretive limit:** Treat this as a gain/noise analogue, not a direct biological model of the LC-norepinephrine system.

## Phase 7 — Robustness and generalization

**Objective:** Attempt to falsify the result.

- Repeat across seeds, task sequences, reversal points and learning rates.
- Match spectral radius, density and absolute weight.
- Include degree-preserving sign shuffles and stationary-task controls.
- Separate useful switching from indiscriminate instability.
- Repeat the final analysis on the released three-subject data if feasible.

**Gate:** The main effect survives appropriate matched controls and is not explained solely by spectral radius, density, weight magnitude or readout learning rate.

## Phase 8 — Statistics and reporting

- Treat simulation seeds as repeated stochastic runs, not biological subjects.
- Report paired differences, confidence intervals and effect sizes.
- Separate variation across subjects from variation across simulations.
- Use interaction and quadratic models for competition-by-gain sweeps.
- Release code, configurations, seeds, derived results and figure scripts.

## Minimum viable project

The minimum complete study includes:

- a verified Python/C++ reproduction of the core FC result
- validated metastability calculations
- a working reversal-learning task
- cooperative-only, biological signed and matched-null comparisons
- a competition-strength sweep
- reproducibility and robustness checks

## Scope boundaries

This project will test a computational operationalization of exploration and exploitation. It will not claim to have directly measured human exploratory behavior, identified long-range inhibitory synapses, or established that negative generative weights correspond to a single biological mechanism.

## Immediate milestone

Enter Phase 4 by defining the reversal-learning task, outcome measures and success gates before testing any cooperative–competitive hypothesis. First establish that a neutral control reservoir can learn an initial mapping, decline immediately after reversal and subsequently recover.

## Current evidence summary

For the released single subject, the completed work supports the following bounded claim:

> Cooperative and competitive effective interactions jointly contribute to reproducing empirical static functional connectivity. Their signs, strengths and anatomical assignments form an interdependent fitted organization; perturbing either sign-specific strength pattern or the complete sign map impairs model fit.

Phase 3 now extends this claim: cooperative–competitive organization affects the accessible continuous dynamical repertoire, but static FC, landscape geometry and movement kinetics do not share one optimum. The bifurcation experiment further shows that changing movement through the landscape can simultaneously reshape it. These are single-subject computational findings and do not yet demonstrate adaptive explore–exploit behavior; that bridge will be tested explicitly in Phase 4.
