# Generality of the Hopf Response–Phase Dissociation — Stage 1 Results

## Decision

Under the frozen Stage 1 rule, the dissociation is **general across every already sampled perturbation family**: both pulse signs, both strengths, both durations, central and peripheral target pools, and matched A and B target sets passed. This conclusion is restricted to ten-region perturbations in the present fitted connectome.

## What “general” means here

Within every perturbation-family level, amplitude-qualified phase was not strongly reducible to either direct displacement or propagation:

| Factor level | Phase–displacement rho | Phase–propagation rho | Local/boundary localization support |
|---|---:|---:|---:|
| Negative pulse | 0.396 | 0.135 | 97.8% |
| Positive pulse | 0.387 | 0.139 | 97.8% |
| Weak `|delta_a| = 0.01` | 0.326 | 0.037 | 97.8% |
| Strong `|delta_a| = 0.03` | 0.327 | 0.039 | 97.8% |
| Brief 7.2 s | 0.351 | 0.088 | 100% |
| Sustained 28.8 s | 0.381 | 0.117 | 95.7% |
| Central target | 0.463 | 0.158 | 95.6% |
| Peripheral target | 0.331 | 0.131 | 100% |
| Matched set A | 0.391 | 0.188 | 95.6% |
| Matched set B | 0.397 | 0.083 | 100% |

All correlations remained below the prespecified strong-coupling threshold `|rho| = 0.8`. Eligible amplitude-qualified localization coverage ranged from 94.7% to 97.6%; insufficient edge-time cells were excluded rather than assigned values.

## Factor effects

The three measurements nevertheless responded coherently to intervention dose:

- Positive pulses produced larger mean displacement, propagation, and phase change than negative pulses; the seed-matched direction was positive for 30/30 seeds for displacement and propagation and 28/30 for phase.
- Strong pulses increased all three measures in 30/30 seeds.
- Sustained pulses increased all three measures in 30/30 seeds.

Target anatomy separated the measurements especially clearly:

- Peripheral targeting produced greater direct displacement and phase reconfiguration than central targeting in 30/30 seeds.
- Central targeting produced greater propagation outside the stimulated set than peripheral targeting in 30/30 seeds.

Thus a target may react strongly itself without transmitting the largest response to the rest of the network. Connectivity-defined centrality shapes local susceptibility and outward influence differently.

Matched A sites produced larger displacement and propagation than B sites in all thirty seed-level comparisons. Phase was also larger for A on average, but its direction was less uniform: B exceeded A in 10/30 seed-level averages. This further supports partial—not total—separation of phase organization from amplitude response.

## The important hierarchical qualification

Within fixed gain regimes, phase often correlated strongly with intervention magnitude:

| Gain regime | Phase–displacement rho | Phase–propagation rho |
|---|---:|---:|
| Uncoupled | 0.848 | undefined because propagation is always zero |
| Cooperative-only | 0.886 | 0.848 |
| Competitive-only | 0.886 | 0.721 |
| Fitted signed | 0.873 | 0.846 |
| Competition-dominant | 0.950 | 0.829 |
| Cooperation-dominant | 0.867 | 0.877 |

This is not a contradiction. Within one network, stronger and longer interventions tend to increase displacement, spread, and phase disruption together. Across networks with different cooperative–competitive balance, however, the mapping between those quantities changes substantially. The dissociation is therefore principally a **network-regime dissociation**, not a claim that phase is insensitive to perturbation dose.

The competition-dominant regime was also the localization exception: only 87.2% of eligible pairs showed local/boundary phase exceeding within-unperturbed phase, compared with approximately 100% in the other coupled regimes. This is consistent with its high-instability, poorly recovering dynamics and suggests more spatially diffuse relational disruption when competition outruns cooperative stabilization.

## Scientific conclusion

The defensible result is:

> Perturbation strength, duration, and sign scale amplitude and phase responses together within a fixed network, but cooperative–competitive regime and target anatomy determine how those response dimensions relate. The separation between local displacement, outward propagation, and relational phase reconfiguration generalizes across all sampled ten-region perturbation families.

This is stronger than saying the original panel was merely unusual, but narrower than claiming universal dynamical dissociation.

## What remains untested

- Focality: one, five, ten, or twenty perturbed regions.
- Constant-per-region versus constant-total perturbation dose.
- Named anatomical or functional brain systems.
- Additional connectomes or subjects.
- Alternative intervention mechanisms and baseline model parameters.

These limitations justify a separately frozen focality experiment as the next simulation stage.

## Outputs

- Factor-level summaries: `results/hopf_dissociation_generality/factor_level_summary.csv`
- Seed-matched contrasts: `results/hopf_dissociation_generality/paired_factor_contrasts.csv`
- Complete summary: `results/hopf_dissociation_generality/summary.json`
- Figure: `figures/hopf_dissociation_generality.png`
