"""Generate realistic attributed demo subset in data/demo/ for offline development and testing."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def create_demo_data(dest_dir: Path | str, seed: int = 42) -> None:
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    # 1. LICENSE-DATA and ATTRIBUTION.md
    license_file = dest / "LICENSE-DATA"
    license_file.write_text(
        "CGMacros dataset subset and synthetic derivatives licensed under CC BY-NC-SA 4.0.\n"
        "Attribution required: Gutierrez-Osuna et al. (2025), PhysioNet, doi:10.13026/3z8q-x658.\n"
        "Non-commercial use only. Share-alike applies to derivative adaptations.\n",
        encoding="utf-8",
    )

    attr_file = dest / "ATTRIBUTION.md"
    attr_file.write_text(
        "# Data Attribution and Provenance Notice\n\n"
        "This directory contains synthetic fixtures and small attributed subsets modeled after:\n"
        "- **Dataset**: CGMacros: Continuous Glucose Monitoring and Macronutrient Intake (v1.0.0)\n"
        "- **Authors**: Gutierrez-Osuna et al., Sansum Diabetes Research Institute / Texas A&M\n"
        "- **DOI**: 10.13026/3z8q-x658 (PhysioNet)\n"
        "- **Licence**: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International\n",
        encoding="utf-8",
    )

    # 2. bio.csv (demographics & screening labs)
    # Covering healthy (P001-P002), prediabetes (P010-P011), t2d (P020-P022)
    demo_patients = [
        {
            "Participant ID": "P001",
            "Gender": "Female",
            "Age": 28,
            "Height (inches)": 65.0,
            "Body weight (pounds)": 132.0,
            "BMI": 22.0,
            "A1c": 5.2,
            "Fasting glucose": 88.0,
            "Insulin": 6.5,
            "Triglycerides": 95.0,
            "HDL": 58.0,
            "LDL": 105.0,
            "Group": "healthy",
        },
        {
            "Participant ID": "P002",
            "Gender": "Male",
            "Age": 34,
            "Height (inches)": 70.0,
            "Body weight (pounds)": 165.0,
            "BMI": 23.7,
            "A1c": 5.4,
            "Fasting glucose": 92.0,
            "Insulin": 7.2,
            "Triglycerides": 110.0,
            "HDL": 52.0,
            "LDL": 112.0,
            "Group": "healthy",
        },
        {
            "Participant ID": "P010",
            "Gender": "Male",
            "Age": 48,
            "Height (inches)": 69.0,
            "Body weight (pounds)": 195.0,
            "BMI": 28.8,
            "A1c": 6.0,
            "Fasting glucose": 110.0,
            "Insulin": 14.5,
            "Triglycerides": 165.0,
            "HDL": 44.0,
            "LDL": 128.0,
            "Group": "prediabetes",
        },
        {
            "Participant ID": "P011",
            "Gender": "Female",
            "Age": 52,
            "Height (inches)": 64.0,
            "Body weight (pounds)": 178.0,
            "BMI": 30.5,
            "A1c": 6.2,
            "Fasting glucose": 115.0,
            "Insulin": 16.0,
            "Triglycerides": 180.0,
            "HDL": 42.0,
            "LDL": 134.0,
            "Group": "prediabetes",
        },
        {
            "Participant ID": "P020",
            "Gender": "Female",
            "Age": 58,
            "Height (inches)": 63.0,
            "Body weight (pounds)": 185.0,
            "BMI": 32.8,
            "A1c": 7.4,
            "Fasting glucose": 138.0,
            "Insulin": 22.0,
            "Triglycerides": 210.0,
            "HDL": 38.0,
            "LDL": 142.0,
            "Group": "t2d",
        },
        {
            "Participant ID": "P021",
            "Gender": "Male",
            "Age": 61,
            "Height (inches)": 71.0,
            "Body weight (pounds)": 225.0,
            "BMI": 31.4,
            "A1c": 7.8,
            "Fasting glucose": 145.0,
            "Insulin": 24.5,
            "Triglycerides": 225.0,
            "HDL": 36.0,
            "LDL": 148.0,
            "Group": "t2d",
        },
    ]
    bio_df = pd.DataFrame(demo_patients)
    bio_df.to_csv(dest / "bio.csv", index=False)

    # 3. Per-participant 1-minute time series CSVs (3 days per participant)
    start_time = datetime(2026, 10, 1, 0, 0)
    total_minutes = 3 * 24 * 60  # 3 days = 4320 minutes

    for p in demo_patients:
        pid = p["Participant ID"]
        baseline_g = p["Fasting glucose"]
        is_t2d = p["Group"] == "t2d"

        timestamps = [start_time + timedelta(minutes=i) for i in range(total_minutes)]
        dexcom = np.zeros(total_minutes)
        libre = np.zeros(total_minutes)
        hr = np.zeros(total_minutes)
        mets = np.zeros(total_minutes)
        activity_cal = np.zeros(total_minutes)
        meal_types = [""] * total_minutes
        calories = np.zeros(total_minutes)
        carbs = np.zeros(total_minutes)
        protein = np.zeros(total_minutes)
        fat = np.zeros(total_minutes)
        fiber = np.zeros(total_minutes)
        amount_consumed = np.zeros(total_minutes)

        # Baseline physiology + circadian variation
        for i, t in enumerate(timestamps):
            circadian = 5.0 * math.sin(2 * math.pi * (t.hour + t.minute / 60.0) / 24.0)
            noise = rng.normal(0, 1.5)
            dexcom[i] = baseline_g + circadian + noise
            hr[i] = 72.0 + rng.normal(0, 4.0)
            mets[i] = 1.0 + max(0.0, rng.normal(0.1, 0.2))
            activity_cal[i] = mets[i] * 1.2

        # Inject 3 meals per day: Breakfast (08:00), Lunch (13:00), Dinner (19:00)
        for day in range(3):
            meal_schedules = [
                (8, 0, "breakfast", 350, 45, 20, 10, 5),
                (13, 0, "lunch", 600, 75, 25, 22, 6),
                (19, 0, "dinner", 750, 90, 30, 28, 8),
            ]
            for m_hour, m_min, m_type, cal, c, pr, f, fib in meal_schedules:
                idx = day * 1440 + m_hour * 60 + m_min
                if idx < total_minutes:
                    meal_types[idx] = m_type
                    calories[idx] = cal
                    carbs[idx] = c
                    protein[idx] = pr
                    fat[idx] = f
                    fiber[idx] = fib
                    amount_consumed[idx] = 100.0

                    # Simulate post-prandial excursion over 180 min
                    peak_amp = (c * (1.2 if is_t2d else 0.7)) + rng.normal(0, 3.0)
                    t_peak = 60.0 if not is_t2d else 80.0
                    for k in range(180):
                        if idx + k < total_minutes:
                            # Gamma curve response
                            tau = k / t_peak
                            resp = peak_amp * (tau * math.exp(1 - tau))
                            dexcom[idx + k] += max(0.0, resp)

        # Dexcom 5-min discretization & Libre 15-min discretization
        for i in range(total_minutes):
            if i % 5 != 0:
                dexcom[i] = dexcom[i - (i % 5)]  # repeated forward in 1-min rows
            if i % 15 != 0:
                libre[i] = dexcom[i - (i % 15)] + rng.normal(0, 3.0)
            else:
                libre[i] = dexcom[i] + rng.normal(0, 3.0)

        # Clamp glucose to sensor bounds 40-400 mg/dL
        dexcom = np.clip(dexcom, 40.0, 400.0)
        libre = np.clip(libre, 40.0, 400.0)

        df = pd.DataFrame(
            {
                "Timestamp": [t.strftime("%m/%d/%Y %H:%M") for t in timestamps],
                "Libre GL": libre,
                "Dexcom GL": dexcom,
                "HR": hr,
                "Calories (Activity)": activity_cal,
                "Mets": mets,
                "Meal Type": meal_types,
                "Calories": calories,
                "Carbs": carbs,
                "Protein": protein,
                "Fat": fat,
                "Fiber": fiber,
                "Amount Consumed": amount_consumed,
                "Image Path": ["" for _ in range(total_minutes)],
            }
        )

        df.to_csv(dest / f"{pid}.csv", index=False)


if __name__ == "__main__":
    create_demo_data("data/demo")
    print("Demo dataset generated successfully in data/demo/")
