#!/usr/bin/env python3
"""Fit the frozen AR(1) TMS model to any AFNI NTHC1035 TMS site."""

from __future__ import annotations

import json
import argparse
from pathlib import Path
import sys

import nibabel as nib
import numpy as np
import pandas as pd
from nibabel.processing import resample_from_to
from nilearn.glm.first_level import FirstLevelModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from luppi_recreation.tms_glm import audit_tms_design, build_tms_design


PRESMA_AFNI = (
    ROOT
    / "results/empirical_tms_fmri_translation/afni/tms_presma_sub-NTHC1035"
    / "NTHC1035_presma.results"
)
PRESMA_OUTPUT = (
    ROOT
    / "results/empirical_tms_fmri_translation/afni/tms_presma_sub-NTHC1035/glm"
)
ATLAS = (
    ROOT
    / "data/atlases/templateflow/tpl-MNI152NLin2009cAsym"
    / "tpl-MNI152NLin2009cAsym_res-02_atlas-Schaefer2018_"
    "desc-100Parcels7Networks_dseg.nii.gz"
)


def afni_motion_confounds(afni: Path) -> tuple[pd.DataFrame, np.ndarray]:
    """Convert AFNI roll/pitch/yaw/dS/dL/dP parameters to frozen confounds."""

    motion = np.loadtxt(afni / "dfile_rall.1D", dtype=float)
    if motion.shape != (164, 6):
        raise ValueError(f"Expected 164x6 AFNI motion array, found {motion.shape}")

    # AFNI rotations are degrees. Translation axes are superior, left and
    # posterior; their names here provide a stable six-parameter basis rather
    # than claiming scanner RAS orientation.
    rotations_deg = motion[:, :3]
    translations = motion[:, 3:]
    derivatives = np.vstack([np.zeros((1, 6)), np.diff(motion, axis=0)])
    fd = np.zeros(len(motion), dtype=float)
    fd[1:] = np.sum(np.abs(np.diff(translations, axis=0)), axis=1) + 50.0 * np.sum(
        np.abs(np.deg2rad(np.diff(rotations_deg, axis=0))), axis=1
    )

    confounds = pd.DataFrame(
        {
            "trans_x": translations[:, 1],
            "trans_y": translations[:, 2],
            "trans_z": translations[:, 0],
            "rot_x": rotations_deg[:, 0],
            "rot_y": rotations_deg[:, 1],
            "rot_z": rotations_deg[:, 2],
            "trans_x_derivative1": derivatives[:, 4],
            "trans_y_derivative1": derivatives[:, 5],
            "trans_z_derivative1": derivatives[:, 3],
            "rot_x_derivative1": derivatives[:, 0],
            "rot_y_derivative1": derivatives[:, 1],
            "rot_z_derivative1": derivatives[:, 2],
            "framewise_displacement": fd,
        }
    )
    return confounds, fd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="R-preSMA")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "configs/tms_sites_sub-NTHC1035.json").read_text())
    matches = [entry for entry in manifest["sites"] if entry["site"] == args.site]
    if len(matches) != 1:
        raise ValueError(f"Unknown or duplicated site: {args.site}")
    task = matches[0]["task"]
    subject_id = f"NTHC1035_{args.site.replace('-', '')}"
    if args.site == "R-preSMA":
        afni = PRESMA_AFNI
        output = PRESMA_OUTPUT
        afni_subject_id = "NTHC1035_presma"
    else:
        site_root = (
            ROOT
            / "results/empirical_tms_fmri_translation/afni/tms_sites_sub-NTHC1035"
            / args.site
        )
        afni = site_root / f"{subject_id}.results"
        output = site_root / "glm"
        afni_subject_id = subject_id
    events_path = (
        ROOT
        / "data/derived/ds005498_pilot_bids/sub-NTHC1035/ses-2/func"
        / f"sub-NTHC1035_ses-2_task-{task}_events.tsv"
    )
    output.mkdir(parents=True, exist_ok=True)

    bold = nib.load(afni / f"pb04.{afni_subject_id}.r01.scale+tlrc.HEAD")
    if bold.shape != (96, 114, 96, 164):
        raise ValueError(f"Unexpected preprocessed BOLD shape: {bold.shape}")
    bold_nifti_path = output / f"sub-NTHC1035_task-{task}_desc-scaled_bold.nii"
    if not bold_nifti_path.exists():
        bold_nifti = nib.Nifti1Image(
            np.asanyarray(bold.dataobj, dtype=np.float32), bold.affine
        )
        bold_nifti.header.set_zooms((2.0, 2.0, 2.0, 2.4))
        nib.save(bold_nifti, bold_nifti_path)
    extents_image = nib.load(afni / "mask_epi_extents+tlrc.HEAD")
    extents = np.squeeze(np.asanyarray(extents_image.dataobj)) > 0
    atlas = np.rint(
        np.asanyarray(
            resample_from_to(
                nib.load(ATLAS), (extents.shape, extents_image.affine), order=0
            ).dataobj
        )
    ).astype(int)
    mask_data = extents & (atlas > 0)
    mask = nib.Nifti1Image(mask_data.astype(np.uint8), extents_image.affine)
    nib.save(mask, output / "desc-corticalExtents_mask.nii.gz")

    events = pd.read_csv(events_path, sep="\t")
    events["onset"] = events["onset"].astype(float) - 7.2
    if len(events) != 68 or events["onset"].min() < 0:
        raise ValueError("Shifted event audit failed")

    confounds, fd = afni_motion_confounds(afni)
    frame_times = np.arange(bold.shape[3], dtype=float) * 2.4
    design = build_tms_design(frame_times, events, confounds)
    audit = audit_tms_design(design)
    if not audit.full_rank:
        raise ValueError("Empirical TMS design is not full rank")

    model = FirstLevelModel(
        t_r=2.4,
        mask_img=mask,
        noise_model="ar1",
        standardize=False,
        signal_scaling=False,
        drift_model=None,
        minimize_memory=False,
        n_jobs=1,
    )
    model.fit(bold_nifti_path, design_matrices=design)
    beta = model.compute_contrast("TMS_pulse", output_type="effect_size")
    z_map = model.compute_contrast("TMS_pulse", output_type="z_score")
    nib.save(beta, output / f"sub-NTHC1035_task-{task}_desc-TMSpulse_beta.nii.gz")
    nib.save(z_map, output / f"sub-NTHC1035_task-{task}_desc-TMSpulse_z.nii.gz")

    # Conservative sensitivity: restrict the fit to AFNI's intensity-derived
    # EPI/anatomy mask, which retains fewer but higher-TSNR target voxels.
    auto_image = nib.load(afni / f"mask_epi_anat.{afni_subject_id}+tlrc.HEAD")
    auto_data = np.squeeze(np.asanyarray(auto_image.dataobj)) > 0
    auto_mask = nib.Nifti1Image(auto_data.astype(np.uint8), auto_image.affine)
    auto_model = FirstLevelModel(
        t_r=2.4,
        mask_img=auto_mask,
        noise_model="ar1",
        standardize=False,
        signal_scaling=False,
        drift_model=None,
        minimize_memory=False,
        n_jobs=1,
    )
    auto_model.fit(bold_nifti_path, design_matrices=design)
    auto_beta = auto_model.compute_contrast("TMS_pulse", output_type="effect_size")
    auto_z = auto_model.compute_contrast("TMS_pulse", output_type="z_score")
    nib.save(
        auto_beta,
        output / f"sub-NTHC1035_task-{task}_desc-TMSpulse_mask-AFNIAuto_beta.nii.gz",
    )
    nib.save(
        auto_z,
        output / f"sub-NTHC1035_task-{task}_desc-TMSpulse_mask-AFNIAuto_z.nii.gz",
    )
    design.to_csv(output / "design_matrix.tsv", sep="\t", index=False)
    confounds.to_csv(output / "motion_confounds.tsv", sep="\t", index=False)

    result = {
        "site": args.site,
        "task": task,
        **audit.__dict__,
        "full_rank": audit.full_rank,
        "noise_model": "ar1",
        "events": len(events),
        "first_shifted_onset_seconds": float(events["onset"].min()),
        "last_shifted_onset_seconds": float(events["onset"].max()),
        "fd_threshold_mm": 0.5,
        "fd_max_mm": float(fd.max()),
        "fd_mean_mm": float(fd.mean()),
        "beta_finite_inside_mask": bool(np.isfinite(beta.get_fdata()[mask_data]).all()),
        "z_finite_inside_mask": bool(np.isfinite(z_map.get_fdata()[mask_data]).all()),
    }
    (output / "glm_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
