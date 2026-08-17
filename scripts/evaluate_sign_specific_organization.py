"""Evaluate cooperative and competitive organization with matched perturbations."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import load_hopf_extension, load_single_subject
from luppi_recreation.connectivity_nulls import (
    magnitude_matched_positive_mask,
    shuffle_values_within_mask,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = PROJECT_ROOT / "upstream" / "competitive-cooperative-hopf"
DATA_DIRECTORY = UPSTREAM_ROOT / "data" / "matlab" / "single"
OPTIMIZATION_PATH = PROJECT_ROOT / "results" / "single_subject_optimization" / "signed.npz"
OUTPUT_DIRECTORY = PROJECT_ROOT / "results" / "sign_specific_organization"
FIGURE_PATH = PROJECT_ROOT / "figures" / "sign_specific_organization.png"

REPETITION_TIME = 0.72
NOISE_STRENGTH = 0.001
BIFURCATION_PARAMETER = -0.02
NOISE_TYPE = 1


def score_network(hopf, connectivity, frequencies, n_timepoints, seed, empirical_values):
    bold = np.asarray(
        hopf.simulate(
            connectivity,
            frequencies,
            n_timepoints,
            REPETITION_TIME,
            NOISE_STRENGTH,
            BIFURCATION_PARAMETER,
            NOISE_TYPE,
            seed,
        ),
        dtype=np.float64,
    )
    simulated_fc = np.corrcoef(bold)
    simulated_values = simulated_fc[np.tril_indices_from(simulated_fc, k=-1)]
    return float(np.corrcoef(empirical_values, simulated_values)[0, 1])


def summarize(values: list[float]) -> dict[str, float]:
    array = np.asarray(values)
    return {
        "mean": float(array.mean()),
        "sd": float(array.std(ddof=1)) if len(array) > 1 else 0.0,
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shuffles", type=int, default=100)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--first-seed", type=int, default=42)
    parser.add_argument("--shuffle-seed", type=int, default=20260805)
    args = parser.parse_args()
    if args.shuffles < 1 or args.seeds < 1:
        raise ValueError("shuffles and seeds must be positive")

    data = load_single_subject(DATA_DIRECTORY)
    fitted = np.load(OPTIMIZATION_PATH)
    original = np.asarray(fitted["generative_connectivity"], dtype=np.float64)
    frequencies = np.asarray(fitted["regional_frequencies"], dtype=np.float64)
    empirical_fc = np.corrcoef(data.bold)
    empirical_values = empirical_fc[np.tril_indices_from(empirical_fc, k=-1)]
    simulation_seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    hopf = load_hopf_extension(UPSTREAM_ROOT)

    negative_mask = original < 0
    matched_positive_mask = magnitude_matched_positive_mask(original)
    if np.count_nonzero(negative_mask) != np.count_nonzero(matched_positive_mask):
        raise RuntimeError("matched perturbations do not contain equal weight counts")

    deterministic_networks = {"original": original}
    negative_removed = original.copy()
    negative_removed[negative_mask] = 0
    deterministic_networks["negative_removed"] = negative_removed
    negative_flipped = original.copy()
    negative_flipped[negative_mask] = np.abs(negative_flipped[negative_mask])
    deterministic_networks["negative_flipped_positive"] = negative_flipped

    records: list[dict[str, int | float | str]] = []
    condition_scores: dict[str, list[float]] = {}
    for condition, connectivity in deterministic_networks.items():
        print(f"Evaluating {condition}", flush=True)
        scores = []
        for seed in simulation_seeds:
            score = score_network(
                hopf, connectivity, frequencies, data.n_timepoints, seed, empirical_values
            )
            scores.append(score)
            records.append(
                {
                    "condition": condition,
                    "shuffle": 0,
                    "simulation_seed": seed,
                    "fc_correlation": score,
                }
            )
        condition_scores[condition] = scores

    rng = np.random.default_rng(args.shuffle_seed)
    shuffle_means = {"negative_strength_shuffle": [], "positive_strength_shuffle": []}
    masks = {
        "negative_strength_shuffle": negative_mask,
        "positive_strength_shuffle": matched_positive_mask,
    }
    for shuffle_index in range(1, args.shuffles + 1):
        print(f"Matched shuffle {shuffle_index}/{args.shuffles}", flush=True)
        for condition, mask in masks.items():
            connectivity = shuffle_values_within_mask(original, mask, rng)
            scores = []
            for seed in simulation_seeds:
                score = score_network(
                    hopf,
                    connectivity,
                    frequencies,
                    data.n_timepoints,
                    seed,
                    empirical_values,
                )
                scores.append(score)
                records.append(
                    {
                        "condition": condition,
                        "shuffle": shuffle_index,
                        "simulation_seed": seed,
                        "fc_correlation": score,
                    }
                )
            shuffle_means[condition].append(float(np.mean(scores)))

    original_mean = float(np.mean(condition_scores["original"]))
    summary: dict[str, object] = {
        "design": {
            "negative_weight_count": int(np.count_nonzero(negative_mask)),
            "matched_positive_weight_count": int(np.count_nonzero(matched_positive_mask)),
            "negative_mean_absolute_weight": float(np.mean(np.abs(original[negative_mask]))),
            "matched_positive_mean_weight": float(np.mean(original[matched_positive_mask])),
            "n_shuffles": args.shuffles,
            "simulation_seeds": simulation_seeds,
            "interpretation": (
                "Within-sign shuffles test strength-to-location mapping while preserving "
                "the sign map. Removal and flipping are separate sign ablations."
            ),
        },
        "fixed_conditions": {
            condition: summarize(scores)
            for condition, scores in condition_scores.items()
        },
        "shuffle_conditions": {},
    }
    for condition, values in shuffle_means.items():
        array = np.asarray(values)
        count_at_least_original = int(np.sum(array >= original_mean))
        summary["shuffle_conditions"][condition] = {
            **summarize(values),
            "mean_drop_from_original": float(original_mean - array.mean()),
            "shuffles_at_least_as_good_as_original": count_at_least_original,
            "one_sided_permutation_p_value": float(
                (count_at_least_original + 1) / (args.shuffles + 1)
            ),
        }

    negative_array = np.asarray(shuffle_means["negative_strength_shuffle"])
    positive_array = np.asarray(shuffle_means["positive_strength_shuffle"])
    difference = negative_array - positive_array
    summary["matched_comparison"] = {
        "mean_negative_minus_positive_shuffle": float(difference.mean()),
        "sd": float(difference.std(ddof=1)) if len(difference) > 1 else 0.0,
        "fraction_negative_shuffle_higher": float(np.mean(difference > 0)),
        "note": (
            "This is descriptive: matching equalizes count and approximately matches "
            "magnitude, but positive and negative weights retain their biological/model roles."
        ),
    }

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIRECTORY / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (OUTPUT_DIRECTORY / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    figure, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)
    labels = ["Original", "Negatives\nremoved", "Negatives\nflipped positive"]
    fixed_means = [
        np.mean(condition_scores[key])
        for key in ("original", "negative_removed", "negative_flipped_positive")
    ]
    fixed_sds = [
        np.std(condition_scores[key], ddof=1)
        for key in ("original", "negative_removed", "negative_flipped_positive")
    ]
    axes[0].bar(labels, fixed_means, yerr=fixed_sds, color=["#414B5A", "#B9A38C", "#D07A67"], capsize=4)
    axes[0].set_title("Are negative interactions required?", fontweight="bold")
    axes[0].set_ylabel("Empirical–simulated FC correlation")

    distributions = [negative_array, positive_array]
    violin = axes[1].violinplot(distributions, showmeans=True, showextrema=True)
    for body, color in zip(violin["bodies"], ["#B23A48", "#3D7EA6"], strict=True):
        body.set_facecolor(color)
        body.set_edgecolor(color)
        body.set_alpha(0.75)
    axes[1].axhline(original_mean, color="#414B5A", linestyle="--", label="Original")
    axes[1].set_xticks([1, 2], ["Negative-strength\nshuffle", "Matched positive-strength\nshuffle"])
    axes[1].set_title("Does strength-to-location mapping matter?", fontweight="bold")
    axes[1].set_ylabel("Mean FC correlation across matched seeds")
    axes[1].legend(frameon=False)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Sign-specific perturbations of fitted effective connectivity", fontweight="bold")
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
