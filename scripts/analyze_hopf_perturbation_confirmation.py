"""Analyze frozen target-free perturbation confirmation without a composite score."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "results/hopf_perturbation_response/confirmation"
OUT = ROOT / "results/hopf_perturbation_response/analysis"
FIG = ROOT / "figures/hopf_perturbation_response_confirmation.png"
METRICS = ["control_stability", "direct_response", "propagation", "propagation_fraction",
           "phase_reconfiguration", "recovery_time_seconds", "residual_displacement"]


def floats(row: dict[str, str]) -> dict[str, object]:
    output = dict(row)
    for key in ["cooperative_gain", "competitive_gain", "duration_seconds", "delta_a", "seed", *METRICS]:
        output[key] = float(row[key])
    output["recovery_right_censored"] = row["recovery_right_censored"] == "True"
    return output


def profile_reliability(indices: list[int], profiles: np.ndarray) -> float:
    # Mean leave-one-seed-out correlation avoids counting all 435 seed pairs per cell.
    values = []
    for index in indices:
        others = [other for other in indices if other != index]
        reference = profiles[others].mean(axis=0)
        correlation = np.corrcoef(profiles[index], reference)[0, 1]
        if np.isfinite(correlation): values.append(correlation)
    return float(np.mean(values)) if values else float("nan")


def nondominated(records: list[dict[str, float]], orientation: dict[str, int]) -> list[dict[str, float]]:
    output = []
    for candidate in records:
        dominated = False
        for other in records:
            if other is candidate: continue
            comparisons = [orientation[key] * other[key] >= orientation[key] * candidate[key] for key in orientation]
            strict = [orientation[key] * other[key] > orientation[key] * candidate[key] for key in orientation]
            if all(comparisons) and any(strict): dominated = True; break
        if not dominated: output.append(candidate)
    return output


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True); FIG.parent.mkdir(parents=True, exist_ok=True)
    rows = [floats(row) for row in csv.DictReader((IN / "confirmation_pairs.csv").open())]
    profiles = np.load(IN / "regional_response_profiles.npz")["profiles"]
    assert len(rows) == len(profiles) == 15360

    reliability_cells = defaultdict(list)
    for index, row in enumerate(rows):
        key = (row["cooperative_gain"], row["competitive_gain"], row["site"],
               row["duration_seconds"], row["delta_a"])
        reliability_cells[key].append(index)
    reliabilities = defaultdict(list)
    for key, indices in reliability_cells.items():
        reliabilities[key[:2]].append(profile_reliability(indices, profiles))

    grouped = []
    for cooperative in (0.0, .5, 1.0, 1.5):
        for competitive in (0.0, .5, 1.0, 1.5):
            selected = [row for row in rows if row["cooperative_gain"] == cooperative and row["competitive_gain"] == competitive]
            record = {"cooperative_gain":cooperative,"competitive_gain":competitive}
            for metric in METRICS:
                values=np.asarray([row[metric] for row in selected])
                record[f"median_{metric}"]=float(np.median(values))
                record[f"mean_{metric}"]=float(np.mean(values))
                record[f"q25_{metric}"]=float(np.quantile(values,.25))
                record[f"q75_{metric}"]=float(np.quantile(values,.75))
            record["recovery_censored_fraction"] = float(np.mean([row["recovery_right_censored"] for row in selected]))
            record["median_response_reliability"] = float(np.nanmedian(reliabilities[(cooperative,competitive)]))
            grouped.append(record)

    # Descriptive gain associations, retaining all perturbation pairs and paired seeds.
    associations = {}
    for metric in METRICS:
        associations[metric] = {
            "cooperative_gain_spearman": float(spearmanr([r["cooperative_gain"] for r in rows],[r[metric] for r in rows]).statistic),
            "competitive_gain_spearman": float(spearmanr([r["competitive_gain"] for r in rows],[r[metric] for r in rows]).statistic),
        }

    # One transparent orientation only; full axes remain reported and this is not an optimum.
    pareto_records=[]
    for record in grouped:
        pareto_records.append({
            "cooperative_gain":record["cooperative_gain"],"competitive_gain":record["competitive_gain"],
            "stability":record["median_control_stability"],"response":record["median_direct_response"],
            "propagation":record["median_propagation"],"recovery":record["median_recovery_time_seconds"],
            "residual":record["median_residual_displacement"],"reliability":record["median_response_reliability"],
        })
    orientation={"stability":-1,"response":1,"propagation":1,"recovery":-1,"residual":-1,"reliability":1}
    frontier=nondominated(pareto_records,orientation)

    with (OUT/"gain_summary.csv").open("w",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(grouped[0]));writer.writeheader();writer.writerows(grouped)
    summary={"protocol_version":"1.0.0","confirmation_pairs":len(rows),"gain_conditions":len(grouped),
             "response_reliability_definition":"median leave-one-seed-out regional-profile correlation across perturbation cells",
             "descriptive_gain_associations":associations,"pareto_orientation":orientation,
             "pareto_nondominated_conditions":frontier,
             "composite_score_constructed":False,"overall_winner_selected":False}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")

    fig,axes=plt.subplots(2,3,figsize=(13,8),constrained_layout=True)
    display=[("median_control_stability","Control instability"),("median_direct_response","Direct response"),
             ("median_propagation","Propagation"),("median_phase_reconfiguration","Phase reconfiguration"),
             ("median_recovery_time_seconds","Recovery time (s)"),("median_response_reliability","Response reliability")]
    gains=[0.,.5,1.,1.5]
    for ax,(key,title) in zip(axes.flat,display):
        matrix=np.array([[next(r[key] for r in grouped if r["cooperative_gain"]==c and r["competitive_gain"]==k) for c in gains] for k in gains])
        image=ax.imshow(matrix,origin="lower",aspect="auto",cmap="viridis")
        ax.set(xticks=range(4),xticklabels=gains,yticks=range(4),yticklabels=gains,xlabel="Cooperative gain",ylabel="Competitive gain",title=title)
        fig.colorbar(image,ax=ax,shrink=.78)
    fig.suptitle("Target-free paired Hopf perturbation responses (30 confirmation seeds)")
    fig.savefig(FIG,dpi=180);plt.close(fig)
    print(json.dumps(summary,indent=2))


if __name__ == "__main__": main()
