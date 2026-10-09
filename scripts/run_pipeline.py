"""Run end-to-end data processing and validation on demo dataset."""

import json
import logging
from pathlib import Path

from aegis.data.clean import clean_all_participants
from aegis.data.ehr_synthetic import generate_synthetic_ehr_for_patients
from aegis.data.meals import extract_all_meals
from aegis.data.patients import parse_patient_profiles
from aegis.data.samples import build_samples_for_cohort
from aegis.data.splits import generate_patient_level_splits
from aegis.data.validate import (
    build_dataset_manifest,
    verify_feature_shapes,
    verify_patient_split_disjointness,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aegis.pipeline")


def run_pipeline(data_dir: str = "data/demo", output_dir: str = "data/processed") -> None:
    src = Path(data_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    logger.info("Step 1: Parsing static patient profiles from bio.csv...")
    patients_df = parse_patient_profiles(src / "bio.csv")
    patients_df.to_parquet(out / "patients.parquet", index=False)

    logger.info("Step 2: Cleaning and resampling sensor time series to 5-min grid...")
    sensor_df = clean_all_participants(src, out)

    logger.info("Step 3: Extracting meal events and computing effective macronutrients...")
    meals_df = extract_all_meals(src, out / "meals.parquet")

    logger.info("Step 4: Generating deterministic synthetic EHR layer (Decision D14)...")
    generate_synthetic_ehr_for_patients(patients_df, seed=42, output_dir=out)

    logger.info("Step 5: Generating patient-level 5-fold cross-validation splits...")
    splits_data = generate_patient_level_splits(
        patients_df, n_splits=5, seed=42, output_path=out / "splits.json"
    )
    verify_patient_split_disjointness(splits_data)
    logger.info("Leakage check PASSED: All folds strictly disjoint at patient level.")

    logger.info("Step 6: Building supervised forecasting samples (180-min horizon)...")
    samples = build_samples_for_cohort(patients_df, meals_df, sensor_df)
    verify_feature_shapes(samples)
    with open(out / "samples.json", "w", encoding="utf-8") as f:
        json.dump(samples, f)
    logger.info("Feature shape check PASSED for %d samples.", len(samples))

    logger.info("Step 7: Validating and creating dataset manifest (Checkpoint C1)...")
    manifest = build_dataset_manifest(
        patients_df, meals_df, sensor_df, samples, out / "MANIFEST.json"
    )
    logger.info("CHECKPOINT C1 MET: dataset_version=%s", manifest["dataset_version"])


if __name__ == "__main__":
    run_pipeline()
