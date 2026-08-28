#!/bin/zsh
set -euo pipefail

script_dir="${0:A:h}"
project="${script_dir:h}"
input="${project}/data/derived/ds005498_pilot_bids"
template_dir="${project}/data/atlases/afni"
output="${project}/results/empirical_tms_fmri_translation/afni/sswarper_sub-NTHC1035"

t1="/data/sub-NTHC1035/ses-1/anat/sub-NTHC1035_ses-1_T1w.nii.gz"
template="/templates/MNI152_2009_template_SSW.nii.gz"

if [[ ! -f "${input}/sub-NTHC1035/ses-1/anat/sub-NTHC1035_ses-1_T1w.nii.gz" ]]; then
  print -u2 "Pilot T1w image not found in ${input}"
  exit 2
fi
if [[ ! -f "${template_dir}/MNI152_2009_template_SSW.nii.gz" ]]; then
  print -u2 "AFNI sswarper2 template not found in ${template_dir}"
  exit 2
fi

mkdir -p "${output}"

docker run --rm --platform linux/amd64 \
  -v "${input}:/data:ro" \
  -v "${template_dir}:/templates:ro" \
  -v "${output}:/out" \
  afni/afni_make_build:AFNI_26.1.04 \
  sswarper2 \
  -input "${t1}" \
  -base "${template}" \
  -subid NTHC1035 \
  -odir /out
