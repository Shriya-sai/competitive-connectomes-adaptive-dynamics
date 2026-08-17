# Target-Free Hopf Perturbation–Response Experiment — Results

## Status

Completed under frozen protocol version 1.0.0. The five development seeds passed the instrument gate before any confirmation seed was simulated. The final confirmation set contains 15,360 paired interventions across 16 gain conditions, four sites, four signed amplitudes, two durations, and 30 independent seeds. All trajectories were finite.

## Instrument validation

Control and intervention trajectories were exactly identical before pulse onset. Zero-amplitude pairs remained exactly identical throughout. Direct response increased with absolute pulse magnitude in 100% of the prespecified development cells, exceeding the 80% gate. The genuine disjoint site-label test passed. The instrument therefore isolates the perturbation causally under identical state and noise.

## Main result

Cooperative and competitive gains strongly and differently shaped perturbation response. The result was not a single optimum and did not show that balanced gains simply “win.”

Across all matched perturbations and seeds:

- Cooperative gain was strongly associated with lower unperturbed instability (`Spearman rho = -0.856`), smaller direct response (`rho = -0.703`), faster recovery (`rho = -0.496`), and lower residual displacement (`rho = -0.626`).
- Competitive gain was associated with greater unperturbed instability (`rho = +0.468`), larger direct response (`rho = +0.424`), wider absolute propagation (`rho = +0.608`), slower recovery (`rho = +0.483`), and greater residual displacement (`rho = +0.509`).
- Cooperative gain increased the *fraction* of the response expressed outside the stimulated regions (`rho = +0.633`) even while reducing its absolute magnitude. Thus absolute propagation and proportional distribution are not interchangeable.

These are descriptive associations over the complete factorial dataset, not independent biological-subject statistics.

## Representative conditions

| Gains `(cooperative, competitive)` | Control instability | Direct response | Propagation | Median recovery | Censored | Residual |
|---|---:|---:|---:|---:|---:|---:|
| `(0, 1)` competitive-only | 0.12614 | 0.008595 | 0.000395 | 144.0 s | 100% | 0.000802 |
| `(1, 0)` cooperative-only | 0.001315 | 0.0000525 | 0.00000622 | 86.4 s | 1.4% | 3.91e-07 |
| `(1, 1)` fitted signed | 0.001577 | 0.0000750 | 0.00000937 | 101.5 s | 9.7% | 9.88e-07 |
| `(1.5, 1)` cooperation-dominant signed | 0.001229 | 0.0000465 | 0.00000696 | 91.4 s | 4.2% | 4.16e-07 |
| `(1, 1.5)` competition-dominant signed | 0.05841 | 0.003732 | 0.000537 | 144.0 s | 100% | 0.000452 |

The fitted signed network responded somewhat more strongly and propagated more than the cooperative-only network, but recovered more slowly and retained more residual displacement. When competition became substantially stronger than cooperation, the system entered a qualitatively high-instability, nonrecovering regime. Increasing cooperation relative to competition restored control stability and recovery but also suppressed absolute response.

## Reliability

Median leave-one-seed-out regional-profile reliability ranged from 0.852 to 0.999 across gain conditions. Therefore the spatial response patterns were generally reproducible even when the absolute response was small. Reliability itself did not identify a universally preferred gain condition.

## Pareto result

Under the declared orientation—lower instability, higher response, higher propagation, faster recovery, lower residual, and higher reliability—all 16 conditions were nondominated. This means each retained at least one advantage that prevented another condition from being unambiguously superior across all six dimensions.

This is scientifically informative. A unique “best balance” cannot be obtained without specifying how much responsiveness should be traded against stability and recovery. Assigning those weights would introduce a normative objective not supplied by this target-free experiment. No composite score or winner was therefore constructed.

## Interpretation

The experiment supports the bounded claim that cooperative and competitive interactions jointly shape distinct dimensions of perturbation-response dynamics:

- competition increases sensitivity and absolute spread but can destabilize the background and prevent recovery;
- cooperation stabilizes and contains dynamics, improves recovery, and can distribute a smaller response proportionally across the network;
- jointly signed regimes interpolate between these properties, with sharp instability appearing when competition outruns cooperative stabilization.

This supplies mathematical evidence for a stability–flexibility tension. It does not show learning, action selection, exploration, exploitation, or behavioural adaptation. The model has still not chosen or learned anything.

## Important limitations

1. Results concern one fitted 100-region connectome, not a human population.
2. The intervention is a temporary local bifurcation shift, one of many possible perturbation mechanisms.
3. Recovery is right-censored at 144 seconds; conditions with 100% censoring are known only not to have recovered within the observation window.
4. The broad Pareto set reflects genuine dimensional conflict but also means this experiment alone cannot define an optimal operating point.
5. Phase reconfiguration showed relatively weak monotonic gain associations and must not be treated as the dominant result.

## Outputs

- Development gate: `results/hopf_perturbation_response/development/instrument_gate.json`
- Development pairs: `results/hopf_perturbation_response/development/development_pairs.csv`
- Confirmation pairs: `results/hopf_perturbation_response/confirmation/confirmation_pairs.csv`
- Regional profiles: `results/hopf_perturbation_response/confirmation/regional_response_profiles.npz`
- Gain summary: `results/hopf_perturbation_response/analysis/gain_summary.csv`
- Analysis summary: `results/hopf_perturbation_response/analysis/summary.json`
- Figure: `figures/hopf_perturbation_response_confirmation.png`
