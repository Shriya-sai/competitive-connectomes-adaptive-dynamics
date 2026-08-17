"""Integrity-checking downloader for the ds004295 one-subject EEG pilot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from boto3.s3.transfer import TransferConfig


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "public_reversal_eeg_pilot" / "sub-s1"
RESULT = ROOT / "results" / "reversal_eeg_pilot" / "download_integrity.json"
BUCKET = "openneuro.org"
KEYS = [
    "ds004295/sub-s1/eeg/sub-s1_task-task_eeg.set",
    "ds004295/sub-s1/eeg/sub-s1_task-task_eeg.fdt",
]


def md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, retries={"max_attempts": 10}))
    transfer = TransferConfig(
        multipart_threshold=64 * 1024 * 1024,
        multipart_chunksize=64 * 1024 * 1024,
        max_concurrency=4,
        use_threads=True,
    )
    records = []
    for key in KEYS:
        target = DEST / Path(key).name
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
    RESULT.write_text(json.dumps({"files": records, "passed": True}, indent=2) + "\n")
    print(RESULT.read_text())


if __name__ == "__main__":
    main()
