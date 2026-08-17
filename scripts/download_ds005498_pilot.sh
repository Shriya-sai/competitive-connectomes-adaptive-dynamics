#!/bin/zsh
set -euo pipefail

subject="sub-NTHC1035"
dataset="ds005498"
destination="data/public/ds005498/${subject}"
manifest="${destination}/s3_manifest.xml"

mkdir -p "${destination}"
curl -fsSL "https://s3.amazonaws.com/openneuro.org?list-type=2&prefix=${dataset}/${subject}&encoding-type=url" -o "${manifest}"

grep -o '<Key>[^<]*</Key>' "${manifest}" | sed -e 's#<Key>##' -e 's#</Key>##' | xargs -n 1 -P 6 zsh -c '
  key="$1"
  relative="${key#ds005498/}"
  target="data/public/ds005498/${relative}"
  mkdir -p "${target:h}"
  partial="${target}.part"
  curl -fsSL --retry 3 "https://s3.amazonaws.com/openneuro.org/${key}" -o "${partial}"
  mv "${partial}" "${target}"
' _

echo "Downloaded ${subject} to ${destination}"
