# Empirical route selection

## Purpose

The computational experiments establish how a fitted cooperative–competitive
Hopf network responds to perturbation. They do not by themselves connect that
response to human adaptive behaviour. Several public-data routes were therefore
tested before the current empirical design was selected.

This document preserves the consequential decisions and negative results. The
detailed pilot notebooks, download utilities and abandoned analysis pipelines
were removed from the public tree to keep the repository focused; they remain
available in Git history.

## Reversal-learning fMRI

Wang et al. provide an excellent 32-participant behavioural reversal-learning
dataset and participant-level fMRI derivatives, but not continuous task BOLD or
participant-specific diffusion connectomes. The behavioural reconstruction was
feasible and reproduced the expected collapse and recovery around reversal.
The released neural derivatives could not support the continuous whole-brain
dynamical analysis required here.

OpenNeuro `ds000052` contains continuous task fMRI, but reversed contingencies
occur in later blocks. Reversal is therefore confounded with run order,
practice, fatigue and scanner drift. Its 13 participants also lack compatible
resting fMRI and diffusion connectivity. It was rejected as a primary test.

## Reversal-learning EEG

OpenNeuro `ds004295` offered trial-resolved reversal behaviour and 66-channel
EEG. A frozen three-participant confirmation tested whether theta phase-pattern
reconfiguration increased during early updating relative to stable trials. The
gate failed: one participant had insufficient trials and the two evaluable
participants showed opposite directions.

A subsequent synthetic audit identified an instrument problem. Ordinary phase
drift caused by regional frequency heterogeneity pushed the nominal null close
to the empirical values, leaving little useful dynamic range. A redesigned
short-horizon phase predictor passed synthetic tests but failed a second frozen
technical confirmation: stable empirical prediction error was already near its
maximum, and the broader covariance endpoint did not support the prediction.

These results do not reject a biological relationship between network
organization and adaptive behaviour. They show that the available scalp-EEG
regime and tested phase instruments could not provide a credible measurement of
the proposed construct. The stopping rule was therefore activated rather than
searching additional metrics post hoc.

## Selected route: concurrent TMS-fMRI

The current empirical route uses OpenNeuro `ds005498`. It asks a narrower,
mechanistically aligned question:

> Does independently estimated resting functional embedding predict whether a
> focal perturbation remains local or propagates through the network?

This does not test reversal learning, exploration or exploitation. It tests the
architecture-to-perturbation bridge that must be established before making any
behavioural claim. The frozen analysis, quality-control rules and limitations
are specified in
[`EMPIRICAL_TMS_FMRI_TRANSLATION_PROTOCOL.md`](EMPIRICAL_TMS_FMRI_TRANSLATION_PROTOCOL.md).

## Evidential boundary

- Simulation seeds are not biological participants.
- Effective negative weights are not automatically inhibitory synapses.
- Cross-dataset agreement is convergent evidence, not within-person causation.
- A successful TMS-fMRI result would validate an architecture–response
  relationship, not adaptive behaviour.

## Sources

- Luppi et al.: https://doi.org/10.1038/s41593-026-02205-3
- Wang et al.: https://www.nature.com/articles/s41467-025-63995-x
- OpenNeuro `ds000052`: https://openneuro.org/datasets/ds000052
- OpenNeuro `ds004295`: https://openneuro.org/datasets/ds004295
- OpenNeuro `ds005498`: https://doi.org/10.18112/openneuro.ds005498.v2.0.0
