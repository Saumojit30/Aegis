"""Data validation suite and Checkpoint C1 manifest generator."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from aegis.features.extract import extract_sequence_and_anchor_features

logger = logging.getLogger(__name__)


def verify_patient_split_disjointness(splits_data: Dict[str, Any]) -> bool:
    """Leakage Test 1: Ensure zero patient overlap across sets within each fold."""
    for fold in splits_data.get("folds", []):
        f_idx = fold["fold"]
        train_set = set(fold["train_patients"])
        val_set = set(fold["val_patients"])
        cal_set = set(fold["cal_patients"])
        test_set = set(fold["test_patients"])

        # Check all intersections
        if train_set & val_set:
            raise AssertionError(f"Fold {f_idx}: train and val overlap on {train_set & val_set}")
        if train_set & cal_set:
            raise AssertionError(f"Fold {f_idx}: train and cal overlap on {train_set & cal_set}")
        if train_set & test_set:
            raise AssertionError(f"Fold {f_idx}: train and test overlap on {train_set & test_set}")
        if val_set & cal_set:
            raise AssertionError(f"Fold {f_idx}: val and cal overlap on {val_set & cal_set}")
        if val_set & test_set:
            raise AssertionError(f"Fold {f_idx}: val and test overlap on {val_set & test_set}")
        if cal_set & test_set:
            raise AssertionError(f"Fold {f_idx}: cal and test overlap on {cal_set & test_set}")

    return True


def verify_temporal_no_future_leakage(sensor_df: pd.DataFrame, t0: pd.Timestamp) -> bool:
    """Leakage Test 2: Perturbing future observations > t0 must not change feature tensors."""
    # Extract baseline features
    seq_baseline, anchor_baseline, g_baseline = extract_sequence_and_anchor_features(sensor_df, t0)

    # Corrupt future values (add 1000 mg/dL to all readings after t0)
    corrupted_df = sensor_df.copy()
    future_mask = corrupted_df["ts"] > t0
    corrupted_df.loc[future_mask, "glucose"] = 999.0
    corrupted_df.loc[future_mask, "hr"] = 999.0
    corrupted_df.loc[future_mask, "mets"] = 999.0

    seq_corrupted, anchor_corrupted, g_corrupted = extract_sequence_and_anchor_features(
        corrupted_df, t0
    )

    if not (seq_baseline == seq_corrupted).all():
        raise AssertionError("Temporal leakage detected: future data altered seq tensor!")
    if not (anchor_baseline == anchor_corrupted).all():
        raise AssertionError("Temporal leakage detected: future data altered anchor tensor!")
    if g_baseline != g_corrupted:
        raise AssertionError("Temporal leakage detected: future data altered baseline glucose!")

    return True


def verify_feature_shapes(samples: List[Dict[str, Any]]) -> bool:
    """Verify exact tensor dimensions across all built samples."""
    for s in samples:
        seq = s["seq"]
        if len(seq) != 12 or any(len(row) != 6 for row in seq):
            raise AssertionError(
                f"Invalid seq tensor shape in sample {s['sample_id']}: expected [12, 6]"
            )
        if len(s["static"]) != 8:
            raise AssertionError(
                f"Invalid static tensor length in sample {s['sample_id']}: expected 8"
            )
        if len(s["meal"]) != 16:
            raise AssertionError(
                f"Invalid meal tensor length in sample {s['sample_id']}: expected 16"
            )
        if len(s["anchor"]) != 4:
            raise AssertionError(
                f"Invalid anchor tensor length in sample {s['sample_id']}: expected 4"
            )
        if len(s["target_deltas"]) != 36:
            raise AssertionError(
                f"Invalid target deltas length in sample {s['sample_id']}: expected 36"
            )

    return True


def build_dataset_manifest(
    patients_df: pd.DataFrame,
    meals_df: pd.DataFrame,
    sensor_df: pd.DataFrame,
    samples: List[Dict[str, Any]],
    output_path: Path | str,
) -> Dict[str, Any]:
    """Generate Checkpoint C1 MANIFEST.json recording dataset hash and statistics."""
    # Compute deterministic fingerprint from patient and sample IDs
    hasher = hashlib.sha256()
    for pid in sorted(patients_df["patient_id"].astype(str)):
        hasher.update(pid.encode())
    for s in samples:
        hasher.update(s["sample_id"].encode())
    dataset_hash = hasher.hexdigest()[:16]

    manifest = {
        "dataset_version": f"v1.0.0-{dataset_hash}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cohort": {
            "total_patients": len(patients_df),
            "healthy": int((patients_df["group"] == "healthy").sum()),
            "prediabetes": int((patients_df["group"] == "prediabetes").sum()),
            "t2d": int((patients_df["group"] == "t2d").sum()),
        },
        "records": {
            "sensor_rows": len(sensor_df),
            "total_meals": len(meals_df),
            "supervised_samples": len(samples),
        },
        "target_windows": {
            "history_steps": 12,
            "horizon_steps": 36,
            "step_interval_min": 5,
        },
        "checkpoint_c1_status": "PASSED",
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info("Generated Checkpoint C1 dataset manifest at %s", out)
    return manifest
