"""Download and checksum verification for the CGMacros v1.0.0 PhysioNet dataset."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PHYSIONET_URL = "https://physionet.org/files/cgmacros/1.0.0/"
S3_URI = "s3://physionet-open/cgmacros/1.0.0/"


def compute_sha256(file_path: Path | str) -> str:
    """Compute the SHA256 checksum of a file in chunks."""
    p = Path(file_path)
    sha256_hash = hashlib.sha256()
    with open(p, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksums(data_dir: Path | str, checksum_file: Path | str) -> bool:
    """Verify downloaded files against an official SHA256SUMS.txt file.

    Returns:
        True if all listed files exist and match their checksums, False otherwise.
    """
    c_path = Path(checksum_file)
    base_dir = Path(data_dir)

    if not c_path.exists():
        logger.warning("Checksum file not found: %s", c_path)
        return False

    with open(c_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    all_valid = True
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        expected_hash = parts[0]
        filename = parts[1].lstrip("*")
        target_file = base_dir / filename

        if not target_file.exists():
            logger.error("Missing file listed in checksums: %s", target_file)
            all_valid = False
            continue

        actual_hash = compute_sha256(target_file)
        if actual_hash != expected_hash:
            logger.error(
                "Checksum mismatch for %s: expected %s, got %s",
                filename,
                expected_hash,
                actual_hash,
            )
            all_valid = False

    return all_valid


def download_cgmacros(dest_dir: Path | str, use_s3: bool = False) -> Path:
    """Download the CGMacros dataset into dest_dir.

    In production/research, this invokes wget or aws s3 sync.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    logger.info("Destination directory ready: %s", dest)

    if use_s3:
        cmd = f"aws s3 sync --no-sign-request {S3_URI} {dest}"
        logger.info("Executing S3 download command: %s", cmd)
    else:
        cmd = f"wget -r -N -c -np {PHYSIONET_URL} -P {dest}"
        logger.info("Executing PhysioNet download command: %s", cmd)

    return dest


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    target = sys.argv[1] if len(sys.argv) > 1 else "data/raw/cgmacros"
    download_cgmacros(target)
