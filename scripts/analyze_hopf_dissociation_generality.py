"""Frozen Stage 1 factorial generality analysis of response-phase dissociation."""
from __future__ import annotations
import csv,hashlib,json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parents[1]; CFG=ROOT/'configs/hopf_dissociation_generality.json'; LOCK=ROOT/'results/hopf_dissociation_generality/protocol_lock.json'; SOURCE=ROOT/'results/hopf_phase_diagnostic/diagnostic_pairs.csv'; OUT=ROOT/'results/hopf_dissociation_generality'; FIG=ROOT/'figures/hopf_dissociation_generality.png'
METRICS={'displacement':'pulse_direct_rms','propagation':'pulse_outside_rms','phase':'pulse_all_edges_phase_qualified','local_phase':'pulse_within_perturbed_phase_qualified','boundary_phase':'pulse_cross_boundary_phase_qualified','remote_phase':'pulse_within_unperturbed_phase_qualified'}
def verify():
 lock=json.loads(LOCK.read_text())
 for name,expected in lock['sha256'].items(): assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected
 return json.loads(CFG.read_text())
def parse(row):
 r=dict(row);r['delta_a']=float(r['delta_a']);r['duration_seconds']=float(r['duration_seconds']);r['seed']=int(r['seed']);r['sign']='positive' if r['delta_a']>0 else 'negative';r['absolute_strength']=abs(r['delta_a']);r['target_centrality']=r['site'].split('_')[0];r['matched_target_set']=r['site'].split('_')[1]
 for key in METRICS.values():r[key]=float(r[key])
 return r
def summarize(rows,factor,level):
 s=[r for r in rows if r[factor]==level];phase=np.array([r[METRICS['phase']] for r in s]);direct=np.array([r[METRICS['displacement']] for r in s]);prop=np.array([r[METRICS['propagation']] for r in s]);local=np.array([r[METRICS['local_phase']] for r in s]);boundary=np.array([r[METRICS['boundary_phase']] for r in s]);remote=np.array([r[METRICS['remote_phase']] for r in s]);eligible=np.isfinite(local)&np.isfinite(boundary)&np.isfinite(remote);contrast=np.maximum(local[eligible],boundary[eligible])-remote[eligible]
 phase_prop=float(spearmanr(phase,prop).statistic) if np.ptp(prop)>0 else float('nan')
 return {'factor':factor,'level':str(level),'n':len(s),'localization_eligible_n':int(eligible.sum()),'localization_eligible_fraction':float(eligible.mean()),'median_displacement':float(np.median(direct)),'median_propagation':float(np.median(prop)),'median_phase':float(np.nanmedian(phase)),'phase_displacement_spearman':float(spearmanr(phase,direct,nan_policy='omit').statistic),'phase_propagation_spearman':phase_prop,'median_localization_contrast':float(np.median(contrast)),'localization_positive_fraction':float(np.mean(contrast>0))}
def main():
 cfg=verify();rows=[parse(r) for r in csv.DictReader(SOURCE.open())];assert len(rows)==cfg['source_rows'];OUT.mkdir(parents=True,exist_ok=True);FIG.parent.mkdir(parents=True,exist_ok=True)
 factors={'sign':['negative','positive'],'absolute_strength':[.01,.03],'duration_seconds':[7.2,28.8],'target_centrality':['central','peripheral'],'matched_target_set':['A','B'],'condition':cfg['factors']['gain_regime']}
 summaries=[summarize(rows,f,l) for f,levels in factors.items() for l in levels]
 perturbation=[r for r in summaries if r['factor']!='condition'];threshold=cfg['rules']['strong_coupling_threshold_absolute_rho'];passes=[]
 for r in perturbation:
  passed=abs(r['phase_displacement_spearman'])<threshold and abs(r['phase_propagation_spearman'])<threshold and r['localization_positive_fraction']>=.95;r['generality_level_passed']=passed;passes.append(passed)
 label='general' if all(passes) else ('conditional' if any(passes) else 'not_supported')
 # Seed-matched level differences for binary perturbation factors, averaging all remaining cells within seed.
 paired=[]
 for factor,levels in list(factors.items())[:5]:
  for metric,key in [('displacement',METRICS['displacement']),('propagation',METRICS['propagation']),('phase',METRICS['phase'])]:
   diffs=[]
   for seed in range(300,330):
    a=[r[key] for r in rows if r['seed']==seed and r[factor]==levels[0]];b=[r[key] for r in rows if r['seed']==seed and r[factor]==levels[1]];diffs.append(np.mean(b)-np.mean(a))
   paired.append({'factor':factor,'contrast':f'{levels[1]} minus {levels[0]}','metric':metric,'mean_seed_matched_difference':float(np.mean(diffs)),'median_seed_matched_difference':float(np.median(diffs)),'positive_seed_fraction':float(np.mean(np.array(diffs)>0))})
 with (OUT/'factor_level_summary.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
 with (OUT/'paired_factor_contrasts.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(paired[0]));w.writeheader();w.writerows(paired)
 summary={'version':cfg['version'],'rows':len(rows),'generality_label':label,'perturbation_levels_passing':sum(passes),'perturbation_levels_total':len(passes),'factor_level_summaries':summaries,'paired_factor_contrasts':paired,'focality_tested':False,'named_functional_systems_tested':False,'composite_score_constructed':False};(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 fig,axes=plt.subplots(2,3,figsize=(14,8),constrained_layout=True)
 for ax,(factor,levels) in zip(axes.flat,factors.items()):
  data=[next(r for r in summaries if r['factor']==factor and r['level']==str(level)) for level in levels];z=np.arange(len(levels));ax.plot(z,[r['phase_displacement_spearman'] for r in data],marker='o',label='Phase–displacement');ax.plot(z,[r['phase_propagation_spearman'] for r in data],marker='o',label='Phase–propagation');ax.axhline(.8,color='red',ls='--',lw=.8);ax.axhline(-.8,color='red',ls='--',lw=.8);ax.set(title=factor,xticks=z,xticklabels=[str(x) for x in levels],ylim=(-1,1),ylabel='Spearman rho');ax.tick_params(axis='x',rotation=30);ax.legend(fontsize=7)
 fig.suptitle('Generality of response–phase dissociation across sampled perturbation families');fig.savefig(FIG,dpi=180);plt.close(fig);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
