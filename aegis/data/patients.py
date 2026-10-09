"""Parsing and standardization of static clinical patient profiles from bio.csv."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

POUNDS_TO_KG = 0.45359237
INCHES_TO_CM = 2.54


def parse_patient_profiles(bio_csv_path: Path | str) -> pd.DataFrame:
    """Parse bio.csv into the canonical patients dataframe."""
    p = Path(bio_csv_path)
    if not p.exists():
        raise FileNotFoundError(f"bio.csv not found at: {p}")

    df = pd.read_csv(p)

    # Standardize column mappings
    pid_col = "Participant ID" if "Participant ID" in df.columns else "patient_id"
    group_col = "Group" if "Group" in df.columns else "group"
    age_col = "Age" if "Age" in df.columns else "age"
    gender_col = "Gender" if "Gender" in df.columns else "sex"
    bmi_col = "BMI" if "BMI" in df.columns else "bmi"
    weight_col = "Body weight (pounds)" if "Body weight (pounds)" in df.columns else "weight_lbs"
    height_col = "Height (inches)" if "Height (inches)" in df.columns else "height_in"
    a1c_col = "A1c" if "A1c" in df.columns else "hba1c"
    fasting_g_col = "Fasting glucose" if "Fasting glucose" in df.columns else "fasting_glucose"
    insulin_col = "Insulin" if "Insulin" in df.columns else "fasting_insulin"
    tg_col = "Triglycerides" if "Triglycerides" in df.columns else "triglycerides"
    hdl_col = "HDL" if "HDL" in df.columns else "hdl"
    ldl_col = "LDL" if "LDL" in df.columns else "ldl"

    clean_patients = []
    for _, row in df.iterrows():
        pid = str(row[pid_col]).strip()
        weight_lbs = float(row[weight_col]) if pd.notna(row[weight_col]) else None
        height_in = float(row[height_col]) if pd.notna(row[height_col]) else None

        weight_kg = round(weight_lbs * POUNDS_TO_KG, 2) if weight_lbs else None
        height_cm = round(height_in * INCHES_TO_CM, 2) if height_in else None

        # Derive group if missing
        a1c = float(row[a1c_col]) if pd.notna(row[a1c_col]) else None
        if group_col in row and pd.notna(row[group_col]):
            group = str(row[group_col]).lower().strip()
        else:
            if a1c and a1c >= 6.5:
                group = "t2d"
            elif a1c and a1c >= 5.7:
                group = "prediabetes"
            else:
                group = "healthy"

        clean_patients.append(
            {
                "patient_id": pid,
                "source_id": pid,
                "group": group,
                "age": float(row[age_col]) if pd.notna(row[age_col]) else None,
                "sex": str(row[gender_col]).lower().strip()
                if pd.notna(row[gender_col])
                else "unknown",
                "bmi": float(row[bmi_col]) if pd.notna(row[bmi_col]) else None,
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "hba1c": a1c,
                "fasting_glucose": float(row[fasting_g_col])
                if pd.notna(row[fasting_g_col])
                else None,
                "fasting_insulin": float(row[insulin_col]) if pd.notna(row[insulin_col]) else None,
                "triglycerides": float(row[tg_col]) if pd.notna(row[tg_col]) else None,
                "hdl": float(row[hdl_col]) if pd.notna(row[hdl_col]) else None,
                "ldl": float(row[ldl_col]) if pd.notna(row[ldl_col]) else None,
            }
        )

    out_df = pd.DataFrame(clean_patients)
    return out_df
