#!/usr/bin/env python3
"""Apply the frozen spatial-response instrument to the AFNI pilot GLM."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import nibabel as nib
import numpy as np
from nibabel.processing import resample_from_to


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from luppi_recreation.tms_spatial import measure_tms_spatial_response


PILOT = (
    ROOT
    / "results/empirical_tms_fmri_translation/afni/tms_presma_sub-NTHC1035"
)
AFNI = PILOT / "NTHC1035_presma.results"
GLM = PILOT / "glm"
ATLAS = (
    ROOT
    / "data/atlases/templateflow/tpl-MNI152NLin2009cAsym"
    / "tpl-MNI152NLin2009cAsym_res-02_atlas-Schaefer2018_"
    "desc-100Parcels7Networks_dseg.nii.gz"
)
SPHERE = ROOT / "upstream/sptmsfmri/data/stim-sites/R-preSMA_Sphere_Bin.nii.gz"


def main() -> None:
    beta_image = nib.load(
        GLM / "sub-NTHC1035_task-stim6x2x70_desc-TMSpulse_beta.nii.gz"
    )
    z_image = nib.load(
        GLM / "sub-NTHC1035_task-stim6x2x70_desc-TMSpulse_z.nii.gz"
    )
    target = (beta_image.shape, beta_image.affine)
    beta = beta_image.get_fdata()
    z_map = z_image.get_fdata()
    atlas = np.rint(
        np.asanyarray(resample_from_to(nib.load(ATLAS), target, order=0).dataobj)
    ).astype(int)
    sphere = (
        np.asanyarray(resample_from_to(nib.load(SPHERE), target, order=0).dataobj)
        > 0.5
    )
    coverage_image = nib.load(AFNI / "mask_epi_extents+tlrc.HEAD")
    coverage = np.squeeze(np.asanyarray(coverage_image.dataobj)) > 0

    eligible_labels: list[int] = []
    parcel_coverage: dict[int, float] = {}
    for label in range(1, 101):
        parcel = atlas == label
        fraction = float(coverage[parcel].mean())
        parcel_coverage[label] = fraction
        if fraction >= 0.80:
            eligible_labels.append(label)

    eligible_atlas = atlas.copy()
    eligible_atlas[~np.isin(atlas, eligible_labels)] = 0
    cortical_coverage = coverage & (atlas > 0)
    response = measure_tms_spatial_response(
        beta,
        z_map,
        eligible_atlas,
        sphere,
        cortical_coverage,
        voxel_sizes_mm=(2.0, 2.0, 2.0),
        exclusion_buffer_mm=10.0,
        extent_z_threshold=3.1,
    )

    local = sphere & cortical_coverage
    local_betas = beta[local]
    local_z = z_map[local]
    auto_mask = np.squeeze(
        np.asanyarray(
            nib.load(AFNI / "mask_epi_anat.NTHC1035_presma+tlrc.HEAD").dataobj
        )
    ) > 0
    auto_beta = nib.load(
        GLM
        / "sub-NTHC1035_task-stim6x2x70_desc-TMSpulse_mask-AFNIAuto_beta.nii.gz"
    ).get_fdata()
    auto_z = nib.load(
        GLM / "sub-NTHC1035_task-stim6x2x70_desc-TMSpulse_mask-AFNIAuto_z.nii.gz"
    ).get_fdata()
    auto_local = sphere & (atlas > 0) & auto_mask
    variance_line = nib.load(GLM / "variance_line_mask_mni.nii.gz").get_fdata() > 0
    flagged_local = local & variance_line
    clean_local = local & ~variance_line
    if not np.any(clean_local):
        raise RuntimeError("Variance-line exclusion removed the entire target")
    result = {
        "subject": "sub-NTHC1035",
        "run": "ses-2_task-stim6x2x70",
        "target": "right preSMA",
        "local_signed_beta": response.local_signed_beta,
        "local_absolute_beta": response.local_absolute_beta,
        "local_mean_z": float(np.mean(local_z)),
        "local_median_beta": float(np.median(local_betas)),
        "local_beta_standard_deviation": float(np.std(local_betas)),
        "local_voxels": int(local.sum()),
        "automask_sensitivity_local_signed_beta": float(
            np.mean(auto_beta[auto_local])
        ),
        "automask_sensitivity_local_mean_z": float(np.mean(auto_z[auto_local])),
        "automask_sensitivity_local_voxels": int(auto_local.sum()),
        "variance_line_voxels_mni": int(variance_line.sum()),
        "variance_line_target_overlap_voxels": int(flagged_local.sum()),
        "variance_line_target_overlap_fraction": float(
            flagged_local.sum() / local.sum()
        ),
        "variance_line_excluded_local_signed_beta": float(
            np.mean(beta[clean_local])
        ),
        "variance_line_excluded_local_mean_z": float(np.mean(z_map[clean_local])),
        "variance_line_excluded_local_voxels": int(clean_local.sum()),
        "remote_mean_absolute_beta": response.remote_mean_absolute_beta,
        "remote_mean_positive_beta": response.remote_mean_positive_beta,
        "remote_mean_negative_magnitude": response.remote_mean_negative_magnitude,
        "remote_response_extent": response.remote_response_extent,
        "n_remote_parcels": response.n_remote_parcels,
        "remote_labels": response.remote_labels.tolist(),
        "remote_parcel_betas": response.remote_parcel_betas.tolist(),
        "remote_parcel_z_scores": response.remote_parcel_z_scores.tolist(),
        "excluded_low_coverage_parcels": sorted(
            label for label, fraction in parcel_coverage.items() if fraction < 0.80
        ),
    }
    path = PILOT / "spatial_response.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
