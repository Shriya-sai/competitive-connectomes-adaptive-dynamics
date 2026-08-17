#!/bin/zsh
set -euo pipefail

project="/Users/shriyasai/Documents/Luppi et al. Recreation"
input="${project}/data/derived/ds005498_pilot_bids"
output="${project}/results/empirical_tms_fmri_translation/fmriprep"
work="${project}/build/fmriprep_work"

mkdir -p "${output}" "${work}"

docker run --rm --platform linux/amd64 \
  -v "${input}:/data:ro" \
  -v "${output}:/out" \
  -v "${work}:/work" \
  nipreps/fmriprep:25.2.5 \
  /data /out participant \
  --participant-label NTHC1035 \
  --task-id stim6x2x70 \
  --fs-no-reconall \
  --ignore slicetiming \
  --output-spaces MNI152NLin2009cAsym:res-2 \
  --nthreads 6 \
  --omp-nthreads 2 \
  --mem-mb 6500 \
  --work-dir /work \
  --stop-on-first-crash \
  --notrack
