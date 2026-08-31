# Competitive Connectomes and Adaptive Dynamics

An independent Python/C++ reproduction and mechanistic extension of Luppi et
al., [*Competitive interactions shape mammalian brain network dynamics and
computation*](https://doi.org/10.1038/s41593-026-02205-3).

This project asks how cooperative and competitive effective interactions jointly
shape whole-brain dynamics, and whether their organization predicts how a
localized perturbation remains local or propagates through the brain.

## Project status

The single-subject computational reproduction and mechanistic perturbation
sequence are complete. An empirical TMS-fMRI translation is preregistered in
code and undergoing pilot preprocessing. A FreeSurfer licence has now been
obtained and the pinned fMRIPrep right-preSMA pilot is ready to run. The
empirical stage is not yet a confirmed result.

Current test status in a fully provisioned checkout: **42 passing tests**.

## What was reproduced

The authors' released C++ Hopf optimizer was rebuilt for Python 3.12 and used
with their released 100-region human demonstration data. Regional oscillation
frequency extraction was independently translated from MATLAB into Python and
matched the released reference.

For one fitted subject, frozen models were re-simulated across 30 matched noise
seeds:

| Model | Mean empirical–simulated FC correlation |
|---|---:|
| Cooperative only | 0.482 |
| Cooperative–competitive | 0.677 |

The signed model performed better in all 30 matched simulations. These are
stochastic repetitions of one fitted biological subject—not 30 independent
subjects.

## Mechanistic extensions

The project separates questions that a simple signed-versus-positive comparison
cannot answer:

- **Whole-weight placement null:** the fitted signed network achieved mean FC
  correlation 0.682; 100 reciprocal-pair placement shuffles averaged 0.067,
  with none matching the original (`p = 0.0099`).
- **Sign-specific strength nulls:** shuffling negative strengths reduced mean
  fit by 0.119; a magnitude-matched positive-strength shuffle reduced it by
  0.078. Both cooperative and competitive organization mattered.
- **Sign-map null:** fixing every magnitude while redistributing cooperative and
  competitive anatomical roles reduced mean fit from 0.682 to 0.040 across 100
  null maps (`p = 0.0099`).
- **Dynamical validation:** the signed model was closer to empirical mean
  synchrony for 30/30 seeds and closer in metastability for 25/30 seeds, but did
  not dominate every measure.
- **Perturbation experiments:** local susceptibility and remote influence
  dissociated. Weakly embedded targets could be locally susceptible, whereas
  negative-strength and mixed-sign targets became stronger broadcasters when
  competitive pathways were active.

The bounded computational conclusion is that cooperative and competitive signs,
strengths and anatomical assignments form an interdependent fitted organization.
This does **not** establish that negative effective weights are inhibitory
synapses or that one fitted subject represents a population.

## Empirical validation route

Several candidate bridges to adaptive behaviour were tested before the current
route was selected:

- A reversal-learning EEG endpoint failed its frozen confirmation gate. A
  subsequent synthetic audit showed that the original phase-departure metric
  could not distinguish genuine reconfiguration from ordinary oscillator drift.
  This was recorded as an instrument failure, not rewritten as a clean failure
  of the biological hypothesis.
- A redesigned short-horizon relative-phase predictor passed synthetic
  construct validation, but the available empirical regime remained too
  restrictive for the intended bridge.
- The current route uses public concurrent single-pulse TMS-fMRI
  ([OpenNeuro ds005498](https://doi.org/10.18112/openneuro.ds005498.v2.0.0)) to
  test whether independently estimated resting functional embedding predicts
  local susceptibility versus remote propagation.

Before inspecting processed TMS responses, the following were frozen and tested:

1. A 68-event first-level GLM with SPM HRF, 0.01 Hz high-pass filtering, motion
   derivatives, FD censoring and AR(1) empirical noise modeling.
2. A spatial instrument using the released stimulation sphere, a 10 mm
   near-field exclusion buffer and the TemplateFlow Schaefer-100 atlas in the
   exact MNI152NLin2009cAsym grid.
3. Resting positive, negative, total-absolute and mixed-sign functional
   embedding, with mandatory global-signal-regression sensitivity analysis.

The final participant gate applied that frozen analysis to all 11 stimulation
sites in NTHC1035. Ten runs passed motion QC (R-IPL was flagged at 44/164
censored volumes), but none showed a detectable local or remote response at the
frozen remote `|mean z| >= 3.1` threshold; local means were also far below that
same conservative criterion. The resting-embedding association was
therefore not attempted: without a detected perturbational response, there was
no defensible propagation outcome to explain. This closes the empirical route
as an informative pilot failure rather than evidence against the biological
hypothesis.

The route-selection record and full frozen protocol are in
[`docs/EMPIRICAL_ROUTE_SELECTION.md`](docs/EMPIRICAL_ROUTE_SELECTION.md) and
[`docs/EMPIRICAL_TMS_FMRI_TRANSLATION_PROTOCOL.md`](docs/EMPIRICAL_TMS_FMRI_TRANSLATION_PROTOCOL.md).

## Repository structure

```text
src/luppi_recreation/   Reusable analysis and measurement code
scripts/                Reproduction, null-model and validation entry points
tests/                  Mathematical and regression tests
configs/                Frozen experiment parameters and upstream provenance
docs/                   Protocols, results and empirical-route decisions
ui/                     Dependency-free interactive perturbation explorer
data/                   Local public datasets (ignored by Git)
results/                Regenerable numerical outputs (ignored by Git)
figures/                Regenerable figures (ignored by Git)
upstream/               External repositories pinned by commit (ignored by Git)
```

Raw public datasets, virtual environments, compiled binaries, preprocessing
work directories and software licences are intentionally excluded from Git.

## Installation

Requirements:

- Python 3.12 (development used 3.12.9)
- A C++ compiler
- Eigen headers (`brew install eigen` on macOS)
- Docker Desktop only for the empirical fMRI preprocessing stage

```bash
git clone https://github.com/Shriya-sai/competitive-connectomes-adaptive-dynamics.git
cd competitive-connectomes-adaptive-dynamics

python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

git clone https://github.com/Hana-Ali/competitive-cooperative-hopf.git \
  upstream/competitive-cooperative-hopf
git -C upstream/competitive-cooperative-hopf checkout \
  da592aab6784db5c6c59f29f6bcb2b3743f1afd7
git -C upstream/competitive-cooperative-hopf apply \
  ../../configs/upstream_compatibility.patch

cd upstream/competitive-cooperative-hopf
python cpp/build_hopf.py
cd ../..
```

The compatibility patch replaces removed Python `distutils` imports, exposes an
optional simulation seed while preserving the upstream default of 42, and adds
the paired perturbation interface used only by the extension experiments. See
[`configs/upstream_patch_notes.md`](configs/upstream_patch_notes.md).

## Verification and entry points

Run the complete automated suite:

```bash
python -m pytest -q
```

In a fresh clone, the three integration tests that require the separately
cloned demonstration data and compiled Hopf extension are reported as skipped.
After completing the upstream setup above, all 42 tests run.

Initial reproduction sequence:

```bash
python scripts/inspect_single_subject.py
python scripts/extract_single_subject_frequencies.py
python scripts/simulate_single_subject.py
python scripts/optimize_single_subject.py
python scripts/evaluate_frozen_gc.py
```

The repository contains separate scripts for each null model, dynamical
instrument, gain sweep, perturbation experiment and active empirical analysis.
Frozen parameters live in `configs/`; interpretive reports live in `docs/`.

## Interactive perturbation explorer

The repository includes a static browser interface for comparing the four
reference interaction architectures, stimulation targets, amplitudes and
durations. It ships with 128 frozen response profiles aggregated from the
paired 30-seed confirmation runs, so it works immediately after cloning:

```bash
python -m http.server 8000
```

Open `http://localhost:8000/ui/`. After reproducing the numerical analysis,
regenerate the interface dataset with:

```bash
python scripts/export_brain_dynamics_ui.py
```

The interface deliberately uses a schematic bilateral layout because the
released model does not provide atlas coordinates for this visualization. Its
playback is the actual paired intervention-minus-control trajectory from frozen
confirmation seed 300; the displayed summary metrics remain 30-seed medians.
See [`ui/README.md`](ui/README.md) for the exact provenance and limitations.

## Reproducibility principles

- Simulation seeds are repeated stochastic runs, never treated as biological
  sample size.
- Development and confirmation seeds or participants are separated where the
  data permit.
- Measurement instruments are tested on synthetic ground truth before empirical
  use.
- Failed gates remain documented and are not retuned after inspection.
- Negative functional correlation is not equated with direct anatomical
  inhibition.
- Generated outputs are excluded from version control; scripts, frozen configs,
  provenance and interpretive records are tracked.

## Current limitations

- Core reproduction results use one released human subject.
- Generative weights were jointly optimized; ablations demonstrate dependence
  within that solution, not uniqueness among all possible reoptimized models.
- The empirical TMS-fMRI route ended at its prespecified participant gate: no
  local or remote TMS response was detectable across the 10 motion-QC-passing
  sites, so no architecture–propagation association could be tested.
- No result currently establishes a causal link between cooperative–competitive
  whole-brain organization and human exploration–exploitation behaviour.

## Key documentation

- [`PROJECT_OUTLINE.md`](PROJECT_OUTLINE.md) — concise project roadmap
- [`docs/HOPF_ARCHITECTURAL_ALLOCATION_RESULTS.md`](docs/HOPF_ARCHITECTURAL_ALLOCATION_RESULTS.md) — final mechanistic result
- [`docs/EMPIRICAL_ROUTE_SELECTION.md`](docs/EMPIRICAL_ROUTE_SELECTION.md) — rejected routes and current empirical rationale
- [`configs/upstream_version.txt`](configs/upstream_version.txt) — exact upstream provenance

## Child NeuroAI project

The biological and dynamical results developed here motivate the separate
project **Competitive Architectures for Brain-Inspired Deep Learning**.
Its repository, [`competitive-architectures-neuroai`](https://github.com/Shriya-sai/competitive-architectures-neuroai),
tests whether controlled artificial analogues of structured competition improve
computation or brain alignment. The repositories remain independent so that the
translation does not blur the evidential boundary between whole-brain modeling
and DNN experiments.

## Licence

Project-authored code is released under the [MIT License](LICENSE). External
software, public datasets and the upstream Hopf implementation retain their own
licences and citation requirements. No raw participant data or FreeSurfer
licence file is distributed in this repository.

## Citation and attribution

This is an independent educational reproduction and extension, not an official
repository of the original authors. The Hopf simulator, optimizer and released
demonstration data originate from
[`Hana-Ali/competitive-cooperative-hopf`](https://github.com/Hana-Ali/competitive-cooperative-hopf)
at the pinned commit recorded above. Please cite Luppi et al. and the relevant
public datasets when reusing this work.
