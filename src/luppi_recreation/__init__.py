"""Python tools for the Luppi et al. computational reproduction."""

from .data import SingleSubjectData, load_single_subject
from .dynamics import (
    PhaseDynamics,
    bandpass_signals,
    instantaneous_phase,
    kuramoto_order_parameter,
    phase_dynamics,
    summarize_order_parameter,
)
from .frequencies import extract_regional_frequencies
from .hopf_backend import load_hopf_extension
from .leida import (
    LeadingEigenvectorDynamics,
    LeidaLandscape,
    cluster_projective_states,
    leading_phase_eigenvectors,
    leida,
    projective_angular_distances,
    summarize_leida_landscape,
)
from .recurrent_states import (
    WindowedConnectivity,
    adjusted_rand_index,
    cluster_connectivity_states,
    windowed_functional_connectivity,
)

__all__ = [
    "SingleSubjectData",
    "PhaseDynamics",
    "bandpass_signals",
    "extract_regional_frequencies",
    "instantaneous_phase",
    "kuramoto_order_parameter",
    "load_hopf_extension",
    "load_single_subject",
    "phase_dynamics",
    "summarize_order_parameter",
    "WindowedConnectivity",
    "adjusted_rand_index",
    "cluster_connectivity_states",
    "windowed_functional_connectivity",
    "LeadingEigenvectorDynamics",
    "leading_phase_eigenvectors",
    "leida",
    "cluster_projective_states",
    "LeidaLandscape",
    "projective_angular_distances",
    "summarize_leida_landscape",
]
