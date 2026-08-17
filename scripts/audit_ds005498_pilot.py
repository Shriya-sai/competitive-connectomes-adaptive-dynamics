"""Audit downloaded ds005498 pilot integrity, image geometry, and shared timing."""
from pathlib import Path
import json,urllib.parse,xml.etree.ElementTree as ET
import nibabel as nib
import numpy as np
from scipy.io import loadmat

ROOT=Path(__file__).resolve().parents[1]
SUB=ROOT/'data/public/ds005498/sub-NTHC1035'
MAN=SUB/'s3_manifest.xml';NS={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
tree=ET.parse(MAN).getroot();mismatches=[]
for item in tree.findall('s:Contents',NS):
 key=urllib.parse.unquote(item.find('s:Key',NS).text);expected=int(item.find('s:Size',NS).text)
 path=ROOT/'data/public/ds005498'/Path(key).relative_to('ds005498')
 if not path.exists() or path.stat().st_size!=expected:mismatches.append({'path':str(path),'expected':expected,'observed':path.stat().st_size if path.exists() else None})
images=[]
for path in sorted(SUB.glob('**/*.nii*')):
 image=nib.load(path);images.append({'file':path.name,'shape':list(image.shape),'zooms':[float(x) for x in image.header.get_zooms()]})
timing=loadmat(ROOT/'upstream/sptmsfmri/data/stim-timing/CC_ERtiming_stim.mat',simplify_cells=True)
onsets=np.asarray(timing['onsets'],float);binary=np.loadtxt(ROOT/'upstream/sptmsfmri/data/stim-timing/stim-timing-TR-Binary.txt')
result={'manifest_file_count':len(tree.findall('s:Contents',NS)),'size_mismatches':mismatches,'images':images,'timing':{'matlab_onset_count':len(onsets),'first_onset_seconds':float(onsets[0]),'last_onset_seconds':float(onsets[-1]),'binary_length':len(binary),'binary_pulse_count':int(binary.sum()),'onsets_after_discarding_3_volumes_seconds':(onsets-7.2).tolist()},'audit_passed':bool(not mismatches and len(images)==13 and len(onsets)==68 and binary.sum()==68)}
out=ROOT/'results/empirical_tms_fmri_translation';out.mkdir(parents=True,exist_ok=True);(out/'pilot_download_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='images' and k!='timing'},indent=2))
