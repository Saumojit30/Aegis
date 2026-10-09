"""Supervised forecasting sample builder for 180-minute post-meal trajectories."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from aegis.features.extract import (
    extract_meal_features,
    extract_sequence_and_anchor_features,
    extract_static_features,
)

logger = logging.getLogger(__name__)

HORIZON_STEPS = 36  # 180 minutes at 5-minute intervals


def build_samples_for_cohort(
    patients_df: pd.DataFrame,
    meals_df: pd.DataFrame,
    sensor_df: pd.DataFrame,
    min_history_fraction: float = 0.7,
    min_target_fraction: float = 0.8,
) -> List[Dict[str, Any]]:
    """Construct supervised meal forecasting samples across all patients."""
    samples = []
    sensor_df = sensor_df.sort_values("ts")

    # Map patients by ID
    patient_map = {row["patient_id"]: row for _, row in patients_df.iterrows()}

    # Group sensor and meals by patient
    sensor_by_patient = {pid: grp for pid, grp in sensor_df.groupby("patient_id")}
    meals_by_patient = {
        pid: grp.sort_values("ts_start") for pid, grp in meals_df.groupby("patient_id")
    }

    for pid, p_meals in meals_by_patient.items():
        if pid not in patient_map or pid not in sensor_by_patient:
            continue

        p_profile = patient_map[pid]
        p_sensor = sensor_by_patient[pid]

        # Extract static features
        static_vec = extract_static_features(p_profile)

        for m_idx, (_, meal) in enumerate(p_meals.iterrows()):
            t0 = pd.to_datetime(meal["ts_start"])

            # 1. Check history window up to t0 (60 minutes = 12 steps)
            t_history_start = t0 - pd.Timedelta(minutes=60)
            hist_df = p_sensor[(p_sensor["ts"] >= t_history_start) & (p_sensor["ts"] <= t0)]
            if hist_df.empty:
                continue

            valid_history_count = hist_df["glucose"].notna().sum()
            if (valid_history_count / 12.0) < min_history_fraction:
                continue

            # Extract sequence and anchor features
            seq_tensor, anchor_vec, g_t0 = extract_sequence_and_anchor_features(
                p_sensor, t0, steps=12
            )

            # 2. Extract 36 future target steps: t0 + 5k for k in 1..36
            target_ts = [t0 + pd.Timedelta(minutes=5 * k) for k in range(1, HORIZON_STEPS + 1)]
            target_window = p_sensor[
                (p_sensor["ts"] > t0) & (p_sensor["ts"] <= t0 + pd.Timedelta(minutes=180))
            ].set_index("ts")

            # Check next meal truncation
            next_meal_ts = None
            if m_idx + 1 < len(p_meals):
                next_meal_ts = pd.to_datetime(p_meals.iloc[m_idx + 1]["ts_start"])

            target_deltas = np.zeros(HORIZON_STEPS, dtype=np.float32)
            target_mask = np.zeros(HORIZON_STEPS, dtype=np.float32)

            valid_primary_points = 0
            for k_idx, ts_k in enumerate(target_ts):
                if next_meal_ts and ts_k >= next_meal_ts:
                    # Truncate at subsequent meal start
                    break

                if ts_k in target_window.index:
                    val = target_window.loc[ts_k, "glucose"]
                    if pd.notna(val):
                        target_deltas[k_idx] = float(val) - g_t0
                        target_mask[k_idx] = 1.0
                        if k_idx < 24:  # within primary 120-min window
                            valid_primary_points += 1

            # Quality gate: >= 80% valid target points in primary 120 min (24 steps)
            if (valid_primary_points / 24.0) < min_target_fraction:
                continue

            # Extract meal features
            meal_vec = extract_meal_features(meal, t0)

            # Derived ground truth metrics
            valid_deltas = target_deltas[target_mask > 0]
            true_peak_delta = float(np.max(valid_deltas)) if len(valid_deltas) > 0 else 0.0
            true_peak_g = g_t0 + true_peak_delta
            peak_idx = int(np.argmax(valid_deltas)) if len(valid_deltas) > 0 else 0
            true_time_to_peak_min = (peak_idx + 1) * 5

            # Delayed window mean (120-180 min = steps 24..35)
            delayed_slice = target_deltas[24:36]
            delayed_mask = target_mask[24:36]
            delayed_mean = (
                float(np.mean(delayed_slice[delayed_mask > 0])) if np.sum(delayed_mask) > 0 else 0.0
            )

            samples.append(
                {
                    "sample_id": f"{meal['meal_id']}_S",
                    "patient_id": pid,
                    "meal_id": meal["meal_id"],
                    "group": p_profile.get("group", "healthy"),
                    "t0": t0.isoformat(),
                    "g_t0": g_t0,
                    "seq": seq_tensor.tolist(),
                    "static": static_vec.tolist(),
                    "meal": meal_vec.tolist(),
                    "anchor": anchor_vec.tolist(),
                    "target_deltas": target_deltas.tolist(),
                    "target_mask": target_mask.tolist(),
                    "true_peak_delta": true_peak_delta,
                    "true_peak_g": true_peak_g,
                    "true_time_to_peak_min": true_time_to_peak_min,
                    "true_delayed_mean": delayed_mean,
                    "is_high_risk": bool(true_peak_g >= 180.0),
                }
            )

    logger.info("Constructed %d forecasting samples", len(samples))
    return samples
