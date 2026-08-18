#!/bin/zsh
set -euo pipefail

project="${0:A:h:h}"
input="${project}/data/derived/ds005498_pilot_bids"
sswarper="${project}/results/empirical_tms_fmri_translation/afni/sswarper_sub-NTHC1035"
template_dir="${project}/data/atlases/afni"
output="${project}/results/empirical_tms_fmri_translation/afni/tms_presma_sub-NTHC1035"

bold_host="${input}/sub-NTHC1035/ses-2/func/sub-NTHC1035_ses-2_task-stim6x2x70_bold.nii.gz"

required=(
  "${bold_host}"
  "${sswarper}/anatSS.NTHC1035.nii"
  "${sswarper}/anatQQ.NTHC1035.nii"
  "${sswarper}/anatQQ.NTHC1035_WARP.nii"
  "${sswarper}/anatQQ.NTHC1035.aff12.1D"
  "${template_dir}/MNI152_2009_template_SSW.nii.gz"
)
for required_path in "${required[@]}"; do
  if [[ ! -f "${required_path}" ]]; then
    print -u2 "Required pilot input not found: ${required_path}"
    exit 2
  fi
done

mkdir -p "${output}"

docker run --rm --platform linux/amd64 \
  -v "${input}:/data:ro" \
  -v "${sswarper}:/ssw:ro" \
  -v "${template_dir}:/templates:ro" \
  -v "${output}:/out" \
  afni/afni_make_build:AFNI_26.1.04 \
  afni_proc.py \
  -subj_id NTHC1035_presma \
  -script /out/proc.NTHC1035_presma \
  -out_dir /out/NTHC1035_presma.results \
  -dsets /data/sub-NTHC1035/ses-2/func/sub-NTHC1035_ses-2_task-stim6x2x70_bold.nii.gz \
  -copy_anat /ssw/anatSS.NTHC1035.nii \
  -anat_has_skull no \
  -blocks despike align tlrc volreg blur mask scale regress \
  -tcat_remove_first_trs 3 \
  -align_opts_aea -cost lpc+ZZ -giant_move -check_flip \
  -tlrc_base /templates/MNI152_2009_template_SSW.nii.gz \
  -tlrc_NL_warp \
  -tlrc_NL_warped_dsets \
    /ssw/anatQQ.NTHC1035.nii \
    /ssw/anatQQ.NTHC1035.aff12.1D \
    /ssw/anatQQ.NTHC1035_WARP.nii \
  -volreg_align_to MIN_OUTLIER \
  -volreg_align_e2a \
  -volreg_tlrc_warp \
  -volreg_warp_dxyz 2.0 \
  -blur_size 4.0 \
  -mask_epi_anat yes \
  -regress_motion_per_run \
  -regress_apply_mot_types demean deriv \
  -regress_censor_motion 0.3 \
  -regress_censor_outliers 0.05 \
  -regress_run_clustsim no \
  -regress_est_blur_errts \
  -html_review_style pythonic \
  -execute

# Transform AFNI's native-EPI variance-line flag with the reference-volume
# EPI-to-MNI warp. This supports a leave-flagged-column-out GLM sensitivity.
mkdir -p "${output}/glm"
docker run --rm --platform linux/amd64 \
  -v "${output}:/pilot" \
  afni/afni_make_build:AFNI_26.1.04 \
  3dNwarpApply \
  -master /pilot/NTHC1035_presma.results/anatQQ.NTHC1035+tlrc \
  -dxyz 2 \
  -source /pilot/NTHC1035_presma.results/vlines.pb00.tcat/clustset.r01.nii.gz \
  -nwarp "/pilot/NTHC1035_presma.results/anatQQ.NTHC1035_WARP.nii /pilot/NTHC1035_presma.results/mat.basewarp.aff12.1D" \
  -interp NN \
  -ainterp NN \
  -prefix /pilot/glm/variance_line_mask_mni.nii.gz
