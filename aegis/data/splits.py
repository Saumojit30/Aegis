"""Stratified grouped 5-fold cross-validation split generation at patient level."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def generate_patient_level_splits(
    patients_df: pd.DataFrame,
    n_splits: int = 5,
    seed: int = 42,
    output_path: Path | str | None = None,
) -> Dict[str, Any]:
    """Generate 5-fold grouped cross-validation splits stratified by diabetes status.

    Within each fold:
    - test_patients: held-out test cohort
    - Remaining patients are split into:
        - train_patients: primary model fitting
        - val_patients: early stopping and hyperparameter selection
        - cal_patients: split-conformal calibration
    """
    rng = np.random.default_rng(seed)

    # Group patients by diabetes category
    grouped_pids: Dict[str, List[str]] = {}
    for _, row in patients_df.iterrows():
        grp = str(row.get("group", "healthy")).lower()
        pid = str(row["patient_id"])
        grouped_pids.setdefault(grp, []).append(pid)

    # Shuffle within each group deterministically
    for grp in grouped_pids:
        rng.shuffle(grouped_pids[grp])

    # Partition each group into n_splits buckets
    group_buckets: Dict[str, List[List[str]]] = {}
    for grp, pids in grouped_pids.items():
        buckets: List[List[str]] = [[] for _ in range(n_splits)]
        for i, pid in enumerate(pids):
            buckets[i % n_splits].append(pid)
        group_buckets[grp] = buckets

    folds = []
    for fold_idx in range(n_splits):
        # Held-out test patients for this fold
        test_patients = []
        for grp in group_buckets:
            test_patients.extend(group_buckets[grp][fold_idx])

        # Available non-test patients
        pool = [p for p in patients_df["patient_id"].astype(str) if p not in test_patients]
        rng.shuffle(pool)

        # Allocate roughly: ~70% train, ~15% val, ~15% calibration
        n_pool = len(pool)
        n_val = max(1, int(round(n_pool * 0.15)))
        n_cal = max(1, int(round(n_pool * 0.15)))

        val_patients = sorted(pool[:n_val])
        cal_patients = sorted(pool[n_val : n_val + n_cal])
        train_patients = sorted(pool[n_val + n_cal :])

        folds.append(
            {
                "fold": fold_idx,
                "train_patients": train_patients,
                "val_patients": val_patients,
                "cal_patients": cal_patients,
                "test_patients": sorted(test_patients),
            }
        )

    splits_data = {
        "metadata": {
            "n_splits": n_splits,
            "seed": seed,
            "total_patients": len(patients_df),
            "group_counts": {grp: len(pids) for grp, pids in grouped_pids.items()},
        },
        "folds": folds,
    }

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(splits_data, f, indent=2)
        logger.info("Saved 5-fold patient splits to %s", out)

    return splits_data
