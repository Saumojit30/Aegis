"""Unit tests for data cleaning, resampling, and meal extraction."""

from pathlib import Path

import pandas as pd

from aegis.data.clean import clean_participant_timeseries
from aegis.data.meals import extract_participant_meals
from aegis.data.patients import parse_patient_profiles


def test_clean_participant_timeseries(tmp_path: Path):
    # Create sample 1-min raw CSV
    csv_file = tmp_path / "P999.csv"
    data = {
        "Timestamp": [
            "10/01/2026 08:00",
            "10/01/2026 08:01",
            "10/01/2026 08:02",
            "10/01/2026 08:05",
            "10/01/2026 08:10",
            "10/01/2026 08:30",  # 20 min gap -> should stay missing
        ],
        "Dexcom GL": [100.0, 102.0, 104.0, 110.0, 120.0, 140.0],
        "Libre GL": [98.0, 99.0, 101.0, 108.0, 118.0, 138.0],
        "HR": [70.0, 71.0, 72.0, 75.0, 80.0, 85.0],
        "Mets": [1.0, 1.0, 1.0, 1.2, 1.5, 1.8],
        "Calories (Activity)": [1.2, 1.2, 1.2, 1.4, 1.8, 2.0],
        "Meal Type": ["breakfast", "", "", "", "", ""],
        "Calories": [400.0, 0, 0, 0, 0, 0],
        "Carbs": [50.0, 0, 0, 0, 0, 0],
        "Protein": [20.0, 0, 0, 0, 0, 0],
        "Fat": [15.0, 0, 0, 0, 0, 0],
        "Fiber": [5.0, 0, 0, 0, 0, 0],
        "Amount Consumed": [100.0, 0, 0, 0, 0, 0],
    }
    pd.DataFrame(data).to_csv(csv_file, index=False)

    clean_df, quarantined = clean_participant_timeseries(csv_file, "P999")
    assert not clean_df.empty
    assert "glucose_missing" in clean_df.columns
    assert "glucose_interpolated" in clean_df.columns
    assert clean_df.iloc[0]["glucose"] == 100.0
    assert clean_df.iloc[0]["patient_id"] == "P999"


def test_extract_participant_meals(tmp_path: Path):
    csv_file = tmp_path / "P999.csv"
    data = {
        "Timestamp": ["10/01/2026 08:00", "10/01/2026 13:00"],
        "Meal Type": ["breakfast", "lunch"],
        "Calories": [400.0, 600.0],
        "Carbs": [50.0, 70.0],
        "Protein": [20.0, 25.0],
        "Fat": [15.0, 20.0],
        "Fiber": [5.0, 6.0],
        "Amount Consumed": [50.0, 100.0],  # 50% eaten for breakfast
    }
    pd.DataFrame(data).to_csv(csv_file, index=False)

    meals_df = extract_participant_meals(csv_file, "P999")
    assert len(meals_df) == 2
    b_meal = meals_df.iloc[0]
    # 50% of 50g carbs = 25g effective carbs
    assert b_meal["carbs_eff"] == 25.0
    assert b_meal["calories_eff"] == 200.0
    assert b_meal["meal_id"] == "P999_M001"


def test_parse_patient_profiles(tmp_path: Path):
    bio_file = tmp_path / "bio.csv"
    data = {
        "Participant ID": ["P001", "P020"],
        "Group": ["healthy", "t2d"],
        "Age": [30, 60],
        "Gender": ["Female", "Male"],
        "BMI": [22.5, 33.0],
        "Height (inches)": [65.0, 70.0],
        "Body weight (pounds)": [135.0, 230.0],
        "A1c": [5.2, 7.5],
        "Fasting glucose": [88.0, 140.0],
        "Insulin": [6.0, 20.0],
        "Triglycerides": [90.0, 210.0],
        "HDL": [55.0, 38.0],
        "LDL": [100.0, 145.0],
    }
    pd.DataFrame(data).to_csv(bio_file, index=False)

    patients = parse_patient_profiles(bio_file)
    assert len(patients) == 2
    p1 = patients.iloc[0]
    assert p1["patient_id"] == "P001"
    assert p1["weight_kg"] == round(135.0 * 0.45359237, 2)
    assert p1["height_cm"] == round(65.0 * 2.54, 2)
