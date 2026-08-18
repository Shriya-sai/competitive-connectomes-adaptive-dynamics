#!/usr/bin/env python3
"""Estimate signed Schaefer-100 embedding from the AFNI resting pilot."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import nibabel as nib
import numpy as np
from nibabel.processing import resample_from_to
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from luppi_recreation.functional_embedding import (
    parcel_functional_connectivity,
    select_stimulation_parcel,
    summarize_functional_embedding,
)


RESULTS = ROOT / "results/empirical_tms_fmri_translation/afni/rest_sub-NTHC1035"
AFNI = RESULTS / "NTHC1035_rest.results"
ATLAS = (
    ROOT
    / "data/atlases/templateflow/tpl-MNI152NLin2009cAsym"
    / "tpl-MNI152NLin2009cAsym_res-02_atlas-Schaefer2018_"
    "desc-100Parcels7Networks_dseg.nii.gz"
)
SPHERE = ROOT / "upstream/sptmsfmri/data/stim-sites/R-preSMA_Sphere_Bin.nii.gz"
COVERAGE_THRESHOLD = 0.80


def main() -> None:
    residual_image = nib.load(AFNI / "errts.NTHC1035_rest.tproject+tlrc.HEAD")
    target_grid = (residual_image.shape[:3], residual_image.affine)
    atlas = np.rint(
        resample_from_to(nib.load(ATLAS), target_grid, order=0).get_fdata()
    ).astype(np.int16)
    sphere = (
        resample_from_to(nib.load(SPHERE), target_grid, order=0).get_fdata() > 0.5
    )
    coverage = np.squeeze(
        nib.load(AFNI / "mask_epi_extents+tlrc.HEAD").get_fdata()
    ) > 0
    censor = np.loadtxt(
        AFNI / "censor_NTHC1035_rest_combined_2.1D", dtype=float
    ).astype(bool)
    if censor.shape != (residual_image.shape[3],):
        raise ValueError("Censor vector does not match the resting time series")
    design = np.loadtxt(AFNI / "X.xmat.1D", comments="#")
    final_degrees_of_freedom = int(design.shape[0] - np.linalg.matrix_rank(design))

    parcel_coverage = {
        label: float(coverage[atlas == label].mean()) for label in range(1, 101)
    }
    labels = np.array(
        [
            label
            for label, fraction in parcel_coverage.items()
            if fraction >= COVERAGE_THRESHOLD
        ],
        dtype=int,
    )
    if labels.size < 90:
        raise RuntimeError("Fewer than 90 Schaefer parcels pass rest coverage")

    # AFNI writes censored residual volumes as zero. Remove those volumes before
    # correlations rather than treating them as observations.
    residuals = np.asanyarray(residual_image.dataobj, dtype=np.float32)[..., censor]
    time_series = np.column_stack(
        [
            residuals[(atlas == label) & coverage].mean(axis=0)
            for label in labels
        ]
    ).astype(np.float64)
    cortical = (atlas > 0) & coverage
    global_signal = residuals[cortical].mean(axis=0).astype(np.float64)
    if not np.all(np.isfinite(time_series)) or not np.all(np.isfinite(global_signal)):
        raise RuntimeError("Non-finite resting signals after extraction")

    fc = parcel_functional_connectivity(time_series)
    fc_gsr = parcel_functional_connectivity(
        time_series, global_signal=global_signal
    )
    embedding = summarize_functional_embedding(fc)
    embedding_gsr = summarize_functional_embedding(fc_gsr)
    target_label = select_stimulation_parcel(atlas, sphere, coverage & (atlas > 0))
    matches = np.flatnonzero(labels == target_label)
    if matches.size != 1:
        raise RuntimeError("The stimulation parcel failed resting coverage")
    target_index = int(matches[0])

    upper = np.triu_indices(labels.size, 1)
    target = {
        "parcel": target_label,
        "positive_strength": float(embedding.positive_strength[target_index]),
        "negative_strength": float(embedding.negative_strength[target_index]),
        "total_absolute_strength": float(
            embedding.total_absolute_strength[target_index]
        ),
        "mixed_sign_strength": float(
            embedding.mixed_sign_strength[target_index]
        ),
    }
    target_gsr = {
        "parcel": target_label,
        "positive_strength": float(embedding_gsr.positive_strength[target_index]),
        "negative_strength": float(embedding_gsr.negative_strength[target_index]),
        "total_absolute_strength": float(
            embedding_gsr.total_absolute_strength[target_index]
        ),
        "mixed_sign_strength": float(
            embedding_gsr.mixed_sign_strength[target_index]
        ),
    }
    midpoint = time_series.shape[0] // 2
    first_fc = parcel_functional_connectivity(time_series[:midpoint])
    second_fc = parcel_functional_connectivity(time_series[midpoint:])
    first_fc_gsr = parcel_functional_connectivity(
        time_series[:midpoint], global_signal=global_signal[:midpoint]
    )
    second_fc_gsr = parcel_functional_connectivity(
        time_series[midpoint:], global_signal=global_signal[midpoint:]
    )
    summary = {
        "subject": "sub-NTHC1035",
        "retained_timepoints": int(censor.sum()),
        "censored_timepoints": int((~censor).sum()),
        "final_degrees_of_freedom": final_degrees_of_freedom,
        "coverage_threshold": COVERAGE_THRESHOLD,
        "eligible_parcels": labels.tolist(),
        "excluded_low_coverage_parcels": sorted(set(range(1, 101)) - set(labels)),
        "minimum_parcel_coverage": float(min(parcel_coverage.values())),
        "fc_no_gsr_mean": float(np.mean(fc[upper])),
        "fc_no_gsr_negative_edge_fraction": float(np.mean(fc[upper] < 0)),
        "fc_gsr_mean": float(np.mean(fc_gsr[upper])),
        "fc_gsr_negative_edge_fraction": float(np.mean(fc_gsr[upper] < 0)),
        "split_half_edge_spearman_no_gsr": float(
            spearmanr(first_fc[upper], second_fc[upper]).statistic
        ),
        "split_half_edge_spearman_gsr": float(
            spearmanr(first_fc_gsr[upper], second_fc_gsr[upper]).statistic
        ),
        "target_no_gsr": target,
        "target_gsr": target_gsr,
        "interpretation_guardrail": (
            "Negative FC is a statistical anticorrelation, not a direct "
            "inhibitory or competitive anatomical connection."
        ),
    }
    np.savez_compressed(
        RESULTS / "rest_embedding.npz",
        labels=labels,
        time_series=time_series,
        global_signal=global_signal,
        fc_no_gsr=fc,
        fc_gsr=fc_gsr,
        positive_strength_no_gsr=embedding.positive_strength,
        negative_strength_no_gsr=embedding.negative_strength,
        positive_strength_gsr=embedding_gsr.positive_strength,
        negative_strength_gsr=embedding_gsr.negative_strength,
    )
    (RESULTS / "rest_embedding_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
