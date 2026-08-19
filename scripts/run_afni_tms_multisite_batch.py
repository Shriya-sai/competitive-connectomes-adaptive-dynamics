#!/usr/bin/env python3
"""Run the frozen AFNI pipeline over NTHC1035 TMS sites sequentially."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/tms_sites_sub-NTHC1035.json"
PREPROCESSED_PRESMA = (
    ROOT
    / "results/empirical_tms_fmri_translation/afni/tms_presma_sub-NTHC1035"
    / "NTHC1035_presma.results"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--include-presma", action="store_true")
    parser.add_argument("--site", action="append", help="Limit to a site label")
    args = parser.parse_args()
    sites = json.loads(CONFIG.read_text())["sites"]
    requested = set(args.site or [])
    if requested:
        known = {entry["site"] for entry in sites}
        unknown = requested - known
        if unknown:
            raise ValueError(f"Unknown sites: {sorted(unknown)}")
        sites = [entry for entry in sites if entry["site"] in requested]

    plan = []
    for entry in sites:
        if (
            entry["site"] == "R-preSMA"
            and PREPROCESSED_PRESMA.is_dir()
            and not args.include_presma
        ):
            status = "reuse_validated_result"
        else:
            result = (
                ROOT
                / "results/empirical_tms_fmri_translation/afni/"
                "tms_sites_sub-NTHC1035"
                / entry["site"]
                / f"NTHC1035_{entry['site'].replace('-', '')}.results"
            )
            status = "already_exists" if result.is_dir() else "pending"
        plan.append({**entry, "status": status})
    print(json.dumps(plan, indent=2), flush=True)
    if not args.execute:
        return

    for entry in plan:
        if entry["status"] != "pending":
            continue
        print(f"\n=== {entry['site']} ({entry['task']}) ===", flush=True)
        subprocess.run(
            [
                "zsh",
                str(ROOT / "scripts/run_afni_tms_site.sh"),
                entry["site"],
                entry["task"],
            ],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    main()
