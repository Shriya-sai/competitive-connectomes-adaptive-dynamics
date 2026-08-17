"""Run frozen exploratory phase diagnostic on six reference gain conditions."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt
from luppi_recreation import load_hopf_extension

ROOT=Path(__file__).resolve().parents[1]; UP=ROOT/'upstream/competitive-cooperative-hopf'
CFG_PATH=ROOT/'configs/hopf_phase_diagnostic.json'; LOCK=ROOT/'results/hopf_phase_diagnostic/protocol_lock.json'
PARENT=json.loads((ROOT/'configs/hopf_perturbation_response.json').read_text())
OUT=ROOT/'results/hopf_phase_diagnostic'

def verify():
    cfg=json.loads(CFG_PATH.read_text()); lock=json.loads(LOCK.read_text())
    for name,expected in lock['sha256'].items(): assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected
    return cfg

def edges(mask,kind):
    i,j=np.triu_indices(len(mask),1)
    if kind=='within_perturbed': keep=mask[i]&mask[j]
    elif kind=='within_unperturbed': keep=(~mask[i])&(~mask[j])
    elif kind=='cross_boundary': keep=mask[i]^mask[j]
    else: keep=np.ones(len(i),bool)
    return i[keep],j[keep]

def phase_metric(cp,ip,ca,thresholds,window,edge,qualified):
    i,j=edge; delta=(ip[i][:,window]-ip[j][:,window])-(cp[i][:,window]-cp[j][:,window])
    vals=np.cos(delta)
    if qualified:
        valid=(ca[i][:,window]>thresholds[i,None])&(ca[j][:,window]>thresholds[j,None])
        fraction=float(valid.mean())
        value=float(1-np.mean(vals[valid])) if fraction>=.25 and valid.any() else np.nan
    else: fraction=1.; value=float(1-np.mean(vals))
    return value,fraction

def main():
    cfg=verify(); OUT.mkdir(parents=True,exist_ok=True)
    model=np.load(ROOT/PARENT['model']['connectivity_file']); signed=np.asarray(model['generative_connectivity']); freq=np.asarray(model['regional_frequencies'])
    pos=np.clip(signed,0,None); neg=np.clip(signed,None,0); hopf=load_hopf_extension(UP)
    tr=.72; pre=100; recovery=200; sos=butter(2,[.01,.1],btype='bandpass',fs=1/tr,output='sos')
    rows=[]; total=6*4*4*2*30; done=0
    for name,(gc,gi) in cfg['reference_gain_conditions'].items():
      conn=gc*pos+gi*neg
      for site,indices in PARENT['perturbations']['resolved_zero_based_site_sets'].items():
       mask=np.zeros(100,bool);mask[indices]=True; vector=mask.astype(float); edge_sets={kind:edges(mask,kind) for kind in cfg['spatial_edge_classes']}
       for duration in PARENT['perturbations']['duration_seconds']:
        pulse=int(round(duration/tr)); pulse_win=np.arange(pre,pre+pulse); early=np.arange(pre+pulse,pre+2*pulse); late=np.arange(pre+pulse+recovery-40,pre+pulse+recovery)
        for amp in PARENT['perturbations']['delta_a']:
         for seed in PARENT['randomization']['confirmation_seeds']:
          c,x=hopf.simulate_paired_perturbation(conn,freq,vector,pre,pulse,recovery,tr,.001,-.02,amp,500.,1,seed);c=np.asarray(c);x=np.asarray(x);d=x-c
          cf=sosfiltfilt(sos,c,axis=-1);xf=sosfiltfilt(sos,x,axis=-1);cana=hilbert(cf,axis=-1);iana=hilbert(xf,axis=-1)
          ca=np.abs(cana);cp=np.angle(cana);ip=np.angle(iana);threshold=np.quantile(ca[:,:pre],.2,axis=1)
          energy=np.mean(d*d,axis=0); common=np.mean(d,axis=0)**2
          base={'condition':name,'cooperative_gain':gc,'competitive_gain':gi,'site':site,'duration_seconds':duration,'delta_a':amp,'seed':seed,
                'pulse_direct_rms':float(np.sqrt(np.mean(d[mask][:,pulse_win]**2))),'pulse_outside_rms':float(np.sqrt(np.mean(d[~mask][:,pulse_win]**2))),
                'early_recovery_direct_rms':float(np.sqrt(np.mean(d[mask][:,early]**2))),'early_recovery_outside_rms':float(np.sqrt(np.mean(d[~mask][:,early]**2))),
                'pulse_common_mode_fraction':float(common[pulse_win].mean()/max(energy[pulse_win].mean(),1e-15)),
                'early_recovery_common_mode_fraction':float(common[early].mean()/max(energy[early].mean(),1e-15))}
          for window_name,window in [('pulse',pulse_win),('early_recovery',early),('late_recovery',late)]:
           for kind,edge in edge_sets.items():
            raw,_=phase_metric(cp,ip,ca,threshold,window,edge,False);qualified,fraction=phase_metric(cp,ip,ca,threshold,window,edge,True)
            base[f'{window_name}_{kind}_phase_raw']=raw;base[f'{window_name}_{kind}_phase_qualified']=qualified;base[f'{window_name}_{kind}_valid_fraction']=fraction
          rows.append(base);done+=1
          if done%480==0: print(f'completed {done}/{total}',flush=True)
    with (OUT/'diagnostic_pairs.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={'version':cfg['version'],'pairs':len(rows),'all_finite':all(all(np.isfinite(v) for k,v in r.items() if isinstance(v,float) and 'qualified' not in k) for r in rows)}
    (OUT/'run_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
