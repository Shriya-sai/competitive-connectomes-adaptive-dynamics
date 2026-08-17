"""Create a clean, minimal BIDS input for the frozen ds005498 pilot subject."""
from pathlib import Path
import json,os,shutil
import numpy as np
from scipy.io import loadmat

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/public/ds005498';SUBJECT='sub-NTHC1035'
DEST=ROOT/'data/derived/ds005498_pilot_bids'
DEST.mkdir(parents=True,exist_ok=True)

description=json.loads((SOURCE/'dataset_description.json').read_text())
description['Name']='Single-pulse TMS fMRI — local pilot subset'
(DEST/'dataset_description.json').write_text(json.dumps(description,indent=2)+'\n')
(DEST/'participants.tsv').write_text('participant_id\nsub-NTHC1035\n')
(DEST/'README').write_text('Local BIDS pilot subset of OpenNeuro ds005498 v2.0.0. Files are hard-linked from the immutable public-data download.\n')

for source in sorted((SOURCE/SUBJECT).glob('ses-*/*/*')):
    if not source.is_file() or source.name=='s3_manifest.xml':continue
    relative=source.relative_to(SOURCE);target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if target.stat().st_ino==source.stat().st_ino:continue
        target.unlink()
    os.link(source,target)

onsets=np.asarray(loadmat(ROOT/'upstream/sptmsfmri/data/stim-timing/CC_ERtiming_stim.mat',simplify_cells=True)['onsets'],float)
for bold in sorted((DEST/SUBJECT/'ses-2/func').glob('*_bold.nii.gz')):
    events=bold.with_name(bold.name.replace('_bold.nii.gz','_events.tsv'))
    lines=['onset\tduration\ttrial_type']+[f'{onset:.1f}\t0\tTMSpulse' for onset in onsets]
    events.write_text('\n'.join(lines)+'\n')
print(DEST)
