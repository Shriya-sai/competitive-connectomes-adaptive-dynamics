# Target-Free Hopf Perturbation–Response Experiment — Frozen Protocol

## Status

Frozen before implementing the time-varying perturbation simulator or generating perturbation-response outcomes. This protocol replaces the rejected target-state A→B proposal. No target-state protocol was created or run.

## Scientific question

**How do cooperative and competitive coupling gains alter the magnitude, propagation, reconfiguration, persistence, and recovery of whole-network responses to matched exogenous perturbations?**

This experiment tests dynamical capacity. It does not model actions, rewards, contingency learning, or behavioural choice. Therefore its results may not be called exploration, exploitation, reversal learning, or behavioural adaptation.

## Why the task is target-free

The model is not assigned a desired post-perturbation state. It receives no reward and no connectivity update. A temporary intervention is applied and then removed; the response is observed rather than scored against a state chosen by the investigator.

Every intervention has a paired counterfactual control with the same connectivity, initial oscillator state, regional frequencies, integration schedule, and complete stochastic-noise sequence. The only difference is the temporary intervention. Consequently, intervention-minus-control trajectories isolate the causal response to the pulse from ordinary stochastic divergence.

## Frozen model

The 100-region fitted signed connectivity and regional frequencies in `results/single_subject_optimization/signed.npz` are fixed. For each gain condition:

`C(g_coop, g_comp) = g_coop * positive(C) + g_comp * negative(C)`.

Cooperative and competitive gains independently take 0, 0.5, 1.0, and 1.5 in a full 4 × 4 grid. Connectivity never changes within a trial. Noise is 0.001, the baseline bifurcation parameter is -0.02, and sampling remains at TR = 0.72 seconds.

## Required simulator extension

The existing `hopf.simulate()` supports only fixed parameters for an entire run. A minimal extension is therefore required. It must:

1. expose a temporary region-specific shift `delta_a` in the local bifurcation parameter;
2. preserve oscillator state across pre-pulse, pulse, and recovery periods;
3. allow control and intervention runs to begin from an identical post-burn-in state;
4. replay the identical random-noise sequence in both members of the pair; and
5. introduce no action, reward, target state, learning rule, or connectivity update.

This extension changes the experimental input, not the fitted network.

## Temporal design

- Discarded burn-in: 500 seconds.
- Recorded pre-perturbation baseline: 72 seconds.
- Pulse durations: 7.2 seconds and 28.8 seconds.
- Recorded recovery after pulse removal: 144 seconds.

A zero-amplitude pair must remain identical to numerical tolerance throughout. All nonzero pairs must be identical before pulse onset.

## Perturbations

The intervention temporarily adds `delta_a` to selected regions' local bifurcation parameters. Frozen amplitudes are -0.03, -0.01, +0.01, and +0.03. Positive and negative pulses are distinct experimental conditions and will not be collapsed.

Four ten-region site sets are determined without looking at response outcomes. Regions are ranked by the row sum of absolute fitted signed connectivity, with zero-based region index breaking ties. The twenty strongest regions form the central pool and the twenty weakest form the peripheral pool. Alternating ranked positions define matched A and B sets within each pool. Thus the experiment includes `central_A`, `central_B`, `peripheral_A`, and `peripheral_B`.

This selection tests whether conclusions generalize across paired sites and across connectivity strength. It does not claim that graph strength equals biological importance.

## Separate observables

No single adaptation score will be constructed.

1. **Direct response:** RMS intervention-minus-control signal displacement in perturbed regions during the pulse.
2. **Propagation:** corresponding displacement outside the perturbed regions.
3. **Propagation fraction:** outside-region displacement divided by total displacement.
4. **Phase reconfiguration:** intervention-versus-control distance between pairwise relative-phase patterns.
5. **Recovery time:** after pulse removal, the first point at which smoothed total displacement falls below 5% of that pair's peak pulse response and remains there for 14.4 seconds. A response not meeting this criterion is right-censored at the end of recovery rather than silently called recovered.
6. **Residual displacement:** mean total displacement during the final 28.8 seconds.
7. **Response reliability:** cross-seed similarity of regional response-amplitude profiles.
8. **Unperturbed stability:** variability of the control trajectory, reported separately so apparent responsiveness is not confused with baseline instability.

Correlation-matrix reconfiguration is exploratory rather than primary. The brief pulse contains only ten BOLD samples, so FC during the pulse alone would be badly underdetermined. A shrinkage correlation distance may be calculated over a fixed 28.8-second interval beginning at pulse onset, but it cannot determine the primary conclusion.

Metrics are descriptive axes. Higher responsiveness, wider propagation, faster recovery, and lower residual displacement are not automatically treated as universally better.

## Pareto analysis

The gain grid may be described using a Pareto frontier across stability, response, propagation, recovery, residual displacement, and reliability. This is not a disguised composite score. A condition is nondominated only relative to explicitly oriented dimensions; the complete component values must remain visible, and alternative scientific orientations must be discussed.

No weighted composite, overall winner, or post-hoc ranking is permitted.

## Development and confirmation separation

Seeds 200–204 are development seeds used only to check simulator correctness and metric sensitivity. Development uses four reference gain conditions—uncoupled, cooperative-only, competitive-only, and fitted signed—across every site, amplitude, and duration, giving 640 paired interventions. Seeds 300–329 are untouched confirmation seeds. Confirmation uses the complete frozen factorial design, giving 15,360 paired interventions, and may begin only after the development instrument gate passes.

The gate requires:

- exact paired identity before pulse onset to tolerance `1e-10`;
- exact zero-pulse identity throughout to tolerance `1e-10`;
- no NaN or infinite outputs;
- direct response increasing with absolute pulse magnitude in at least 80% of development cells; and
- a site-permutation check showing that perturbed-versus-unperturbed labels are handled correctly.

Passing this gate validates the experimental instrument, not the cooperation–competition hypothesis.

## Scope of any eventual conclusion

A successful experiment may show that cooperative and competitive gains shape perturbation-response dynamics or reveal a stability–flexibility trade-off in this fitted whole-brain model. It cannot demonstrate learning, behavioural adaptation, exploration, or exploitation. Connecting these dynamical properties to behaviour requires a separately justified model or independent empirical data.

## Stopping rules

- Do not tune pulse parameters to make balanced gains win.
- Do not collapse conflicting dimensions into a preferred weighted score.
- If the instrument gate fails, repair the implementation or version the protocol before touching confirmation seeds.
- If no trade-off appears, record the null result.
