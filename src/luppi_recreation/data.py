"""Load and validate the released demonstration data."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.io import loadmat


FloatMatrix = NDArray[np.float64]


@dataclass(frozen=True)
class SingleSubjectData:
    """Structural connectivity and regional BOLD signals for one subject."""

    structural_connectivity: FloatMatrix
    bold: FloatMatrix

    @property
    def n_regions(self) -> int:
        return self.bold.shape[0]

    @property
    def n_timepoints(self) -> int:
        return self.bold.shape[1]


def load_single_subject(data_directory: str | Path) -> SingleSubjectData:
    """Load the upstream single-subject matrices and validate their layout.

    Expected files and variables:
    - ``SC.mat`` containing ``SC`` with shape ``(regions, regions)``
    - ``FMRI.mat`` containing ``FMRI`` with shape ``(regions, timepoints)``
    """

    data_directory = Path(data_directory)
    sc_path = data_directory / "SC.mat"
    fmri_path = data_directory / "FMRI.mat"

    if not sc_path.is_file():
        raise FileNotFoundError(f"Structural-connectivity file not found: {sc_path}")
    if not fmri_path.is_file():
        raise FileNotFoundError(f"BOLD file not found: {fmri_path}")

    sc_contents = loadmat(sc_path)
    fmri_contents = loadmat(fmri_path)

    if "SC" not in sc_contents:
        raise KeyError(f"Expected variable 'SC' in {sc_path}")
    if "FMRI" not in fmri_contents:
        raise KeyError(f"Expected variable 'FMRI' in {fmri_path}")

    structural_connectivity = np.asarray(sc_contents["SC"], dtype=np.float64)
    bold = np.asarray(fmri_contents["FMRI"], dtype=np.float64)

    if structural_connectivity.ndim != 2:
        raise ValueError("Structural connectivity must be a two-dimensional matrix")
    if bold.ndim != 2:
        raise ValueError("BOLD data must be a two-dimensional matrix")
    if structural_connectivity.shape[0] != structural_connectivity.shape[1]:
        raise ValueError("Structural connectivity must be square")
    if structural_connectivity.shape[0] != bold.shape[0]:
        raise ValueError("SC and BOLD must contain the same number of regions")
    if not np.isfinite(structural_connectivity).all():
        raise ValueError("Structural connectivity contains non-finite values")
    if not np.isfinite(bold).all():
        raise ValueError("BOLD data contains non-finite values")

    return SingleSubjectData(
        structural_connectivity=structural_connectivity,
        bold=bold,
    )
