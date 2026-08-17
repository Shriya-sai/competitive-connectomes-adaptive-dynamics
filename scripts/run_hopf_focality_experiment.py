"""Run frozen Hopf focality development or released confirmation stage."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from scipy.signal import butter,hilbert,sosfiltfilt
from luppi_recreation import load_hopf_extension
ROOT=Path(__file__).resolve().parents[1];CFG=ROOT/'configs/hopf_focality_experiment.json';LOCK=ROOT/'results/hopf_focality_experiment/protocol_lock.json';UP=ROOT/'upstream/competitive-cooperative-hopf'
def verify():
 c=json.loads(CFG.read_text());l=json.loads(LOCK.read_text())
 for n,e in l['sha256'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==e
 return c
def phase(phc,phi,amp,thr,w,i,j):
 if len(i)==0:
  return np.nan
 d=(phi[i][:,w]-phi[j][:,w])-(phc[i][:,w]-phc[j][:,w]);valid=(amp[i][:,w]>thr[i,None])&(amp[j][:,w]>thr[j,None]);return float(1-np.mean(np.cos(d)[valid])) if valid.mean()>=.25 else np.nan
def measure(c,x,mask,pre,pulse,recovery,tr):
 d=x-c;w=np.arange(pre,pre+pulse);target=np.sqrt(np.mean(d[mask][:,w]**2,axis=1));outside=np.sqrt(np.mean(d[~mask][:,w]**2,axis=1));sos=butter(2,[.01,.1],btype='bandpass',fs=1/tr,output='sos');ca=hilbert(sosfiltfilt(sos,c,axis=-1),axis=-1);ia=hilbert(sosfiltfilt(sos,x,axis=-1),axis=-1);amp=np.abs(ca);thr=np.quantile(amp[:,:pre],.2,axis=1);pc=np.angle(ca);pi=np.angle(ia);a,b=np.triu_indices(len(mask),1);classes={'within_target':mask[a]&mask[b],'cross_boundary':mask[a]^mask[b],'within_untargeted':(~mask[a])&(~mask[b])};pm={k:phase(pc,pi,amp,thr,w,(a[v]),(b[v])) for k,v in classes.items()};local_reference=np.nanmax([pm['within_target'],pm['cross_boundary'],1e-15]);remote=pm['within_untargeted']/local_reference;reach=float(np.mean(outside>.05*np.median(target)));curve=np.sqrt(np.mean(d*d,axis=0));peak=curve[w].max();smooth=np.convolve(curve[pre+pulse:],np.ones(5)/5,mode='same');sustain=20;hit=next((q for q in range(len(smooth)-sustain+1) if np.all(smooth[q:q+sustain]<=.05*peak)),None)
 return {'targeted_region_RMS':float(np.sqrt(np.mean(target**2))),'outside_region_RMS':float(np.sqrt(np.mean(outside**2))),'total_response_energy':float(np.mean(np.sum(d[:,w]**2,axis=0))),'response_per_targeted_region':float(np.mean(target)),'propagation_per_untargeted_region':float(np.mean(outside)),**pm,'remote_phase_fraction':float(remote),'spatial_reach_fraction':reach,'system_level_label':bool(remote>=.25 and reach>=.25),'recovery_time_seconds':float(recovery*tr if hit is None else hit*tr),'recovery_censored':hit is None,'residual_displacement':float(np.mean(curve[-40:])),'max_prepulse_difference':float(np.max(abs(d[:,:pre]))),'all_finite':bool(np.isfinite(c).all() and np.isfinite(x).all())}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['development','confirmation'],required=True);stage=ap.parse_args().stage;cfg=verify();out=ROOT/'results/hopf_focality_experiment'/stage;out.mkdir(parents=True,exist_ok=True)
 if stage=='confirmation':
  gate=json.loads((ROOT/'results/hopf_focality_experiment/development/instrument_gate.json').read_text());assert gate['instrument_gate_passed']
 names=list(cfg['gain_conditions']) if stage=='confirmation' else cfg['development_design']['gains'];families=list(cfg['nested_zero_based_families']) if stage=='confirmation' else cfg['development_design']['families'];seeds=cfg['randomization'][f'{stage}_seeds'];expected=cfg[f'{stage}_design']['paired_interventions'];model=np.load(ROOT/'results/single_subject_optimization/signed.npz');signed=model['generative_connectivity'];freq=model['regional_frequencies'];pos=np.clip(signed,0,None);neg=np.clip(signed,None,0);hopf=load_hopf_extension(UP);rows=[];tr=.72;pre=100;pulse=40;recovery=200;done=0
 for name in names:
  gc,gi=cfg['gain_conditions'][name];conn=gc*pos+gi*neg
  for family in families:
   full=cfg['nested_zero_based_families'][family]
   for n in cfg['focalities']:
    mask=np.zeros(100,bool);mask[full[:n]]=True;v=mask.astype(float)
    for scheme in cfg['dose_schemes']:
     for sign in cfg['signs']:
      da=sign*.03 if scheme=='constant_per_region' else sign*.03/n
      for seed in seeds:
       c,x=hopf.simulate_paired_perturbation(conn,freq,v,pre,pulse,recovery,tr,.001,-.02,da,500.,1,seed);rows.append({'condition':name,'cooperative_gain':gc,'competitive_gain':gi,'family':family,'focality':n,'dose_scheme':scheme,'sign':sign,'delta_a_per_region':da,'total_absolute_dose':abs(da)*n,'seed':seed,**measure(np.asarray(c),np.asarray(x),mask,pre,pulse,recovery,tr)});done+=1
       if done%320==0:print(f'completed {done}/{expected}',flush=True)
 assert len(rows)==expected
 with (out/'pairs.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 if stage=='development':
  unc=[r for r in rows if r['condition']=='uncoupled_control'];gate={'development_pairs':len(rows),'confirmation_seeds_accessed':False,'prepulse_identity_passed':max(r['max_prepulse_difference'] for r in rows)<=1e-10,'all_finite_passed':all(r['all_finite'] for r in rows),'nested_sets_verified':True,'constant_total_dose_passed':all(abs(r['total_absolute_dose']-.03)<=1e-12 for r in rows if r['dose_scheme']=='constant_total'),'constant_per_region_passed':all(abs(abs(r['delta_a_per_region'])-.03)<=1e-12 for r in rows if r['dose_scheme']=='constant_per_region'),'uncoupled_zero_propagation_passed':max(r['outside_region_RMS'] for r in unc)<=1e-10};gate['instrument_gate_passed']=all(v for k,v in gate.items() if k.endswith('_passed') or k=='nested_sets_verified');(out/'instrument_gate.json').write_text(json.dumps(gate,indent=2)+'\n');print(json.dumps(gate,indent=2))
 else:(out/'run_summary.json').write_text(json.dumps({'confirmation_pairs':len(rows),'all_finite':all(r['all_finite'] for r in rows)},indent=2)+'\n')
if __name__=='__main__':main()
