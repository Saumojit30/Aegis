# Tasks: Data Pipeline, Synthetic EHR, and Feature Engineering

## 1. Ingestion & Synthetic Fixtures (A1.2, A2.8)

- [x] 1.1 Implement `aegis/data/download.py` for downloading CGMacros and checksum verification.
- [x] 1.2 Implement `scripts/build_demo_data.py` to generate an attributed, realistic demo dataset in `data/demo/`.

## 2. Cleaning & Canonical Tables (A2.1, A2.2)

- [x] 2.1 Implement `aegis/data/clean.py` for timestamp parsing, unit conversion, 5-min resampling, and gap interpolation <= 15 min.
- [x] 2.2 Implement `aegis/data/patients.py` to parse screening demographics/labs from `bio.csv`.
- [x] 2.3 Implement `aegis/data/meals.py` to identify meal start events and calculate effective macronutrients.

## 3. Synthetic EHR Generation (A2.3, D14)

- [x] 3.1 Implement `aegis/data/ehr_synthetic.py` generating deterministic synthetic diagnoses, medications, and blood pressure observations matched to patient profiles.
- [x] 3.2 Ensure `synthetic_pairing=true` and pairing distance are permanently tagged.

## 4. Shared Feature Engineering (A2.4, D15, D16)

- [x] 4.1 Implement `aegis/features/extract.py` creating sequence, static, meal, and anchor feature tensors.
- [x] 4.2 Include explicit sensor missingness masks in `seq` tensor (`glucose_mask`, `hr_mask`, `mets_mask`) (D15).
- [x] 4.3 Implement `aegis/features/support.py` calculating OOD support scores against training meal distributions (D16).

## 5. Sample Construction & Leakage Validation (A2.5, A2.6)

- [x] 5.1 Implement `aegis/data/samples.py` packaging meals, history, static features, and 36-step trajectory targets.
- [x] 5.2 Implement `aegis/data/splits.py` generating stratified grouped 5-fold splits saved to `data/processed/splits.json`.
- [x] 5.3 Implement `aegis/data/validate.py` executing the 6 non-negotiable leakage tests and generating `data/MANIFEST.json` (Checkpoint C1).
- [x] 5.4 Write unit test suite in `tests/` verifying pipeline, features, synthetic EHR, and zero patient leakage.
