"""Single source of truth feature extraction module used by training, evaluation, and inference."""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

# Population standardization references
POPULATION_MEANS = {
    "age": 52.0,
    "bmi": 28.5,
    "hba1c": 6.3,
    "fasting_glucose": 115.0,
    "fasting_insulin": 14.0,
    "triglycerides": 160.0,
    "hdl": 46.0,
    "hr": 74.0,
    "mets": 1.15,
}

POPULATION_STDS = {
    "age": 14.0,
    "bmi": 5.5,
    "hba1c": 1.2,
    "fasting_glucose": 28.0,
    "fasting_insulin": 8.0,
    "triglycerides": 55.0,
    "hdl": 12.0,
    "hr": 12.0,
    "mets": 0.45,
}

MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]


def extract_static_features(patient_profile: Dict[str, Any] | pd.Series) -> np.ndarray:
    """Extract standardized 8-dimensional static clinical feature vector."""

    def _safe_float(key: str, default: float) -> float:
        val = patient_profile.get(key)
        if val is None:
            return default
        try:
            f = float(val)
            if math.isnan(f) or math.isinf(f):
                return default
            return f
        except (ValueError, TypeError):
            return default

    age = _safe_float("age", POPULATION_MEANS["age"])
    sex_str = str(patient_profile.get("sex", "female") or "female").lower()
    sex_val = 1.0 if sex_str in ["male", "m"] else 0.0
    bmi = _safe_float("bmi", POPULATION_MEANS["bmi"])
    hba1c = _safe_float("hba1c", POPULATION_MEANS["hba1c"])
    fg = _safe_float("fasting_glucose", POPULATION_MEANS["fasting_glucose"])
    fi = _safe_float("fasting_insulin", POPULATION_MEANS["fasting_insulin"])
    tg = _safe_float("triglycerides", POPULATION_MEANS["triglycerides"])
    hdl = _safe_float("hdl", POPULATION_MEANS["hdl"])

    z_age = (age - POPULATION_MEANS["age"]) / POPULATION_STDS["age"]
    z_bmi = (bmi - POPULATION_MEANS["bmi"]) / POPULATION_STDS["bmi"]
    z_hba1c = (hba1c - POPULATION_MEANS["hba1c"]) / POPULATION_STDS["hba1c"]
    z_fg = (fg - POPULATION_MEANS["fasting_glucose"]) / POPULATION_STDS["fasting_glucose"]
    z_fi = (fi - POPULATION_MEANS["fasting_insulin"]) / POPULATION_STDS["fasting_insulin"]
    z_tg = (tg - POPULATION_MEANS["triglycerides"]) / POPULATION_STDS["triglycerides"]
    z_hdl = (hdl - POPULATION_MEANS["hdl"]) / POPULATION_STDS["hdl"]

    return np.array([z_age, sex_val, z_bmi, z_hba1c, z_fg, z_fi, z_tg, z_hdl], dtype=np.float32)


def extract_meal_features(
    meal: Dict[str, Any] | pd.Series, ts_start: Optional[pd.Timestamp] = None
) -> np.ndarray:
    """Extract standardized 16-dimensional meal composition and timing feature vector."""
    cal = float(meal.get("calories_eff", meal.get("calories", 0.0)))
    carbs = float(meal.get("carbs_eff", meal.get("carbs_g", 0.0)))
    protein = float(meal.get("protein_eff", meal.get("protein_g", 0.0)))
    fat = float(meal.get("fat_eff", meal.get("fat_g", 0.0)))
    fiber = float(meal.get("fiber_eff", meal.get("fiber_g", 0.0)))

    total = max(1.0, carbs + protein + fat)
    fat_ratio = float(meal.get("fat_ratio", fat / total))
    protein_ratio = float(meal.get("protein_ratio", protein / total))
    fiber_per_carb = float(meal.get("fiber_per_carb", fiber / max(1.0, carbs)))
    gl_proxy = float(meal.get("glycaemic_load_proxy", carbs - (0.5 * fiber)))
    delta_prev = float(meal.get("minutes_since_prev_meal", 720.0))

    # Meal type one-hot
    m_type = str(meal.get("meal_type", "lunch")).lower().strip()
    one_hot = [1.0 if m_type == t else 0.0 for t in MEAL_TYPES]

    # Hour of day cyclics
    if ts_start is None:
        raw_ts = meal.get("ts_start")
        ts_start = pd.to_datetime(raw_ts) if raw_ts is not None else pd.Timestamp.now()
    hour_val = ts_start.hour + (ts_start.minute / 60.0)
    sin_hour = math.sin(2.0 * math.pi * hour_val / 24.0)
    cos_hour = math.cos(2.0 * math.pi * hour_val / 24.0)

    # Standardize continuous variables
    z_cal = (cal - 500.0) / 250.0
    z_carbs = (carbs - 55.0) / 25.0
    z_protein = (protein - 25.0) / 12.0
    z_fat = (fat - 20.0) / 10.0
    z_fiber = (fiber - 5.0) / 3.0
    z_delta_prev = min(4.0, (delta_prev - 360.0) / 180.0)

    features = [
        z_cal,
        z_carbs,
        z_protein,
        z_fat,
        z_fiber,
        fat_ratio,
        protein_ratio,
        fiber_per_carb,
        gl_proxy / 50.0,
        z_delta_prev,
        *one_hot,
        sin_hour,
        cos_hour,
    ]
    return np.array(features, dtype=np.float32)


def extract_sequence_and_anchor_features(
    history_5min_df: pd.DataFrame,
    t0: pd.Timestamp,
    steps: int = 12,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """Extract [12, 6] sequence tensor and [4] anchor vector from history up to t0 (Decision D15).

    Returns:
        Tuple of (seq_tensor [12, 6], anchor_tensor [4], last_valid_glucose float)
    """
    # 1. Strictly enforce no future data
    valid_history = history_5min_df[history_5min_df["ts"] <= t0].sort_values("ts")

    # Select the last `steps` (e.g. 12 steps = 60 minutes)
    history_window = valid_history.tail(steps)

    # Sequence grid: [steps, 6]
    seq = np.zeros((steps, 6), dtype=np.float32)

    # Determine baseline G(t0) anchor
    last_valid_g = 120.0  # default population fallback
    anchor_age_min = 60.0  # default stale
    if not history_window.empty:
        non_null_g = history_window.dropna(subset=["glucose"])
        if not non_null_g.empty:
            last_row = non_null_g.iloc[-1]
            last_valid_g = float(last_row["glucose"])
            anchor_age_min = max(0.0, (t0 - last_row["ts"]).total_seconds() / 60.0)

    # Populate sequence tensor backward from index steps - 1
    n_rows = len(history_window)
    start_offset = steps - n_rows

    for i in range(n_rows):
        row = history_window.iloc[i]
        out_idx = start_offset + i

        # Glucose delta & mask
        g_val = row["glucose"]
        if pd.notna(g_val):
            seq[out_idx, 0] = float(g_val) - last_valid_g
            seq[out_idx, 1] = 1.0  # glucose observed
        else:
            seq[out_idx, 0] = 0.0
            seq[out_idx, 1] = 0.0  # glucose missing

        # HR z-score & mask
        hr_val = row.get("hr")
        if pd.notna(hr_val) and not bool(row.get("hr_missing", False)):
            seq[out_idx, 2] = (float(hr_val) - POPULATION_MEANS["hr"]) / POPULATION_STDS["hr"]
            seq[out_idx, 3] = 1.0  # HR present
        else:
            seq[out_idx, 2] = 0.0
            seq[out_idx, 3] = 0.0  # HR missing

        # METs z-score & mask
        mets_val = row.get("mets")
        if pd.notna(mets_val) and not bool(row.get("mets_missing", False)):
            seq[out_idx, 4] = (float(mets_val) - POPULATION_MEANS["mets"]) / POPULATION_STDS["mets"]
            seq[out_idx, 5] = 1.0  # METs present
        else:
            seq[out_idx, 4] = 0.0
            seq[out_idx, 5] = 0.0  # METs missing

    # Compute anchor statistics: pre_meal_mean_30, pre_meal_slope_15
    # Last 6 steps = 30 min, last 3 steps = 15 min
    last_6_steps = seq[-6:, :]
    observed_g_30 = last_6_steps[last_6_steps[:, 1] > 0, 0]
    mean_30 = float(np.mean(observed_g_30)) if len(observed_g_30) > 0 else 0.0

    last_3_steps = seq[-3:, :]
    observed_g_15 = last_3_steps[last_3_steps[:, 1] > 0, 0]
    if len(observed_g_15) >= 2:
        slope_15 = float((observed_g_15[-1] - observed_g_15[0]) / max(1, len(observed_g_15) - 1))
    else:
        slope_15 = 0.0

    anchor = np.array(
        [
            (last_valid_g - POPULATION_MEANS["fasting_glucose"])
            / POPULATION_STDS["fasting_glucose"],
            min(2.0, anchor_age_min / 30.0),
            mean_30 / 20.0,
            slope_15 / 5.0,
        ],
        dtype=np.float32,
    )

    return seq, anchor, last_valid_g
