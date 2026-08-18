#!/usr/bin/env python3
"""Quantify spatial coverage for the AFNI right-preSMA functional pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from nibabel.processing import resample_from_to


ROOT = Path(__file__).resolve().parents[1]
RESULTS = (
    ROOT
    / "results/empirical_tms_fmri_translation/afni/tms_presma_sub-NTHC1035"
    / "NTHC1035_presma.results"
)
ATLAS = (
    ROOT
    / "data/atlases/templateflow/tpl-MNI152NLin2009cAsym"
    / "tpl-MNI152NLin2009cAsym_res-02_atlas-Schaefer2018_"
    "desc-100Parcels7Networks_dseg.nii.gz"
)
SPHERE = ROOT / "upstream/sptmsfmri/data/stim-sites/R-preSMA_Sphere_Bin.nii.gz"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # The cortical first-level mask is the intersection of these valid EPI
    # extents and the Schaefer atlas. The intensity-derived AFNI automask is a
    # sensitivity mask because it removes most of the superior target despite
    # non-zero signal there.
    mask_image = nib.load(RESULTS / "mask_epi_extents+tlrc.HEAD")
    coverage_mask = np.squeeze(np.asanyarray(mask_image.dataobj)) > 0
    target = (coverage_mask.shape, mask_image.affine)

    atlas = np.rint(
        np.asanyarray(resample_from_to(nib.load(ATLAS), target, order=0).dataobj)
    ).astype(int)
    sphere = (
        np.asanyarray(resample_from_to(nib.load(SPHERE), target, order=0).dataobj)
        > 0.5
    )

    parcel_coverage: dict[str, float] = {}
    for parcel in range(1, 101):
        parcel_mask = atlas == parcel
        parcel_coverage[str(parcel)] = float(coverage_mask[parcel_mask].mean())

    cortical_sphere = sphere & (atlas > 0)
    target_parcel_sphere = sphere & (atlas == 78)
    values = np.asarray(list(parcel_coverage.values()))
    result = {
        "subject": "sub-NTHC1035",
        "run": "ses-2_task-stim6x2x70",
        "target_parcel": 78,
        "raw_sphere_coverage": float(coverage_mask[sphere].mean()),
        "cortical_sphere_coverage": float(coverage_mask[cortical_sphere].mean()),
        "target_parcel_sphere_coverage": float(
            coverage_mask[target_parcel_sphere].mean()
        ),
        "target_parcel_total_coverage": parcel_coverage["78"],
        "parcel_coverage_minimum": float(values.min()),
        "parcel_coverage_median": float(np.median(values)),
        "parcels_at_least_80_percent": int(np.sum(values >= 0.80)),
        "parcels_at_least_90_percent": int(np.sum(values >= 0.90)),
        "parcels_at_least_95_percent": int(np.sum(values >= 0.95)),
        "local_coverage_threshold": 0.90,
        "remote_parcel_coverage_threshold": 0.80,
        "local_coverage_passed": bool(coverage_mask[cortical_sphere].mean() >= 0.90),
        "remote_coverage_passed": bool(np.sum(values >= 0.80) >= 80),
        "parcel_coverage": parcel_coverage,
    }

    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n")


if __name__ == "__main__":
    main()
