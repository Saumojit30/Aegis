"""Extraction, effective macro scaling, and enrichment of meal events."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def extract_participant_meals(csv_path: Path | str, patient_id: str) -> pd.DataFrame:
    """Extract meal events from a participant's raw CSV."""
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(f"Participant CSV not found: {p}")

    df = pd.read_csv(p)
    df["ts"] = pd.to_datetime(df["Timestamp"], format="%m/%d/%Y %H:%M", errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts")

    # Filter rows with non-empty Meal Type
    meal_col = "Meal Type" if "Meal Type" in df.columns else "meal_type"
    meal_mask = df[meal_col].notna() & (df[meal_col].astype(str).str.strip() != "")
    meal_rows = df[meal_mask].copy()

    meals = []
    prev_meal_ts: pd.Timestamp | None = None

    for idx, (_, row) in enumerate(meal_rows.iterrows()):
        ts = row["ts"]
        meal_type = str(row[meal_col]).strip().lower()
        amount_pct = float(row.get("Amount Consumed", 100.0))
        if np.isnan(amount_pct) or amount_pct <= 0:
            amount_pct = 100.0

        cal = float(row.get("Calories", 0.0)) if pd.notna(row.get("Calories")) else 0.0
        carbs = float(row.get("Carbs", 0.0)) if pd.notna(row.get("Carbs")) else 0.0
        protein = float(row.get("Protein", 0.0)) if pd.notna(row.get("Protein")) else 0.0
        fat = float(row.get("Fat", 0.0)) if pd.notna(row.get("Fat")) else 0.0
        fiber = float(row.get("Fiber", 0.0)) if pd.notna(row.get("Fiber")) else 0.0

        # Effective macros based on consumed percentage
        fraction = amount_pct / 100.0
        carbs_eff = carbs * fraction
        protein_eff = protein * fraction
        fat_eff = fat * fraction
        fiber_eff = fiber * fraction
        cal_eff = cal * fraction

        total_macros = carbs_eff + protein_eff + fat_eff + 1e-6
        fat_ratio = fat_eff / total_macros
        protein_ratio = protein_eff / total_macros
        fiber_per_carb = fiber_eff / (carbs_eff + 1e-6)
        gl_proxy = carbs_eff - (0.5 * fiber_eff)

        # Time since previous meal
        if prev_meal_ts is not None:
            delta_min = (ts - prev_meal_ts).total_seconds() / 60.0
        else:
            delta_min = 720.0  # default 12h if first meal
        prev_meal_ts = ts

        meal_id = f"{patient_id}_M{idx + 1:03d}"
        meals.append(
            {
                "meal_id": meal_id,
                "patient_id": patient_id,
                "ts_start": ts,
                "meal_type": meal_type,
                "calories": cal,
                "carbs_g": carbs,
                "protein_g": protein,
                "fat_g": fat,
                "fiber_g": fiber,
                "amount_consumed_pct": amount_pct,
                "calories_eff": cal_eff,
                "carbs_eff": carbs_eff,
                "protein_eff": protein_eff,
                "fat_eff": fat_eff,
                "fiber_eff": fiber_eff,
                "fat_ratio": fat_ratio,
                "protein_ratio": protein_ratio,
                "fiber_per_carb": fiber_per_carb,
                "glycaemic_load_proxy": gl_proxy,
                "minutes_since_prev_meal": delta_min,
            }
        )

    return pd.DataFrame(meals)


def extract_all_meals(
    data_dir: Path | str, output_path: Optional[Path | str] = None
) -> pd.DataFrame:
    """Extract meal events for all participant CSVs and return a combined dataframe."""
    src = Path(data_dir)
    all_meals: List[pd.DataFrame] = []

    for f in sorted(src.glob("P*.csv")):
        pid = f.stem
        m_df = extract_participant_meals(f, pid)
        if not m_df.empty:
            all_meals.append(m_df)

    if not all_meals:
        return pd.DataFrame()

    combined = pd.concat(all_meals, ignore_index=True)
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        combined.to_parquet(out, index=False)
        logger.info("Saved %d meal events to %s", len(combined), out)

    return combined
