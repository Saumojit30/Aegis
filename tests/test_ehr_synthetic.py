"""Unit tests for deterministic clinical synthetic EHR generator (Decision D14)."""

import json

import pandas as pd

from aegis.data.ehr_synthetic import generate_synthetic_ehr_for_patients


def test_generate_synthetic_ehr():
    patients = pd.DataFrame(
        [
            {"patient_id": "P001", "group": "healthy", "age": 28, "bmi": 22.0, "hba1c": 5.2},
            {"patient_id": "P020", "group": "t2d", "age": 58, "bmi": 32.5, "hba1c": 7.6},
        ]
    )

    ehr_data = generate_synthetic_ehr_for_patients(patients, seed=42)
    ehr_profiles = ehr_data["ehr_profiles"]
    bp_obs = ehr_data["bp_observations"]

    assert len(ehr_profiles) == 2
    assert (ehr_profiles["synthetic_pairing"]).all()

    # T2D patient check
    t2d_profile = ehr_profiles[ehr_profiles["patient_id"] == "P020"].iloc[0]
    diagnoses = json.loads(t2d_profile["diagnoses"])
    assert any("Type 2 diabetes" in d for d in diagnoses)

    # BP check
    assert not bp_obs.empty
    assert (bp_obs["synthetic"]).all()
    assert (bp_obs["systolic"] > 80).all() and (bp_obs["systolic"] < 220).all()


def test_synthetic_ehr_determinism():
    patients = pd.DataFrame(
        [{"patient_id": "P020", "group": "t2d", "age": 58, "bmi": 32.5, "hba1c": 7.6}]
    )

    run1 = generate_synthetic_ehr_for_patients(patients, seed=123)
    run2 = generate_synthetic_ehr_for_patients(patients, seed=123)

    assert (
        run1["ehr_profiles"].iloc[0]["pairing_distance"]
        == run2["ehr_profiles"].iloc[0]["pairing_distance"]
    )
    assert (run1["bp_observations"]["systolic"] == run2["bp_observations"]["systolic"]).all()
