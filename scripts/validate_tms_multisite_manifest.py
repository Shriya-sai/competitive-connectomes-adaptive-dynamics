#!/usr/bin/env python3
"""Validate the frozen NTHC1035 run-to-site manifest before batch processing."""

from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/tms_sites_sub-NTHC1035.json"
BIDS_FUNC = ROOT / "data/derived/ds005498_pilot_bids/sub-NTHC1035/ses-2/func"
SPHERES = ROOT / "upstream/sptmsfmri/data/stim-sites"


def main() -> None:
    manifest = json.loads(CONFIG.read_text())
    sites = manifest["sites"]
    if len(sites) != 11:
        raise ValueError(f"Expected 11 sites, found {len(sites)}")
    if len({entry["site"] for entry in sites}) != len(sites):
        raise ValueError("Site labels are not unique")
    if len({entry["task"] for entry in sites}) != len(sites):
        raise ValueError("Task labels are not unique")

    rows = []
    for entry in sites:
        stem = f"sub-NTHC1035_ses-2_task-{entry['task']}"
        bold = BIDS_FUNC / f"{stem}_bold.nii.gz"
        events = BIDS_FUNC / f"{stem}_events.tsv"
        sphere = SPHERES / entry["sphere"]
        for path in (bold, events, sphere):
            if not path.is_file():
                raise FileNotFoundError(path)
        image = nib.load(bold)
        event_table = pd.read_csv(events, sep="\t")
        valid = (
            image.shape == (64, 64, 31, 167)
            and abs(image.header.get_zooms()[3] - 2.4) < 1e-6
            and len(event_table) == 68
            and list(event_table.columns) == ["onset", "duration", "trial_type"]
            and float(event_table["onset"].min()) == 11.8
            and float(event_table["onset"].max()) == 388.6
        )
        if not valid:
            raise ValueError(f"Acquisition invariant failed for {entry['site']}")
        rows.append(
            {
                "site": entry["site"],
                "task": entry["task"],
                "sphere": entry["sphere"],
                "volumes": image.shape[3],
                "events": len(event_table),
                "status": "validated",
            }
        )
    output = ROOT / "results/empirical_tms_fmri_translation/tms_multisite_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
