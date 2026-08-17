"""Estimate each region's characteristic BOLD oscillation frequency."""

import numpy as np
from numpy.typing import NDArray
from scipy.signal import butter, convolve, detrend, filtfilt


FloatArray = NDArray[np.float64]


def _gaussian_smooth_uniform(
    coordinates: FloatArray,
    values: FloatArray,
    sigma: float,
) -> FloatArray:
    """Reproduce the uniform-spacing branch of upstream ``gaussfilt.m``."""

    if coordinates.ndim != 1 or values.ndim != 1:
        raise ValueError("Coordinates and values must be one-dimensional")
    if coordinates.size != values.size:
        raise ValueError("Coordinates and values must have equal length")
    if coordinates.size < 2:
        raise ValueError("At least two coordinate values are required")
    if sigma <= 0:
        raise ValueError("Gaussian sigma must be positive")

    spacing = np.diff(coordinates)
    if not np.allclose(spacing, spacing[0], rtol=1e-4, atol=0.0):
        raise ValueError("This implementation requires uniformly spaced coordinates")

    step = spacing[0]
    amplitude = 1.0 / (np.sqrt(2.0 * np.pi) * sigma)
    kernel = step * amplitude * np.exp(
        -0.5 * ((coordinates - np.mean(coordinates)) ** 2) / (sigma**2)
    )
    kernel = kernel[kernel >= step * amplitude * 1e-6]
    # MATLAB's conv(z, filter, 'same') starts one sample later than SciPy's
    # mode='same' when the filter length is even. Slice the full convolution
    # explicitly to preserve the upstream MATLAB alignment.
    full_convolution = convolve(values, kernel, mode="full", method="direct")
    start = kernel.size // 2
    return full_convolution[start : start + values.size]


def extract_regional_frequencies(
    bold: FloatArray,
    repetition_time: float,
    filter_low: float = 0.008,
    filter_high: float = 0.09,
    smoothing_sigma: float = 0.01,
) -> FloatArray:
    """Return the strongest slow BOLD frequency for every region.

    This is a Python translation of the upstream MATLAB function
    ``fcn_extract_frequencies.m`` for a single subject.

    Parameters
    ----------
    bold:
        Matrix with shape ``(regions, timepoints)``.
    repetition_time:
        Seconds between consecutive fMRI measurements (TR).
    filter_low, filter_high:
        Bounds of the slow-frequency band in hertz.
    smoothing_sigma:
        Standard deviation, in hertz, of Gaussian power-spectrum smoothing.
    """

    bold = np.asarray(bold, dtype=np.float64)
    if bold.ndim != 2:
        raise ValueError("BOLD data must have shape (regions, timepoints)")
    if bold.shape[1] < 10:
        raise ValueError("BOLD data contains too few timepoints")
    if not np.isfinite(bold).all():
        raise ValueError("BOLD data contains non-finite values")
    if repetition_time <= 0:
        raise ValueError("Repetition time must be positive")

    nyquist = 1.0 / (2.0 * repetition_time)
    if not 0 < filter_low < filter_high < nyquist:
        raise ValueError(
            "Frequency bounds must satisfy 0 < low < high < Nyquist frequency"
        )

    # MATLAB: butter(2, [low/fnq, high/fnq]) followed by filtfilt.
    numerator, denominator = butter(
        2,
        [filter_low, filter_high],
        btype="bandpass",
        fs=1.0 / repetition_time,
    )

    centered = bold - np.mean(bold, axis=1, keepdims=True)
    detrended = detrend(centered, axis=1, type="linear")
    # MATLAB filtfilt reflects 3 * (max(filter lengths) - 1) samples at each
    # boundary. SciPy's newer default is three samples longer, which changes
    # the selected peak for spectra with closely competing maxima.
    matlab_pad_length = 3 * (max(numerator.size, denominator.size) - 1)
    filtered = filtfilt(
        numerator,
        denominator,
        detrended,
        axis=1,
        padlen=matlab_pad_length,
    )

    n_timepoints = bold.shape[1]
    n_frequencies = n_timepoints // 2
    frequencies = np.arange(n_frequencies, dtype=np.float64) / (
        n_timepoints * repetition_time
    )

    fourier_amplitude = np.abs(np.fft.fft(filtered, axis=1))[:, :n_frequencies]
    power = (fourier_amplitude**2) / (n_timepoints / repetition_time)

    smoothed_power = np.empty_like(power)
    for region in range(bold.shape[0]):
        smoothed_power[region] = _gaussian_smooth_uniform(
            frequencies,
            power[region],
            smoothing_sigma,
        )

    peak_indices = np.argmax(smoothed_power, axis=1)
    regional_frequencies = frequencies[peak_indices]

    zero_mask = regional_frequencies == 0
    if np.any(zero_mask):
        nonzero = regional_frequencies[~zero_mask]
        if nonzero.size == 0:
            raise ValueError("All estimated regional frequencies are zero")
        regional_frequencies[zero_mask] = np.mean(nonzero)

    return regional_frequencies
