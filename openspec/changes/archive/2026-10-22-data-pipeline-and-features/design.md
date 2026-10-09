# Design: Data Pipeline, Synthetic EHR, and Feature Engineering

## Context

Aegis predicts 180-min post-meal glucose excursions from static clinical profiles and dynamic sensor streams. The raw CGMacros dataset comprises 45 participants (~10 days each) with 1-min sampling across Dexcom G6, Libre Pro, and Fitbit. `AGENTS.md` mandates zero data leakage, reproducible splits, and no fabricated values.

## Goals / Non-Goals

**Goals:**
- Provide reproducible cleaning and resampling to uniform 5-min intervals with explicit interpolation flags.
- Extract `patients` and `meals` tables with verified unit conversions and effective macros.
- Generate deterministic synthetic EHR context in pure Python (Decision D14).
- Extract unified feature vectors (`seq [12, 6]`, `static [8]`, `meal [16]`, `anchor [4]`) with explicit wearable missingness masks (Decision D15).
- Calculate Mahalanobis/convex-hull OOD support scores for meals (Decision D16).
- Create patient-grouped stratified 5-fold cross-validation splits with zero patient overlap.
- Pass all 6 leakage prevention tests and generate `data/MANIFEST.json` (Checkpoint C1).

**Non-Goals:**
- Training machine learning models (Batch 3).
- Real-time WebSocket streaming (Batch 6).

## Decisions

- **Primary Sensor (D2):** Dexcom G6 5-minute sampling is used as primary glucose; Libre Pro is stored as auxiliary sensor signal.
- **Python Synthetic EHR (D14):** Generate clinical EHR data using standard Python distributions (NHANES-based age/BMI/BP parameters) seeded with `seed=42`.
- **Sensor Missingness Resilience (D15):** The sequence tensor incorporates 3 dedicated binary mask channels (glucose, HR, METs) and zero-imputed z-scores.
- **Support Score Guardrail (D16):** Standardized Euclidean / Mahalanobis distance to training meal macros determines out-of-distribution flags.
- **Split Strategy:** Stratified by diabetes status (`healthy`, `prediabetes`, `t2d`) on patient level only.

## Risks / Trade-offs

- **Small Cohort Size:** 45 total participants (14 T2D). Patient-level splits leave ~9 patients per test fold. Group stratification ensures representative distribution in every fold.
- **Missing Sensor Data:** Heavy dropout in HR and METs is common. Masking ensures models do not fail on incomplete sensor streams.
