"""Run only the frozen development gate for the paired Hopf perturbation instrument."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt

from luppi_recreation import load_hopf_extension


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "hopf_perturbation_response.json"
LOCK_PATH = ROOT / "results" / "hopf_perturbation_response" / "protocol_lock.json"
OUT = ROOT / "results" / "hopf_perturbation_response" / "development"
UPSTREAM = ROOT / "upstream" / "competitive-cooperative-hopf"


def verify_lock() -> dict:
    config = json.loads(CONFIG_PATH.read_text())
    lock = json.loads(LOCK_PATH.read_text())
    for relative, expected in lock["sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    assert config["randomization"]["confirmation_seeds"] == list(range(300, 330))
    return config


def rms_by_time(delta: np.ndarray, indices: np.ndarray) -> np.ndarray:
    return np.sqrt(np.mean(delta[indices] ** 2, axis=0))


def phase_distance(control: np.ndarray, intervention: np.ndarray, tr: float, mask: np.ndarray) -> float:
    sos = butter(2, [0.01, 0.1], btype="bandpass", fs=1 / tr, output="sos")
    c_phase = np.angle(hilbert(sosfiltfilt(sos, control, axis=-1), axis=-1))
    i_phase = np.angle(hilbert(sosfiltfilt(sos, intervention, axis=-1), axis=-1))
    residual = i_phase[:, mask] - c_phase[:, mask]
    n = residual.shape[0]
    resultant_sq = np.abs(np.exp(1j * residual).sum(axis=0)) ** 2
    agreement = (resultant_sq - n) / (n * (n - 1))
    return float(np.mean(1 - agreement))


def measure(control: np.ndarray, intervention: np.ndarray, site_mask: np.ndarray,
            pre: int, pulse: int, recovery: int, tr: float) -> dict[str, float | bool]:
    delta = intervention - control
    sites = np.flatnonzero(site_mask)
    outside = np.flatnonzero(~site_mask.astype(bool))
    pulse_slice = slice(pre, pre + pulse)
    recovery_slice = slice(pre + pulse, pre + pulse + recovery)
    direct_curve = rms_by_time(delta, sites)
    outside_curve = rms_by_time(delta, outside)
    total_curve = rms_by_time(delta, np.arange(delta.shape[0]))
    direct = float(np.sqrt(np.mean(delta[sites, pulse_slice] ** 2)))
    propagation = float(np.sqrt(np.mean(delta[outside, pulse_slice] ** 2)))
    total_pulse = float(np.sqrt(np.mean(delta[:, pulse_slice] ** 2)))
    peak = float(np.max(total_curve[pulse_slice]))
    threshold = 0.05 * peak
    smooth_n = 5
    smoothed = np.convolve(total_curve[recovery_slice], np.ones(smooth_n) / smooth_n, mode="same")
    sustain = max(1, int(round(14.4 / tr)))
    recovered_index = None
    for index in range(len(smoothed) - sustain + 1):
        if np.all(smoothed[index:index + sustain] <= threshold):
            recovered_index = index
            break
    final_n = int(round(28.8 / tr))
    analysis_mask = np.zeros(control.shape[1], dtype=bool)
    analysis_mask[pre:pre + pulse + recovery] = True
    return {
        "direct_response": direct,
        "propagation": propagation,
        "propagation_fraction": propagation / max(total_pulse, 1e-15),
        "phase_reconfiguration": phase_distance(control, intervention, tr, analysis_mask),
        "peak_total_response": peak,
        "recovery_time_seconds": float(recovered_index * tr) if recovered_index is not None else float(recovery * tr),
        "recovery_right_censored": recovered_index is None,
        "residual_displacement": float(np.mean(total_curve[-final_n:])),
        "control_stability": float(np.mean(np.std(control[:, :pre], axis=1, ddof=1))),
        "response_profile": np.sqrt(np.mean(delta[:, pulse_slice] ** 2, axis=1)),
        "site_label_direct_check": float(np.sqrt(np.mean(delta[sites, pulse_slice] ** 2))),
        "site_label_outside_check": float(np.sqrt(np.mean(delta[outside, pulse_slice] ** 2))),
        "max_prepulse_difference": float(np.max(np.abs(delta[:, :pre]))),
        "all_finite": bool(np.isfinite(control).all() and np.isfinite(intervention).all()),
    }


def site_permutation_unit_check(n_regions: int, true_sites: list[int]) -> bool:
    """Known localized response must move from direct to outside after disjoint relabelling."""
    delta = np.zeros((n_regions, 10), dtype=float)
    delta[true_sites] = 1.0
    true_mask = np.zeros(n_regions, dtype=bool); true_mask[true_sites] = True
    false_sites = [index for index in range(n_regions) if not true_mask[index]][:len(true_sites)]
    false_mask = np.zeros(n_regions, dtype=bool); false_mask[false_sites] = True
    true_direct = float(np.sqrt(np.mean(delta[true_mask] ** 2)))
    true_outside = float(np.sqrt(np.mean(delta[~true_mask] ** 2)))
    permuted_direct = float(np.sqrt(np.mean(delta[false_mask] ** 2)))
    permuted_outside = float(np.sqrt(np.mean(delta[~false_mask] ** 2)))
    return true_direct == 1.0 and true_outside == 0.0 and permuted_direct == 0.0 and permuted_outside > 0.0


def main() -> None:
    cfg = verify_lock()
    OUT.mkdir(parents=True, exist_ok=True)
    model = np.load(ROOT / cfg["model"]["connectivity_file"])
    signed = np.asarray(model[cfg["model"]["connectivity_array"]])
    frequencies = np.asarray(model[cfg["model"]["frequency_array"]])
    positive, negative = np.clip(signed, 0, None), np.clip(signed, None, 0)
    hopf = load_hopf_extension(UPSTREAM)
    tr = cfg["model"]["repetition_time_seconds"]
    pre = int(round(cfg["simulation_schedule"]["recorded_preperturbation_seconds"] / tr))
    recovery = int(round(cfg["simulation_schedule"]["recorded_recovery_seconds"] / tr))
    rows, profiles = [], {}
    gain_conditions = cfg["development_design"]["gain_conditions"]
    sites = cfg["perturbations"]["resolved_zero_based_site_sets"]
    total = cfg["development_design"]["paired_interventions"]
    completed = 0
    for cooperative, competitive in gain_conditions:
        connectivity = cooperative * positive + competitive * negative
        for site_name, indices in sites.items():
            site_mask = np.zeros(signed.shape[0]); site_mask[indices] = 1.0
            for duration_seconds in cfg["perturbations"]["duration_seconds"]:
                pulse = int(round(duration_seconds / tr))
                for amplitude in cfg["perturbations"]["delta_a"]:
                    for seed in cfg["randomization"]["development_seeds"]:
                        control, intervention = hopf.simulate_paired_perturbation(
                            connectivity, frequencies, site_mask, pre, pulse, recovery, tr,
                            cfg["model"]["noise_strength"], cfg["model"]["baseline_bifurcation_parameter"],
                            amplitude, cfg["simulation_schedule"]["discarded_burn_in_seconds"],
                            cfg["model"]["noise_type"], seed,
                        )
                        metrics = measure(np.asarray(control), np.asarray(intervention), site_mask,
                                          pre, pulse, recovery, tr)
                        profile = metrics.pop("response_profile")
                        key = (cooperative, competitive, site_name, duration_seconds, amplitude, seed)
                        profiles[key] = profile
                        rows.append({"cooperative_gain":cooperative,"competitive_gain":competitive,
                                     "site":site_name,"duration_seconds":duration_seconds,
                                     "delta_a":amplitude,"seed":seed,**metrics})
                        completed += 1
                        if completed % 40 == 0:
                            print(f"completed {completed}/{total}", flush=True)

    # Explicit zero-pulse identity across all four gain references and five seeds.
    zero_max = 0.0
    first_site = np.zeros(signed.shape[0]); first_site[sites["central_A"]] = 1.0
    for cooperative, competitive in gain_conditions:
        connectivity = cooperative * positive + competitive * negative
        for seed in cfg["randomization"]["development_seeds"]:
            control, intervention = hopf.simulate_paired_perturbation(
                connectivity, frequencies, first_site, pre, 10, recovery, tr,
                cfg["model"]["noise_strength"], cfg["model"]["baseline_bifurcation_parameter"],
                0.0, cfg["simulation_schedule"]["discarded_burn_in_seconds"],
                cfg["model"]["noise_type"], seed,
            )
            zero_max = max(zero_max, float(np.max(np.abs(np.asarray(control)-np.asarray(intervention)))))

    monotonic = []
    for cooperative, competitive in gain_conditions:
        for site_name in sites:
            for duration in cfg["perturbations"]["duration_seconds"]:
                for seed in cfg["randomization"]["development_seeds"]:
                    for sign in (-1, 1):
                        small = next(r["direct_response"] for r in rows if r["cooperative_gain"]==cooperative and r["competitive_gain"]==competitive and r["site"]==site_name and r["duration_seconds"]==duration and r["seed"]==seed and r["delta_a"]==sign*.01)
                        large = next(r["direct_response"] for r in rows if r["cooperative_gain"]==cooperative and r["competitive_gain"]==competitive and r["site"]==site_name and r["duration_seconds"]==duration and r["seed"]==seed and r["delta_a"]==sign*.03)
                        monotonic.append(large >= small)

    site_checks = [
        abs(r["direct_response"]-r["site_label_direct_check"]) <= 1e-15
        and abs(r["propagation"]-r["site_label_outside_check"]) <= 1e-15
        for r in rows
    ]
    site_permutation_passed = all(site_checks) and site_permutation_unit_check(
        signed.shape[0], sites["central_A"]
    )
    finite = all(r["all_finite"] for r in rows)
    max_pre = max(r["max_prepulse_difference"] for r in rows)
    gate_cfg = cfg["instrument_gate"]
    monotonic_fraction = float(np.mean(monotonic))
    gate = {
        "protocol_version": cfg["protocol_version"],
        "development_pairs": len(rows),
        "confirmation_seeds_accessed": False,
        "zero_pulse_max_absolute_difference": zero_max,
        "zero_pulse_identity_passed": zero_max <= gate_cfg["zero_pulse_control_max_absolute_difference"],
        "max_prepulse_absolute_difference": max_pre,
        "prepulse_identity_passed": max_pre <= gate_cfg["paired_noise_identity_before_pulse_max_absolute_difference"],
        "all_finite_passed": finite,
        "magnitude_monotonic_fraction": monotonic_fraction,
        "magnitude_monotonicity_passed": monotonic_fraction >= gate_cfg["response_must_increase_monotonically_with_absolute_delta_a_in_at_least_fraction_of_development_cells"],
        "site_permutation_check_passed": site_permutation_passed,
    }
    gate["instrument_gate_passed"] = all([
        gate["zero_pulse_identity_passed"], gate["prepulse_identity_passed"],
        gate["all_finite_passed"], gate["magnitude_monotonicity_passed"],
        gate["site_permutation_check_passed"],
    ])
    fields = [key for key in rows[0] if not key.startswith("site_label_")]
    with (OUT / "development_pairs.csv").open("w", newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore"); writer.writeheader(); writer.writerows(rows)
    (OUT / "instrument_gate.json").write_text(json.dumps(gate,indent=2)+"\n")
    print(json.dumps(gate,indent=2))


if __name__ == "__main__":
    main()
