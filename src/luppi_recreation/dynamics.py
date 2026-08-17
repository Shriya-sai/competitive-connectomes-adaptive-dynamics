"""Phase-based measurements of whole-brain network dynamics."""

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, detrend, filtfilt, hilbert


@dataclass(frozen=True)
class PhaseDynamics:
    """Phase-based summary of regional time series."""

    phases: np.ndarray
    order_parameter: np.ndarray
    synchrony: float
    maximum_synchrony: float
    metastability: float


def bandpass_signals(
    signals: np.ndarray,
    repetition_time: float,
    filter_low: float = 0.008,
    filter_high: float = 0.09,
    order: int = 2,
) -> np.ndarray:
    """Detrend and zero-phase bandpass-filter region-by-time signals.

    Defaults reproduce the human-data frequency band and Butterworth order
    documented by Luppi et al. and their released Hopf preprocessing code.
    """

    signals = np.asarray(signals, dtype=np.float64)
    if signals.ndim != 2 or signals.shape[1] < 20:
        raise ValueError("signals must have shape (regions, at least 20 timepoints)")
    if not np.all(np.isfinite(signals)):
        raise ValueError("signals must contain only finite values")
    if repetition_time <= 0:
        raise ValueError("repetition_time must be positive")
    if not isinstance(order, int) or order < 1:
        raise ValueError("order must be a positive integer")
    nyquist = 1 / (2 * repetition_time)
    if not 0 < filter_low < filter_high < nyquist:
        raise ValueError("filter bounds must satisfy 0 < low < high < Nyquist")

    numerator, denominator = butter(
        order,
        [filter_low, filter_high],
        btype="bandpass",
        fs=1 / repetition_time,
    )
    matlab_pad_length = 3 * (max(numerator.size, denominator.size) - 1)
    centered = signals - np.mean(signals, axis=1, keepdims=True)
    detrended = detrend(centered, axis=1, type="linear")
    return filtfilt(
        numerator,
        denominator,
        detrended,
        axis=1,
        padlen=matlab_pad_length,
    )


def instantaneous_phase(signals: np.ndarray) -> np.ndarray:
    """Return Hilbert instantaneous phase for region-by-time signals.

    The input should be narrow-band and have shape ``(regions, timepoints)``.
    Phase is returned in radians in the interval ``[-pi, pi]``.
    """

    signals = np.asarray(signals, dtype=np.float64)
    if signals.ndim != 2:
        raise ValueError("signals must have shape (regions, timepoints)")
    if signals.shape[0] < 2 or signals.shape[1] < 3:
        raise ValueError("signals require at least 2 regions and 3 timepoints")
    if not np.all(np.isfinite(signals)):
        raise ValueError("signals must contain only finite values")
    if np.any(np.std(signals, axis=1) == 0):
        raise ValueError("every regional signal must vary over time")
    return np.angle(hilbert(signals, axis=1))


def kuramoto_order_parameter(phases: np.ndarray) -> np.ndarray:
    """Calculate global phase coherence at every timepoint.

    Zero means maximally dispersed phases and one means perfect alignment.
    """

    phases = np.asarray(phases, dtype=np.float64)
    if phases.ndim != 2:
        raise ValueError("phases must have shape (regions, timepoints)")
    if phases.shape[0] < 2 or phases.shape[1] < 1:
        raise ValueError("phases require at least 2 regions and 1 timepoint")
    if not np.all(np.isfinite(phases)):
        raise ValueError("phases must contain only finite values")
    return np.abs(np.mean(np.exp(1j * phases), axis=0))


def summarize_order_parameter(
    order_parameter: np.ndarray,
) -> tuple[float, float, float]:
    """Return mean synchrony, maximum synchrony and metastability."""

    order_parameter = np.asarray(order_parameter, dtype=np.float64)
    if order_parameter.ndim != 1 or order_parameter.size < 2:
        raise ValueError("order_parameter must be a one-dimensional time series")
    if not np.all(np.isfinite(order_parameter)):
        raise ValueError("order_parameter must contain only finite values")
    tolerance = 1e-12
    if np.any(order_parameter < -tolerance) or np.any(order_parameter > 1 + tolerance):
        raise ValueError("order_parameter values must lie between zero and one")
    return (
        float(np.mean(order_parameter)),
        float(np.max(order_parameter)),
        float(np.std(order_parameter, ddof=0)),
    )


def phase_dynamics(signals: np.ndarray, *, trim: int = 0) -> PhaseDynamics:
    """Calculate phase, Kuramoto coherence, synchrony and metastability.

    ``trim`` removes that many samples from both ends before summarization,
    which can reduce Hilbert-transform boundary effects. The full phase and
    order-parameter arrays are retained in the returned result.
    """

    if not isinstance(trim, int) or trim < 0:
        raise ValueError("trim must be a non-negative integer")
    phases = instantaneous_phase(signals)
    order_parameter = kuramoto_order_parameter(phases)
    if 2 * trim >= order_parameter.size - 1:
        raise ValueError("trim removes too many timepoints")
    summary_values = order_parameter[trim:-trim] if trim else order_parameter
    synchrony, maximum_synchrony, metastability = summarize_order_parameter(
        summary_values
    )
    return PhaseDynamics(
        phases, order_parameter, synchrony, maximum_synchrony, metastability
    )
