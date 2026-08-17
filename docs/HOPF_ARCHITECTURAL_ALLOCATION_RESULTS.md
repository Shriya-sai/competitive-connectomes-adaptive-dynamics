# Hopf Architectural Allocation — Stage 3 Results

## Question

Given a fixed perturbational budget and target count, how does spatial allocation interact with cooperative–competitive network architecture to determine local response, propagation, phase reconfiguration, and recovery?

## Execution

- Every intervention targeted 10 regions with total absolute budget 0.03.
- Six frozen allocation strategies were tested using matched A/B node sets.
- Development: 480 paired simulations; every instrument gate passed.
- Confirmation: 4,320 paired simulations across six gain regimes, two signs, two target-set replicates, and 30 untouched seeds.

## Main result: susceptibility and influence are different

No allocation was uniformly strongest across outcomes or gain regimes.

Peripheral targets frequently showed the largest targeted response and cross-boundary phase displacement in cooperative-only, fitted-signed, and cooperation-dominant systems. This is consistent with lower architectural constraint making peripheral nodes locally susceptible. It does **not** mean that peripheral targets were the strongest amplitude broadcasters.

Competitive-strength and mixed-sign targets produced the largest absolute outward propagation when competitive coupling was active:

- competitive-only: competitive-strength targets had the largest propagation (about 1.34e-4), closely followed by mixed-sign targets;
- fitted signed: competitive-strength targets had the largest propagation (about 3.96e-6) and within-untargeted phase displacement;
- competition-dominant: competitive-strength targets again had the largest propagation (about 3.16e-4), followed by mixed-sign targets.

When only cooperative coupling was active, peripheral targets produced the largest propagation, but the absolute effects were much smaller (about 1.58e-6). Thus competitive architecture did not merely amplify all targets equally: it made allocations aligned with negative and mixed-sign strength disproportionately influential.

## Architecture-by-gain interaction

The same frozen target sets changed rank when the gain regime changed. This is the critical interaction:

- competitive-strength placement became highly influential when competitive edges were active;
- peripheral placement remained locally and phase susceptible across several regimes;
- absolute hubs were not universal winners;
- cooperative-strength targets often showed relatively small cross-boundary phase response, despite their large positive structural strength.

Therefore, node architecture alone is insufficient. A target's dynamical role depends on which signed pathways are active in the network containing it.

## Reproducibility and limitations

Median A/B rank reliability across the six strategies was:

- targeted response: rho = 0.77;
- propagation: rho = 0.66;
- total response energy: rho = 0.60;
- cross-boundary phase: rho = 0.54;
- recovery: rho = 0.67;
- within-untargeted phase and residual displacement: rho = 0.14.

Local response and propagation rankings therefore generalized moderately across matched target sets. Fine-grained remote phase and residual rankings were poorly reproducible and should not support strategy-specific claims.

The architectural categories overlap because hubness, positive strength, negative strength, and mixed-sign strength are correlated properties of the same fitted connectome. The experiment tests reproducible allocation profiles; it does not prove isolated causal effects of mutually exclusive node classes. It also uses one fitted connectome and one perturbation budget.

Relative spatial-reach and remote-fraction measures were excluded from primary inference as frozen, because Stage 2 demonstrated denominator sensitivity.

## Conclusion

With target count and total perturbational budget fixed, spatial allocation materially changes the response. The result is not a simple hub advantage. Weakly embedded regions can be locally susceptible, whereas negative-strength and mixed-sign regions can be stronger broadcasters when competitive pathways are active.

This supports the mechanistic proposition that cooperative and competitive architecture jointly determine how an input is converted into local displacement, remote propagation, and relational reconfiguration. It still does not demonstrate adaptive behaviour.

This completes the planned Hopf mechanistic sequence. The next step is to convert the robust result into a constrained empirical prediction rather than add another unconstrained model sweep.
