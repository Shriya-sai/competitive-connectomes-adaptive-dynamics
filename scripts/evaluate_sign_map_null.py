"""Test whether cooperative/competitive signs belong at particular anatomical edges."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from luppi_recreation import load_hopf_extension, load_single_subject
from luppi_recreation.connectivity_nulls import shuffle_reciprocal_sign_patterns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = PROJECT_ROOT / "upstream" / "competitive-cooperative-hopf"
DATA_DIRECTORY = UPSTREAM_ROOT / "data" / "matlab" / "single"
OPTIMIZATION_PATH = PROJECT_ROOT / "results" / "single_subject_optimization" / "signed.npz"
OUTPUT_DIRECTORY = PROJECT_ROOT / "results" / "sign_map_null"
FIGURE_PATH = PROJECT_ROOT / "figures" / "sign_map_null.png"

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

    print("Evaluating original sign map", flush=True)
    original_scores = [
        score_network(hopf, original, frequencies, data.n_timepoints, seed, empirical_values)
        for seed in simulation_seeds
    ]

    rng = np.random.default_rng(args.shuffle_seed)
    records: list[dict[str, int | float]] = []
    null_means: list[float] = []
    for shuffle_index in range(1, args.shuffles + 1):
        print(f"Sign-map shuffle {shuffle_index}/{args.shuffles}", flush=True)
        shuffled = shuffle_reciprocal_sign_patterns(original, rng)
        if not np.array_equal(np.abs(shuffled), np.abs(original)):
            raise RuntimeError("a sign shuffle changed connection magnitudes")
        scores = []
        for seed in simulation_seeds:
            score = score_network(
                hopf, shuffled, frequencies, data.n_timepoints, seed, empirical_values
            )
            scores.append(score)
            records.append(
                {
                    "shuffle": shuffle_index,
                    "simulation_seed": seed,
                    "fc_correlation": score,
                }
            )
        null_means.append(float(np.mean(scores)))

    original_mean = float(np.mean(original_scores))
    null_array = np.asarray(null_means)
    count_at_least_original = int(np.sum(null_array >= original_mean))
    p_value = (count_at_least_original + 1) / (args.shuffles + 1)

    i, j = np.triu_indices_from(original, k=1)
    occupied = (original[i, j] != 0) | (original[j, i] != 0)
    first_sign = np.sign(original[i[occupied], j[occupied]])
    second_sign = np.sign(original[j[occupied], i[occupied]])
    summary = {
        "hypothesis": (
            "The anatomical assignment of cooperative and competitive roles contributes "
            "to empirical FC fit beyond topology and magnitudes."
        ),
        "n_shuffles": args.shuffles,
        "simulation_seeds": simulation_seeds,
        "original_mean_fc_correlation": original_mean,
        "original_sd_fc_correlation": float(np.std(original_scores, ddof=1))
        if len(original_scores) > 1
        else 0.0,
        "null_mean_fc_correlation": float(null_array.mean()),
        "null_sd_fc_correlation": float(null_array.std(ddof=1))
        if len(null_array) > 1
        else 0.0,
        "null_minimum": float(null_array.min()),
        "null_maximum": float(null_array.max()),
        "mean_drop_from_original": float(original_mean - null_array.mean()),
        "shuffles_at_least_as_good_as_original": count_at_least_original,
        "one_sided_permutation_p_value": float(p_value),
        "original_percentile_in_null": float(100 * np.mean(null_array < original_mean)),
        "preserved": [
            "every directed connection magnitude at its original location",
            "occupied anatomical-edge mask",
            "total positive and negative counts",
            "counts of reciprocal ++, mixed-sign, and -- edge patterns",
        ],
        "reciprocal_edge_pattern_counts": {
            "cooperative_cooperative": int(np.sum((first_sign > 0) & (second_sign > 0))),
            "mixed_sign": int(np.sum(first_sign != second_sign)),
            "competitive_competitive": int(np.sum((first_sign < 0) & (second_sign < 0))),
        },
    }

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIRECTORY / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (OUTPUT_DIRECTORY / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    figure, axis = plt.subplots(figsize=(7.6, 4.8), constrained_layout=True)
    axis.hist(null_array, bins="auto", color="#8A739B", alpha=0.82)
    axis.axvline(
        original_mean,
        color="#263B5A",
        linewidth=2.6,
        label=f"Original sign map ({original_mean:.3f})",
    )
    axis.set_xlabel("Mean empirical–simulated FC correlation across matched seeds")
    axis.set_ylabel("Number of shuffled sign maps")
    axis.set_title("Does the anatomical sign map matter?", fontweight="bold")
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(frameon=False)
    axis.text(
        0.02,
        0.96,
        f"one-sided permutation p = {p_value:.4f}",
        transform=axis.transAxes,
        va="top",
    )
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=240, bbox_inches="tight")
    plt.close(figure)

    print(json.dumps(summary, indent=2))
    print(f"Saved results to: {OUTPUT_DIRECTORY}")
    print(f"Saved figure to: {FIGURE_PATH}")


if __name__ == "__main__":
    main()
