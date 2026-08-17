#!/usr/bin/env python3
"""Fetch and verify the atlas used by the frozen TMS spatial instrument."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import nibabel as nib
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/atlases/templateflow"))
    parser.add_argument("--reference", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ["TEMPLATEFLOW_HOME"] = str(args.data_dir.resolve())
    from templateflow.api import get

    atlas_path = Path(
        get(
            "MNI152NLin2009cAsym",
            resolution=2,
            atlas="Schaefer2018",
            desc="100Parcels7Networks",
            suffix="dseg",
            extension="nii.gz",
        )
    )
    atlas = nib.load(atlas_path)
    reference = nib.load(args.reference)
    if atlas.shape != reference.shape or not np.allclose(atlas.affine, reference.affine):
        raise ValueError("TemplateFlow atlas and analysis reference do not share a grid")
    labels = np.unique(np.asarray(atlas.dataobj))
    positive_labels = labels[labels > 0]
    if not np.array_equal(positive_labels, np.arange(1, 101)):
        raise ValueError("Schaefer atlas does not contain exactly labels 1 through 100")
    print(f"Verified atlas: {atlas_path}")
    print(f"Grid: {atlas.shape}, {atlas.header.get_zooms()[:3]} mm")
    print("Labels: 1-100")


if __name__ == "__main__":
    main()
