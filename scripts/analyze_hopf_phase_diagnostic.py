"""Summarize frozen exploratory Hopf phase diagnostic."""
import csv,json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parents[1]; IN=ROOT/'results/hopf_phase_diagnostic'; FIG=ROOT/'figures/hopf_phase_diagnostic.png'
CONDITIONS=['uncoupled','cooperative_only','competitive_only','fitted_signed','competition_dominant','cooperation_dominant']
CLASSES=['within_perturbed','within_unperturbed','cross_boundary','all_edges']
def main():
 rows=list(csv.DictReader((IN/'diagnostic_pairs.csv').open()))
 def x(r,k): return float(r[k])
 grouped=[]
 for condition in CONDITIONS:
  s=[r for r in rows if r['condition']==condition]; rec={'condition':condition}
  for window in ['pulse','early_recovery','late_recovery']:
   for edge in CLASSES:
    for mode in ['raw','qualified']:
     v=np.array([x(r,f'{window}_{edge}_phase_{mode}') for r in s]);rec[f'median_{window}_{edge}_{mode}']=float(np.nanmedian(v))
    valid=np.array([x(r,f'{window}_{edge}_valid_fraction') for r in s]);rec[f'median_{window}_{edge}_valid_fraction']=float(np.median(valid))
  for k in ['pulse_direct_rms','pulse_outside_rms','early_recovery_direct_rms','early_recovery_outside_rms','pulse_common_mode_fraction','early_recovery_common_mode_fraction']:
   rec[f'median_{k}']=float(np.median([x(r,k) for r in s]))
  grouped.append(rec)
 # Per-pair diagnostic associations and qualification changes.
 raw=np.array([x(r,'pulse_all_edges_phase_raw') for r in rows]);qual=np.array([x(r,'pulse_all_edges_phase_qualified') for r in rows]);valid=np.array([x(r,'pulse_all_edges_valid_fraction') for r in rows]);common=np.array([x(r,'pulse_common_mode_fraction') for r in rows]);direct=np.array([x(r,'pulse_direct_rms') for r in rows])
 summary={'version':'1.0.0','pairs':len(rows),'condition_summaries':grouped,
  'median_absolute_raw_qualified_difference':float(np.nanmedian(abs(raw-qual))),
  'raw_qualified_spearman':float(spearmanr(raw,qual,nan_policy='omit').statistic),
  'raw_phase_vs_invalid_fraction_spearman':float(spearmanr(raw,1-valid).statistic),
  'qualified_phase_vs_invalid_fraction_spearman':float(spearmanr(qual,1-valid,nan_policy='omit').statistic),
  'qualified_phase_vs_common_mode_spearman':float(spearmanr(qual,common,nan_policy='omit').statistic),
  'qualified_phase_vs_direct_response_spearman':float(spearmanr(qual,direct,nan_policy='omit').statistic)}
 # Spatial dominance by condition from qualified pulse medians.
 for rec in grouped:
  values={edge:rec[f'median_pulse_{edge}_qualified'] for edge in CLASSES[:-1]}
  rec['largest_qualified_pulse_edge_class']=max(values,key=values.get)
 (IN/'analysis_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 with (IN/'condition_summary.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(grouped[0]));w.writeheader();w.writerows(grouped)
 fig,axes=plt.subplots(1,3,figsize=(14,4.5),constrained_layout=True);z=np.arange(len(CONDITIONS));width=.36
 axes[0].bar(z-width/2,[r['median_pulse_all_edges_raw'] for r in grouped],width,label='Raw');axes[0].bar(z+width/2,[r['median_pulse_all_edges_qualified'] for r in grouped],width,label='Amplitude-qualified');axes[0].set(title='Pulse-matched all-edge phase',ylabel='Phase distance',xticks=z,xticklabels=CONDITIONS);axes[0].tick_params(axis='x',rotation=35);axes[0].legend()
 for edge in CLASSES[:-1]: axes[1].plot(z,[r[f'median_pulse_{edge}_qualified'] for r in grouped],marker='o',label=edge)
 axes[1].set(title='Qualified phase by edge class',ylabel='Phase distance',xticks=z,xticklabels=CONDITIONS);axes[1].tick_params(axis='x',rotation=35);axes[1].legend(fontsize=8)
 axes[2].scatter(common,qual,s=5,alpha=.2);axes[2].set(title='Common mode versus qualified phase',xlabel='Common-mode fraction',ylabel='Qualified phase distance')
 fig.suptitle('Exploratory phase-reconfiguration measurement audit');fig.savefig(FIG,dpi=180);plt.close(fig)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
