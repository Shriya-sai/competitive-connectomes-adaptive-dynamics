"""Run frozen Stage 3 architectural-allocation experiment."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from luppi_recreation import load_hopf_extension
from run_hopf_focality_experiment import measure

ROOT=Path(__file__).resolve().parents[1];CFG=ROOT/'configs/hopf_architectural_allocation.json';LOCK=ROOT/'results/hopf_architectural_allocation/protocol_lock.json';UP=ROOT/'upstream/competitive-cooperative-hopf'
def load_locked():
 cfg=json.loads(CFG.read_text());lock=json.loads(LOCK.read_text())
 for name,want in lock['sha256'].items():
  assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==want,name
 return cfg
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stage',required=True,choices=['development','confirmation']);stage=ap.parse_args().stage;cfg=load_locked()
 out=ROOT/'results/hopf_architectural_allocation'/stage;out.mkdir(parents=True,exist_ok=True)
 if stage=='confirmation':
  gate=json.loads((ROOT/'results/hopf_architectural_allocation/development/instrument_gate.json').read_text());assert gate['instrument_gate_passed']
 gains=cfg['gain_conditions'] if stage=='confirmation' else {k:cfg['gain_conditions'][k] for k in cfg['development_conditions']};seeds=cfg[f'{stage}_seeds'];expected=cfg[f'{stage}_pairs']
 z=np.load(ROOT/'results/single_subject_optimization/signed.npz');signed=z['generative_connectivity'];freq=z['regional_frequencies'];pos=np.clip(signed,0,None);neg=np.clip(signed,None,0);hopf=load_hopf_extension(UP)
 rows=[];pre,pulse,recovery,tr=100,40,200,.72
 for condition,(gc,gi) in gains.items():
  conn=gc*pos+gi*neg
  for strategy,sets in cfg['strategies'].items():
   for replicate,nodes in sets.items():
    mask=np.zeros(100,bool);mask[nodes]=True;v=mask.astype(float)
    for sign in cfg['signs']:
     da=sign*cfg['allocation_per_target']
     for seed in seeds:
      c,x=hopf.simulate_paired_perturbation(conn,freq,v,pre,pulse,recovery,tr,.001,-.02,da,500.,1,seed)
      rows.append({'condition':condition,'cooperative_gain':gc,'competitive_gain':gi,'strategy':strategy,'replicate':replicate,'sign':sign,'target_count':len(nodes),'delta_a_per_target':da,'total_absolute_budget':abs(da)*len(nodes),'seed':seed,**measure(np.asarray(c),np.asarray(x),mask,pre,pulse,recovery,tr)})
      if len(rows)%240==0:print(f'completed {len(rows)}/{expected}',flush=True)
 assert len(rows)==expected
 with (out/'pairs.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 if stage=='development':
  unc=[r for r in rows if r['condition']=='uncoupled_control'];gate={'development_pairs':len(rows),'confirmation_seeds_accessed':False,'target_count_passed':all(r['target_count']==10 for r in rows),'fixed_budget_passed':all(abs(r['total_absolute_budget']-.03)<=1e-12 for r in rows),'prepulse_identity_passed':max(r['max_prepulse_difference'] for r in rows)<=1e-10,'all_finite_passed':all(r['all_finite'] for r in rows),'uncoupled_zero_propagation_passed':max(r['outside_region_RMS'] for r in unc)<=1e-10};gate['instrument_gate_passed']=all(v for k,v in gate.items() if k.endswith('_passed'));(out/'instrument_gate.json').write_text(json.dumps(gate,indent=2)+'\n');print(json.dumps(gate,indent=2))
 else:(out/'run_summary.json').write_text(json.dumps({'confirmation_pairs':len(rows),'all_finite':all(r['all_finite'] for r in rows)},indent=2)+'\n')
if __name__=='__main__':main()
