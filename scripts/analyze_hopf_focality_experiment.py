"""Analyze the frozen Hopf focality confirmation experiment without pandas."""
from pathlib import Path
from collections import defaultdict
import csv,json
import numpy as np
from scipy.stats import spearmanr,linregress
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/hopf_focality_experiment'
metrics=['response_per_targeted_region','propagation_per_untargeted_region','total_response_energy','cross_boundary','within_untargeted','remote_phase_fraction','spatial_reach_fraction','recovery_time_seconds','residual_displacement']
with (OUT/'confirmation/pairs.csv').open() as f: rows=list(csv.DictReader(f))
for r in rows:
 for c in ['focality','sign','seed',*metrics]:r[c]=float(r[c])
groups=defaultdict(list)
for r in rows:groups[(r['condition'],r['family'],r['dose_scheme'],r['sign'],r['seed'])].append(r)
trends=[]
for k,g in groups.items():
 g=sorted(g,key=lambda r:r['focality']);row=dict(zip(['condition','family','dose_scheme','sign','seed'],k));x=np.array([r['focality'] for r in g])
 for m in metrics:
  y=np.array([r[m] for r in g]);ok=np.isfinite(y);row['rho_'+m]=float(spearmanr(x[ok],y[ok]).statistic) if ok.sum()>2 else np.nan
 row['loglog_total_energy_slope']=float(linregress(np.log(x),np.log([r['total_response_energy'] for r in g])).slope);trends.append(row)
def write(name,data):
 with (OUT/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
write('focality_trends.csv',trends)
summ=[]
for cond in sorted(set(r['condition'] for r in trends)):
 for scheme in ['constant_per_region','constant_total']:
  g=[r for r in trends if r['condition']==cond and r['dose_scheme']==scheme];d={'condition':cond,'dose_scheme':scheme}
  for m in metrics:d['median_rho_'+m]=float(np.nanmedian([r['rho_'+m] for r in g]))
  d['median_loglog_total_energy_slope']=float(np.median([r['loglog_total_energy_slope'] for r in g]));summ.append(d)
write('trend_summary.csv',summ)
headline={}
for scheme in ['constant_per_region','constant_total']:
 g=[r for r in trends if r['dose_scheme']==scheme];headline[scheme]={m:float(np.nanmedian([r['rho_'+m] for r in g])) for m in metrics};headline[scheme]['median_loglog_total_energy_slope']=float(np.median([r['loglog_total_energy_slope'] for r in g]))
headline['system_level_label_rate']=sum(r['system_level_label']=='True' for r in rows)/len(rows);headline['confirmation_pairs']=len(rows)
(OUT/'summary.json').write_text(json.dumps(headline,indent=2)+'\n');print(json.dumps(headline,indent=2))
