#!/bin/zsh
set -euo pipefail

project="${0:A:h:h}"
input="${project}/data/derived/ds005498_pilot_bids"
sswarper="${project}/results/empirical_tms_fmri_translation/afni/sswarper_sub-NTHC1035"
template_dir="${project}/data/atlases/afni"
output="${project}/results/empirical_tms_fmri_translation/afni/rest_sub-NTHC1035"

bold_host="${input}/sub-NTHC1035/ses-1/func/sub-NTHC1035_ses-1_task-resting_bold.nii"
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
  -subj_id NTHC1035_rest \
  -script /out/proc.NTHC1035_rest \
  -out_dir /out/NTHC1035_rest.results \
  -dsets /data/sub-NTHC1035/ses-1/func/sub-NTHC1035_ses-1_task-resting_bold.nii \
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
  -mask_segment_anat yes \
  -mask_segment_erode yes \
  -regress_motion_per_run \
  -regress_apply_mot_types demean deriv \
  -regress_ROI_PC WMe 3 \
  -regress_bandpass 0.01 0.10 \
  -regress_censor_motion 0.2 \
  -regress_censor_outliers 0.05 \
  -regress_run_clustsim no \
  -regress_est_blur_epits \
  -regress_est_blur_errts \
  -html_review_style pythonic \
  -execute
