"""Unit tests for patient-level splits and leakage prevention."""

from pathlib import Path

from aegis.data.clean import clean_participant_timeseries
from aegis.data.meals import extract_participant_meals
from aegis.data.patients import parse_patient_profiles
from aegis.data.samples import build_samples_for_cohort
from aegis.data.splits import generate_patient_level_splits
from aegis.data.validate import (
    build_dataset_manifest,
    verify_feature_shapes,
    verify_patient_split_disjointness,
    verify_temporal_no_future_leakage,
)


def test_splits_and_leakage_end_to_end(tmp_path: Path):
    demo_dir = Path(__file__).parent.parent / "data" / "demo"
    assert (demo_dir / "bio.csv").exists()

    # 1. Parse patients
    patients = parse_patient_profiles(demo_dir / "bio.csv")
    assert len(patients) >= 6

    # 2. Generate 5-fold splits
    splits = generate_patient_level_splits(patients, n_splits=5, seed=42)
    assert len(splits["folds"]) == 5

    # Test Leakage Rule 1: No patient appears in >1 set in any fold
    verify_patient_split_disjointness(splits)

    # 3. Clean timeseries and extract meals for one patient
    p_csv = demo_dir / "P001.csv"
    clean_sensor, _ = clean_participant_timeseries(p_csv, "P001")
    meals = extract_participant_meals(p_csv, "P001")

    # Test Leakage Rule 2: Temporal perturbation test
    t0 = meals.iloc[0]["ts_start"]
    verify_temporal_no_future_leakage(clean_sensor, t0)

    # 4. Build samples
    samples = build_samples_for_cohort(patients, meals, clean_sensor)
    assert len(samples) > 0

    # Test Feature Shapes
    verify_feature_shapes(samples)

    # 5. Checkpoint C1 Manifest
    manifest = build_dataset_manifest(
        patients, meals, clean_sensor, samples, tmp_path / "MANIFEST.json"
    )
    assert manifest["checkpoint_c1_status"] == "PASSED"
