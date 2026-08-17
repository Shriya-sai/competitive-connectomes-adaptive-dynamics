"""Download the small public behavioral portion of OSF project 6n7db."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "public_reversal_behavior"
API = (
    "https://api.osf.io/v2/nodes/6n7db/files/osfstorage/"
    "68a73e830fb3403e98880343/?page%5Bsize%5D=100"
)


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.load(response)


def download(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    with urllib.request.urlopen(url, timeout=120) as response:
        destination.write_bytes(response.read())


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    listing = fetch_json(API)
    selected = []
    for item in listing["data"]:
        name = item["attributes"]["name"]
        if name == "README.txt" or (
            name.startswith("Sub") and name.endswith("_RL_Go_NoGo_results_all.txt")
        ):
            selected.append((name, item["links"]["download"]))

    for name, url in sorted(selected):
        print(f"Downloading {name}")
        download(url, OUTPUT / name)

    participant_files = sorted(OUTPUT.glob("Sub*_RL_Go_NoGo_results_all.txt"))
    print(f"Saved {len(participant_files)} deposited participant files to {OUTPUT}")
    if len(participant_files) != 33:
        raise RuntimeError(f"Expected 33 deposited files, found {len(participant_files)}")
    print("Note: Sub30 is deposited but excluded from the authors' 32-participant analysis.")


if __name__ == "__main__":
    main()
