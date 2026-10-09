"""Cleaning and 5-minute grid resampling for CGMacros continuous sensor streams."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def clean_participant_timeseries(
    csv_path: Path | str,
    patient_id: str,
    glucose_min: float = 20.0,
    glucose_max: float = 600.0,
    interpolation_limit_min: int = 15,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Clean raw 1-minute time series and resample to a strict 5-minute uniform grid.

    Returns:
        Tuple of (clean_5min_df, quarantined_df)
    """
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(f"Participant CSV not found: {p}")

    df = pd.read_csv(p)

    # 1. Parse timestamps and sort
    df["ts"] = pd.to_datetime(df["Timestamp"], format="%m/%d/%Y %H:%M", errors="coerce")
    invalid_ts = df["ts"].isna()
    quarantined = df[invalid_ts].copy()
    if not quarantined.empty:
        quarantined["quarantine_reason"] = "invalid_timestamp"

    df = df[~invalid_ts].sort_values("ts").drop_duplicates(subset=["ts"], keep="first")
    df = df.set_index("ts")

    # 2. Extract columns of interest
    dexcom_col = "Dexcom GL" if "Dexcom GL" in df.columns else "Dexcom"
    libre_col = "Libre GL" if "Libre GL" in df.columns else "Libre"
    hr_col = "HR"
    mets_col = "Mets" if "Mets" in df.columns else "METs"
    cal_col = "Calories (Activity)" if "Calories (Activity)" in df.columns else "Activity Calories"

    # Identify out of range glucose readings
    dexcom = pd.to_numeric(df[dexcom_col], errors="coerce")
    out_of_range = (dexcom < glucose_min) | (dexcom > glucose_max)
    dexcom.loc[out_of_range] = np.nan

    libre = pd.to_numeric(df[libre_col], errors="coerce")
    hr = (
        pd.to_numeric(df[hr_col], errors="coerce")
        if hr_col in df.columns
        else pd.Series(np.nan, index=df.index)
    )
    mets = (
        pd.to_numeric(df[mets_col], errors="coerce")
        if mets_col in df.columns
        else pd.Series(np.nan, index=df.index)
    )
    cal_act = (
        pd.to_numeric(df[cal_col], errors="coerce")
        if cal_col in df.columns
        else pd.Series(np.nan, index=df.index)
    )

    combined_1min = pd.DataFrame(
        {
            "glucose": dexcom,
            "glucose_libre": libre,
            "hr": hr,
            "mets": mets,
            "cal_activity": cal_act,
        },
        index=df.index,
    )

    # 3. Resample to 5-minute grid using the nearest or first observation
    resampled_5min = combined_1min.resample("5min").first()

    # Track missingness prior to interpolation
    raw_missing = resampled_5min["glucose"].isna()

    # Interpolate gaps <= interpolation_limit_min (e.g. 15 min = 3 steps of 5 min)
    max_steps = max(1, interpolation_limit_min // 5)
    interpolated_g = resampled_5min["glucose"].interpolate(
        method="time", limit=max_steps, limit_direction="forward"
    )

    is_interpolated = raw_missing & interpolated_g.notna()
    is_still_missing = interpolated_g.isna()

    resampled_5min["glucose"] = interpolated_g
    resampled_5min["glucose_interpolated"] = is_interpolated
    resampled_5min["glucose_missing"] = is_still_missing
    resampled_5min["hr_missing"] = resampled_5min["hr"].isna()
    resampled_5min["mets_missing"] = resampled_5min["mets"].isna()

    resampled_5min["patient_id"] = patient_id
    resampled_5min = resampled_5min.reset_index()

    # Reorder canonical columns
    canonical_cols = [
        "patient_id",
        "ts",
        "glucose",
        "glucose_libre",
        "hr",
        "mets",
        "cal_activity",
        "glucose_missing",
        "hr_missing",
        "mets_missing",
        "glucose_interpolated",
    ]
    resampled_5min = resampled_5min[canonical_cols]

    return resampled_5min, quarantined


def clean_all_participants(
    data_dir: Path | str,
    output_dir: Path | str,
) -> pd.DataFrame:
    """Clean all participant CSVs in data_dir and save canonical sensor_5min.parquet."""
    src = Path(data_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    all_dfs = []
    csv_files = sorted(src.glob("P*.csv"))
    for f in csv_files:
        pid = f.stem
        clean_df, _ = clean_participant_timeseries(f, pid)
        all_dfs.append(clean_df)

    if not all_dfs:
        raise ValueError(f"No participant CSV files found in {src}")

    combined = pd.concat(all_dfs, ignore_index=True)
    out_file = out / "sensor_5min.parquet"
    combined.to_parquet(out_file, index=False)
    logger.info("Saved cleaned 5-minute sensor data to %s (%d rows)", out_file, len(combined))
    return combined
