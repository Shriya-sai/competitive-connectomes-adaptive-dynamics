# Hopf Architectural Allocation — Frozen Stage 3 Protocol

## Question

Given a fixed perturbational budget and target count, how does spatial allocation interact with cooperative–competitive network architecture to determine local response, propagation, phase reconfiguration, and recovery?

## Controlled comparison

Every intervention targets exactly ten regions. Every target receives absolute `delta_a = 0.003`, so total absolute budget is exactly `0.03`. Pulse duration, baseline, recovery, noise, and bifurcation settings remain unchanged. Positive and negative pulses are analyzed separately.

The experiment therefore changes *where* the budget is delivered without changing how many targets receive it or how much total input is supplied.

## Frozen architectural strategies

Nodes are ranked once using the fitted signed connectome, before simulations. Alternating ranks create A/B matched sets rather than letting one particular ten-node selection determine the result.

- absolute hubs: largest total absolute signed strength;
- cooperative-strength targets: largest positive strength;
- competitive-strength targets: largest absolute negative strength;
- mixed-sign targets: jointly high normalized positive and negative strength;
- peripheral targets: smallest total absolute strength;
- random control: seeded frozen random nodes.

These are connectivity-defined model categories, not named biological systems. Their sets remain fixed when gains are varied, preventing the outcome network from redefining its own targets.

## Outcomes and guardrails

Primary outcomes remain separate: targeted response, absolute untargeted propagation, total response energy, absolute cross-boundary and within-untargeted phase displacement, recovery time, and residual displacement.

The relative spatial-reach statistic, remote-phase fraction, and derived system-level label are retained only for audit compatibility and excluded from primary inference because Stage 2 exposed denominator effects.

Strategy is compared within gain, perturbation sign, A/B replicate, and stochastic seed. We will report whether strategy rankings change across cooperative–competitive gain regimes; no composite flexibility score and no overall “best target” are permitted.

Development uses seeds 600–604 and four diagnostic gain regimes (480 pairs). Confirmation uses untouched seeds 700–729 and all six gain regimes (4,320 pairs), released only after budget, target-count, paired-baseline, finite-output, and uncoupled-propagation gates pass.

This is the final planned mechanistic Hopf experiment. It can identify architecture-dependent response mechanisms, but cannot demonstrate adaptive behaviour. Its output must next be converted into a constrained empirical prediction.
