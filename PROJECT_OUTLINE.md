# Project roadmap

## Scientific question

How do the signs, strengths and anatomical placement of cooperative and
competitive effective interactions shape whole-brain dynamics and responses to
localized perturbation?

## Stage 1 — computational reproduction: complete

- Rebuilt the released C++ Hopf implementation for Python 3.12.
- Reimplemented regional-frequency extraction without MATLAB.
- Reproduced the released single-subject cooperative and signed fits.
- Froze upstream provenance, compatibility changes and automated regression
  tests.

## Stage 2 — organization and dynamics: complete

- Compared signed and cooperative-only simulations across matched seeds.
- Tested whole-weight placement, sign-specific strength and fixed-magnitude
  sign-map null models.
- Measured synchrony, metastability and continuous LEiDA landscape geometry.
- Established the bounded result that both cooperative and competitive
  organization contribute location-specific information in the fitted model.

## Stage 3 — perturbation response: complete

- Built and synthetically validated an exactly paired perturbation instrument.
- Varied cooperative/competitive gain, perturbation sign, magnitude, duration,
  focality and anatomical target.
- Separated direct susceptibility, outward propagation, relative-phase
  reconfiguration and recovery.
- Tested allocation under fixed target count and perturbational budget.
- Added a reproducible browser explorer with literal model-trajectory playback.

## Stage 4 — empirical translation: in progress

The current public-data test uses concurrent TMS-fMRI from OpenNeuro
`ds005498`. Resting functional embedding is estimated independently and tested
against TMS-evoked local response and remote propagation. The GLM, spatial
instrument, nuisance handling and quality-control rules were frozen before
multisite outcomes were inspected.

This stage ends when:

1. the standardized preprocessing sensitivity analysis is complete;
2. every eligible stimulation site has passed or failed frozen QC;
3. the architecture–response association is reported, including a null result;
4. claims remain restricted to perturbation dynamics rather than learning or
   exploration–exploitation behaviour.

See [`docs/EMPIRICAL_ROUTE_SELECTION.md`](docs/EMPIRICAL_ROUTE_SELECTION.md)
for rejected empirical routes and
[`docs/EMPIRICAL_TMS_FMRI_TRANSLATION_PROTOCOL.md`](docs/EMPIRICAL_TMS_FMRI_TRANSLATION_PROTOCOL.md)
for the active protocol.

## Stage 5 — release and extension

- Keep code, frozen configurations, tests and provenance public.
- Keep participant data, software licences and generated preprocessing outputs
  outside Git.
- Complete the empirical result before expanding the biological claim.
- Develop artificial-network analogues in the separate
  [`competitive-architectures-neuroai`](https://github.com/Shriya-sai/competitive-architectures-neuroai)
  repository so whole-brain and DNN evidence remain distinct.
