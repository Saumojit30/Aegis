"""Pure Python deterministic clinical synthetic EHR generator (Decision D14).

Generates synthetic comorbidities, medication regimens, and blood pressure histories
matched to real screening demographics and labs without Java/Synthea dependencies.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def generate_synthetic_ehr_for_patients(
    patients_df: pd.DataFrame,
    seed: int = 42,
    output_dir: Path | str | None = None,
) -> Dict[str, Any]:
    """Generate deterministic synthetic EHR profiles and BP observations for a cohort.

    Returns:
        Dictionary with 'ehr_profiles' (DataFrame) and 'bp_observations' (DataFrame).
    """
    rng = np.random.default_rng(seed)

    ehr_records = []
    bp_records = []

    # Standard reference baseline start date for BP history (last 6 months)
    ref_end_date = datetime(2026, 10, 1)

    for _, p in patients_df.iterrows():
        pid = str(p["patient_id"])
        group = str(p.get("group", "healthy")).lower()
        age = float(p.get("age", 45))
        bmi = float(p.get("bmi", 25.0))
        hba1c = float(p.get("hba1c", 5.5))

        # 1. Generate Comorbidities / Diagnoses
        diagnoses = []
        medications = []

        if group == "t2d" or hba1c >= 6.5:
            diagnoses.append("E11.9: Type 2 diabetes mellitus without complications")
            medications.append("Metformin 500mg BID")
            if hba1c >= 7.5:
                medications.append("Empagliflozin 10mg daily")
            if bmi >= 30.0:
                diagnoses.append("E66.01: Morbid obesity due to excess calories")
        elif group == "prediabetes" or (5.7 <= hba1c < 6.5):
            diagnoses.append("R73.03: Prediabetes")

        # Hypertension probabilities based on age, BMI, and T2D status
        htn_risk = 0.2 + (0.01 * max(0, age - 30)) + (0.02 * max(0, bmi - 25))
        if group == "t2d":
            htn_risk += 0.25

        has_htn = rng.random() < min(0.85, htn_risk)
        if has_htn:
            diagnoses.append("I10: Essential (primary) hypertension")
            if age > 55 or bmi > 30:
                medications.append("Lisinopril 10mg daily")
            else:
                medications.append("Amlodipine 5mg daily")

        # Dyslipidemia
        if float(p.get("triglycerides", 100)) > 150 or float(p.get("ldl", 100)) > 130:
            diagnoses.append("E78.5: Hyperlipidemia, unspecified")
            medications.append("Atorvastatin 20mg daily")

        # 2. Baseline BP values
        if has_htn:
            base_sys = 135.0 + rng.normal(0, 5.0)
            base_dia = 85.0 + rng.normal(0, 4.0)
        else:
            base_sys = 116.0 + rng.normal(0, 4.0)
            base_dia = 74.0 + rng.normal(0, 3.0)

        # Generate 12 historical outpatient BP observations over 180 days
        for obs_idx in range(12):
            days_ago = 180 - (obs_idx * 15) + int(rng.integers(-2, 3))
            ts = ref_end_date - timedelta(days=days_ago, hours=int(rng.integers(8, 17)))
            sys_val = int(round(base_sys + rng.normal(0, 4.0)))
            dia_val = int(round(base_dia + rng.normal(0, 3.0)))

            bp_records.append(
                {
                    "patient_id": pid,
                    "ts": ts,
                    "systolic": sys_val,
                    "diastolic": dia_val,
                    "synthetic": True,
                }
            )

        # Pairing distance metric
        norm_age = (age - 50.0) / 15.0
        norm_bmi = (bmi - 27.0) / 6.0
        norm_a1c = (hba1c - 6.0) / 1.5
        pairing_dist = float(np.sqrt(norm_age**2 + norm_bmi**2 + norm_a1c**2))

        ehr_records.append(
            {
                "patient_id": pid,
                "synthetic_pairing": True,
                "synthea_patient_id": f"SYN-{pid}-{rng.integers(1000, 9999)}",
                "diagnoses": json.dumps(diagnoses),
                "medications": json.dumps(medications),
                "pairing_distance": round(pairing_dist, 4),
            }
        )

    ehr_df = pd.DataFrame(ehr_records)
    bp_df = pd.DataFrame(bp_records)

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        ehr_df.to_parquet(out / "ehr_profiles.parquet", index=False)
        bp_df.to_parquet(out / "bp_observations.parquet", index=False)
        logger.info(
            "Saved synthetic EHR profiles (%d) and BP observations (%d) to %s",
            len(ehr_df),
            len(bp_df),
            out,
        )

    return {"ehr_profiles": ehr_df, "bp_observations": bp_df}
