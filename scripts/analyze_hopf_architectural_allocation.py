"""Analyze Stage 3 allocation profiles and architecture-by-gain interactions."""
from pathlib import Path
from collections import defaultdict
import csv,json
import numpy as np
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/hopf_architectural_allocation';P=OUT/'confirmation/pairs.csv'
metrics=['response_per_targeted_region','propagation_per_untargeted_region','total_response_energy','cross_boundary','within_untargeted','recovery_time_seconds','residual_displacement']
with P.open() as f:rows=list(csv.DictReader(f))
for r in rows:
 for m in metrics:r[m]=float(r[m])
strategies=sorted(set(r['strategy'] for r in rows));conditions=sorted(set(r['condition'] for r in rows))
summ=[]
for condition in conditions:
 for strategy in strategies:
  for sign in ['-1','1']:
   g=[r for r in rows if r['condition']==condition and r['strategy']==strategy and r['sign']==sign];d={'condition':condition,'strategy':strategy,'sign':int(sign),'n':len(g)}
   for m in metrics:d[m]=float(np.nanmedian([r[m] for r in g]))
   summ.append(d)
def write(name,data):
 with (OUT/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
write('strategy_summary.csv',summ)
# A/B reproducibility of complete six-strategy ordering, within condition/sign/seed.
reli=[]
for condition in conditions:
 for sign in ['-1','1']:
  for seed in sorted(set(r['seed'] for r in rows)):
   for m in metrics:
    a=[];b=[]
    for s in strategies:
     ra=next(r for r in rows if r['condition']==condition and r['sign']==sign and r['seed']==seed and r['strategy']==s and r['replicate']=='A')
     rb=next(r for r in rows if r['condition']==condition and r['sign']==sign and r['seed']==seed and r['strategy']==s and r['replicate']=='B')
     a.append(ra[m]);b.append(rb[m])
    rho=spearmanr(a,b).statistic
    reli.append({'condition':condition,'sign':int(sign),'seed':seed,'metric':m,'rho_A_B':float(rho) if np.isfinite(rho) else np.nan})
write('ab_rank_reliability.csv',reli)
# Strategy ranges and winners by condition; descriptive, not an overall winner.
profiles=[]
for condition in conditions:
 for m in metrics:
  g=[r for r in summ if r['condition']==condition]
  vals={s:float(np.nanmedian([r[m] for r in g if r['strategy']==s])) for s in strategies}
  profiles.append({'condition':condition,'metric':m,'minimum_strategy':min(vals,key=vals.get),'maximum_strategy':max(vals,key=vals.get),'min_value':min(vals.values()),'max_value':max(vals.values()),'relative_range':(max(vals.values())-min(vals.values()))/(abs(np.median(list(vals.values())))+1e-15)})
write('condition_profiles.csv',profiles)
headline={'confirmation_pairs':len(rows),'median_A_B_rank_reliability':{m:float(np.nanmedian([r['rho_A_B'] for r in reli if r['metric']==m])) for m in metrics},'profiles':profiles}
(OUT/'summary.json').write_text(json.dumps(headline,indent=2)+'\n')
print(json.dumps(headline['median_A_B_rank_reliability'],indent=2))
for p in profiles:
 if p['metric'] in ('propagation_per_untargeted_region','cross_boundary','within_untargeted'):print(p)
