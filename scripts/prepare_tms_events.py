#!/usr/bin/env python3
"""Create a BIDS events table from the released continuous TMS pulse onsets."""

from __future__ import annotations

import argparse
from pathlib import Path

import nibabel as nib
import pandas as pd
from scipy.io import loadmat


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timing-mat", type=Path, required=True)
    parser.add_argument("--bold", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def extract_onsets(timing_mat: Path) -> list[float]:
    raw = loadmat(timing_mat, squeeze_me=True)["onsets"]
    return [float(value) for value in raw.reshape(-1)]


def main() -> None:
    args = parse_args()
    onsets = extract_onsets(args.timing_mat)
    image = nib.load(args.bold)
    n_volumes = image.shape[3]
    repetition_time = float(image.header.get_zooms()[3])
    run_duration = n_volumes * repetition_time

    if len(onsets) != 68:
        raise ValueError(f"Expected 68 TMS pulses, found {len(onsets)}")
    if min(onsets) < 0 or max(onsets) >= run_duration:
        raise ValueError(
            f"Pulse range {min(onsets):.1f}-{max(onsets):.1f}s falls outside "
            f"the {run_duration:.1f}s run"
        )
    if any(right <= left for left, right in zip(onsets, onsets[1:])):
        raise ValueError("TMS pulse onsets are not strictly increasing")

    events = pd.DataFrame(
        {"onset": onsets, "duration": 0.0, "trial_type": "TMS_pulse"}
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    events.to_csv(args.output, sep="\t", index=False, float_format="%.1f")
    print(
        f"Wrote {len(events)} events to {args.output}\n"
        f"Run: {n_volumes} volumes x {repetition_time:.1f}s = {run_duration:.1f}s\n"
        f"Pulse range: {onsets[0]:.1f}-{onsets[-1]:.1f}s"
    )


if __name__ == "__main__":
    main()
