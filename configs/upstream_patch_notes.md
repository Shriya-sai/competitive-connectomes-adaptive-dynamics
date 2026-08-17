# Upstream compatibility patches

## Python 3.12 build compatibility

- File: `upstream/competitive-cooperative-hopf/cpp/build_hopf.py`
- Upstream commit: `da592aab6784db5c6c59f29f6bcb2b3743f1afd7`
- Change: replaced `from distutils.core import setup, Extension` with `from setuptools import setup, Extension`.
- Reason: Python 3.12 removed `distutils` from the standard library, although the upstream README requires Python 3.12. `setuptools` is the maintained provider of these build interfaces.
- Scientific impact: none; this changes only extension compilation, not Hopf simulation or optimization code.

## Optional simulation seed

- Files: `cpp/hopf_config.hpp`, `cpp/hopf_simulation.hpp`, and `cpp/hopf_python_interface.cpp`
- Change: exposed an optional unsigned random seed for `hopf.simulate()`.
- Default behavior: unchanged; omitting the argument still uses upstream seed `42`.
- Reason: the upstream simulator hard-codes seed 42, so repeated simulations of a frozen GC are identical. Seed control is required to estimate stochastic forward-simulation variability and construct fair null distributions.
- Scientific impact: this is an experimental extension. Reproduction runs retain seed 42; uncertainty analyses must record all seeds explicitly.

## Paired perturbation simulator

- Files: `cpp/hopf_simulation.hpp` and `cpp/hopf_python_interface.cpp`
- Change: added a segment-wise local bifurcation-parameter shift and a Python
  entry point returning matched control/intervention trajectories initialized
  from the same post-burn-in state and driven by identical stochastic noise.
- Reason: perturbational effects must be distinguished from ordinary divergence
  between independently simulated noisy trajectories.
- Scientific impact: this is a project-specific experimental extension and is
  not part of the Luppi et al. reproduction.

The machine-applicable patch is stored in `configs/upstream_compatibility.patch`.
