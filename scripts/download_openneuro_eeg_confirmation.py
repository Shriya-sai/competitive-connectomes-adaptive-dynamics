"""Integrity-checking acquisition for the frozen ds004295 confirmation subset."""

from __future__ import annotations

import hashlib
import json
import argparse
from pathlib import Path

import boto3
from boto3.s3.transfer import TransferConfig
from botocore import UNSIGNED
from botocore.config import Config


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs" / "eeg_switching_analysis.json").read_text())
DATA_ROOT = ROOT / "data" / "public_reversal_eeg_pilot"
DEFAULT_RESULT = ROOT / "results" / "reversal_eeg_confirmation" / "download_integrity.json"
BUCKET = "openneuro.org"


def md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--participants", nargs="+", default=CONFIG["confirmation_participants"])
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    args = parser.parse_args()
    participants = args.participants
    result_path = args.result
    result_path.parent.mkdir(parents=True, exist_ok=True)
    s3 = boto3.client(
        "s3", config=Config(signature_version=UNSIGNED, retries={"max_attempts": 10})
    )
    transfer = TransferConfig(
        multipart_threshold=64 * 1024 * 1024,
        multipart_chunksize=64 * 1024 * 1024,
        max_concurrency=16,
        use_threads=True,
    )
    records = []
    for participant in participants:
        destination = DATA_ROOT / participant
        destination.mkdir(parents=True, exist_ok=True)
        for extension in ("set", "fdt"):
            filename = f"{participant}_task-task_eeg.{extension}"
            key = f"ds004295/{participant}/eeg/{filename}"
            target = destination / filename
            remote = s3.head_object(Bucket=BUCKET, Key=key)
            expected_size = int(remote["ContentLength"])
            expected_etag = remote["ETag"].strip('"')
            if not target.exists() or target.stat().st_size != expected_size:
                temporary = target.with_suffix(target.suffix + ".downloading")
                if temporary.exists():
                    temporary.unlink()
                s3.download_file(BUCKET, key, str(temporary), Config=transfer)
                if temporary.stat().st_size != expected_size:
                    raise RuntimeError(f"Size mismatch for {key}")
                temporary.replace(target)
            local_md5 = md5(target) if "-" not in expected_etag else None
            etag_verified = local_md5 == expected_etag if local_md5 is not None else None
            if etag_verified is False:
                raise RuntimeError(f"MD5 mismatch for {key}")
            records.append(
                {
                    "participant": participant,
                    "key": key,
                    "path": str(target),
                    "expected_size": expected_size,
                    "local_size": target.stat().st_size,
                    "etag": expected_etag,
                    "local_md5": local_md5,
                    "etag_verified": etag_verified,
                    "size_verified": target.stat().st_size == expected_size,
                }
            )
            print(f"verified {participant} .{extension}: {expected_size} bytes", flush=True)
    output = {
        "participants": participants,
        "files": records,
        "passed": len(records) == 2 * len(participants)
        and all(record["size_verified"] for record in records),
    }
    result_path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
