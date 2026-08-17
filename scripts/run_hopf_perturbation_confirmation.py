"""Run the frozen confirmation grid after the development instrument gate passed."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from luppi_recreation import load_hopf_extension
from validate_hopf_perturbation_instrument import ROOT, UPSTREAM, measure, verify_lock


def main() -> None:
    cfg = verify_lock()
    dev = json.loads((ROOT / "results/hopf_perturbation_response/development/instrument_gate.json").read_text())
    if not dev["instrument_gate_passed"] or dev["confirmation_seeds_accessed"]:
        raise RuntimeError("Confirmation is not released by the frozen development gate")
    out = ROOT / "results/hopf_perturbation_response/confirmation"
    out.mkdir(parents=True, exist_ok=True)
    model = np.load(ROOT / cfg["model"]["connectivity_file"])
    signed = np.asarray(model[cfg["model"]["connectivity_array"]])
    frequencies = np.asarray(model[cfg["model"]["frequency_array"]])
    positive, negative = np.clip(signed, 0, None), np.clip(signed, None, 0)
    hopf = load_hopf_extension(UPSTREAM)
    tr = cfg["model"]["repetition_time_seconds"]
    pre = int(round(cfg["simulation_schedule"]["recorded_preperturbation_seconds"] / tr))
    recovery = int(round(cfg["simulation_schedule"]["recorded_recovery_seconds"] / tr))
    rows, profiles = [], []
    total = cfg["confirmation_design"]["paired_interventions"]
    completed = 0
    for cooperative in cfg["gain_grid"]["cooperative"]:
        for competitive in cfg["gain_grid"]["competitive"]:
            connectivity = cooperative * positive + competitive * negative
            for site_name, indices in cfg["perturbations"]["resolved_zero_based_site_sets"].items():
                site_mask = np.zeros(signed.shape[0]); site_mask[indices] = 1.0
                for duration_seconds in cfg["perturbations"]["duration_seconds"]:
                    pulse = int(round(duration_seconds / tr))
                    for amplitude in cfg["perturbations"]["delta_a"]:
                        for seed in cfg["randomization"]["confirmation_seeds"]:
                            control, intervention = hopf.simulate_paired_perturbation(
                                connectivity, frequencies, site_mask, pre, pulse, recovery, tr,
                                cfg["model"]["noise_strength"], cfg["model"]["baseline_bifurcation_parameter"],
                                amplitude, cfg["simulation_schedule"]["discarded_burn_in_seconds"],
                                cfg["model"]["noise_type"], seed,
                            )
                            metrics = measure(np.asarray(control), np.asarray(intervention), site_mask,
                                              pre, pulse, recovery, tr)
                            profiles.append(metrics.pop("response_profile"))
                            rows.append({"cooperative_gain":cooperative,"competitive_gain":competitive,
                                         "site":site_name,"duration_seconds":duration_seconds,
                                         "delta_a":amplitude,"seed":seed,**metrics})
                            completed += 1
                            if completed % 480 == 0:
                                print(f"completed {completed}/{total}", flush=True)
    fields = [key for key in rows[0] if not key.startswith("site_label_")]
    with (out / "confirmation_pairs.csv").open("w",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore");writer.writeheader();writer.writerows(rows)
    np.savez_compressed(out / "regional_response_profiles.npz", profiles=np.asarray(profiles, dtype=np.float32))
    summary={"protocol_version":cfg["protocol_version"],"confirmation_pairs":len(rows),
             "seeds":cfg["randomization"]["confirmation_seeds"],"all_finite":all(r["all_finite"] for r in rows),
             "outcomes_generated_after_development_gate":True}
    (out/"run_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__": main()
