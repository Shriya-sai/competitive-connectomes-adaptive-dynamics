#!/usr/bin/env python3
"""Summarize the frozen NTHC1035 multisite TMS-fMRI detection gate."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AFNI = ROOT / "results/empirical_tms_fmri_translation/afni"
THRESHOLD = 3.1
MAX_CENSOR_FRACTION = 0.20


def main() -> None:
    paths = [
        AFNI / "tms_presma_sub-NTHC1035/spatial_response.json",
        *sorted((AFNI / "tms_sites_sub-NTHC1035").glob("*/spatial_response.json")),
    ]
    rows = []
    for path in paths:
        response = json.loads(path.read_text())
        audit = json.loads((path.parent / "glm/glm_audit.json").read_text())
        censor_fraction = audit["censored_volumes"] / audit["n_timepoints"]
        local_detectable = abs(response["local_mean_z"]) >= THRESHOLD
        remote_detectable = response["remote_response_extent"] > 0
        rows.append({
            "site": response["target"],
            "local_mean_z": response["local_mean_z"],
            "max_remote_absolute_parcel_mean_z": max(
                map(abs, response["remote_parcel_z_scores"])
            ),
            "remote_response_extent": response["remote_response_extent"],
            "censored_volumes": audit["censored_volumes"],
            "censor_fraction": censor_fraction,
            "motion_qc_passed": censor_fraction <= MAX_CENSOR_FRACTION,
            "local_detectable": local_detectable,
            "remote_detectable": remote_detectable,
            "detectable": local_detectable or remote_detectable,
        })

    valid_rows = [row for row in rows if row["motion_qc_passed"]]
    gate_passed = any(row["detectable"] for row in valid_rows)
    summary = {
        "subject": "sub-NTHC1035",
        "detection_absolute_mean_z_threshold": THRESHOLD,
        "maximum_censor_fraction": MAX_CENSOR_FRACTION,
        "sites": rows,
        "n_sites": len(rows),
        "n_motion_qc_passed": len(valid_rows),
        "n_detectable_among_motion_qc_passed": sum(
            row["detectable"] for row in valid_rows
        ),
        "participant_gate_passed": gate_passed,
        "decision": (
            "carry_forward_to_embedding_analysis"
            if gate_passed
            else "stop_empirical_embedding_route_for_this_participant"
        ),
    }
    output = AFNI / "tms_multisite_gate_summary.json"
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
