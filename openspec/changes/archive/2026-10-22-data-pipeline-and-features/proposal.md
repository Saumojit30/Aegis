# Proposal: Data Pipeline, Synthetic EHR, and Feature Engineering (Batch 2)

## Why

Aegis is an end-to-end digital twin system that combines a static clinical profile with a continuous physiological stream to predict post-meal glucose trajectories. To ensure scientific integrity and eliminate data leakage, the pipeline requires:
1. Automated ingestion and verification for the CGMacros v1.0.0 dataset (`bio.csv` and per-participant 1-min sensor logs).
2. Rigorous 5-minute grid resampling, gap interpolation (<= 15 min), and isolation of quarantined anomalies.
3. A deterministic, pure-Python clinical synthetic EHR generator (Decision D14) providing realistic medication, diagnosis, and blood pressure context without Java Synthea overhead.
4. A single, shared feature engineering module (`aegis/features`) with explicit sensor missingness indicators (Decision D15) and out-of-distribution support scoring (Decision D16).
5. Strictly grouped, stratified 5-fold patient splits guaranteeing zero cross-patient data leakage across training, validation, calibration, and test sets.
6. A reproducible dataset manifest (`MANIFEST.json`) meeting **Checkpoint C1**.

## What Changes

1. **Ingestion & Verification**: `aegis/data/download.py` to download CGMacros, verify SHA256 checksums, and generate attributed demo fixtures.
2. **Cleaning & Resampling**: `aegis/data/clean.py` to clean timestamps, convert units (pounds->kg, inches->cm), resample to 5-min intervals, and handle sensor discrepancies.
3. **Event Extraction**: `aegis/data/meals.py` and `aegis/data/patients.py` to extract canonical `patients` and `meals` tables with effective macronutrients.
4. **Synthetic EHR Generator**: `aegis/data/ehr_synthetic.py` creating matched clinical profiles (`ehr_profiles`, `bp_observations`) with `synthetic_pairing=true`.
5. **Unified Feature Module**: `aegis/features/extract.py` and `aegis/features/support.py` producing `seq`, `static`, `meal`, and `anchor` tensors with missingness masks.
6. **Sample Builder & Leakage Tests**: `aegis/data/samples.py` and `aegis/data/splits.py` producing `splits.json` with 6 explicit leakage checks.
7. **Validation & Manifest**: `aegis/data/validate.py` validating data shapes, distributions, and writing `data/MANIFEST.json`.

## Capabilities

### New Capabilities
- `data-pipeline`: Ingestion, cleaning, 5-minute resampling, meal event extraction, and sample building.
- `synthetic-ehr`: Deterministic pure-Python clinical EHR generator pairing synthetic comorbidities and BP history with CGMacros patients.
- `features`: Shared feature extraction producing model input tensors, wearable missingness masks, and OOD meal support scores.

### Modified Capabilities
None (new capabilities building on Phase A0 foundation).

## Impact

- Populates `data/processed/` and `data/demo/` with canonical Parquet and JSON files.
- Establishes the frozen feature extraction pipeline shared by future training, evaluation, and inference services.
- Unlocks Baseline modeling (Phase A3) and Checkpoint C1.
