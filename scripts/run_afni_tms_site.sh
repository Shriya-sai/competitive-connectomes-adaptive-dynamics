#!/bin/zsh
set -euo pipefail

if [[ $# -ne 2 ]]; then
  print -u2 "Usage: $0 SITE_LABEL TASK_LABEL"
  exit 2
fi

site="$1"
task="$2"
project="${0:A:h:h}"
input="${project}/data/derived/ds005498_pilot_bids"
sswarper="${project}/results/empirical_tms_fmri_translation/afni/sswarper_sub-NTHC1035"
template_dir="${project}/data/atlases/afni"
output="${project}/results/empirical_tms_fmri_translation/afni/tms_sites_sub-NTHC1035/${site}"
subject_id="NTHC1035_${site//-/}"
bold_name="sub-NTHC1035_ses-2_task-${task}_bold.nii.gz"

required=(
  "${input}/sub-NTHC1035/ses-2/func/${bold_name}"
  "${sswarper}/anatSS.NTHC1035.nii"
  "${sswarper}/anatQQ.NTHC1035.nii"
  "${sswarper}/anatQQ.NTHC1035_WARP.nii"
  "${sswarper}/anatQQ.NTHC1035.aff12.1D"
  "${template_dir}/MNI152_2009_template_SSW.nii.gz"
)
for required_path in "${required[@]}"; do
  if [[ ! -f "${required_path}" ]]; then
    print -u2 "Required input not found: ${required_path}"
    exit 2
  fi
done
if [[ -d "${output}/${subject_id}.results" ]]; then
  print -u2 "Refusing to overwrite existing result: ${output}/${subject_id}.results"
  exit 3
fi

mkdir -p "${output}"
docker run --rm --platform linux/amd64 \
  -v "${input}:/data:ro" \
  -v "${sswarper}:/ssw:ro" \
  -v "${template_dir}:/templates:ro" \
  -v "${output}:/out" \
  afni/afni_make_build:AFNI_26.1.04 \
  afni_proc.py \
  -subj_id "${subject_id}" \
  -script "/out/proc.${subject_id}" \
  -out_dir "/out/${subject_id}.results" \
  -dsets "/data/sub-NTHC1035/ses-2/func/${bold_name}" \
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

mkdir -p "${output}/glm"
docker run --rm --platform linux/amd64 \
  -v "${output}:/site" \
  afni/afni_make_build:AFNI_26.1.04 \
  3dNwarpApply \
  -master "/site/${subject_id}.results/anatQQ.NTHC1035+tlrc" \
  -dxyz 2 \
  -source "/site/${subject_id}.results/vlines.pb00.tcat/clustset.r01.nii.gz" \
  -nwarp "/site/${subject_id}.results/anatQQ.NTHC1035_WARP.nii /site/${subject_id}.results/mat.basewarp.aff12.1D" \
  -interp NN \
  -ainterp NN \
  -prefix /site/glm/variance_line_mask_mni.nii.gz
