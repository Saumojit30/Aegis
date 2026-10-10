# Spec Delta: Baselines

## Purpose
Specifies standard reference forecasters B0–B4 against which complex temporal neural networks must be benchmarked.

## ADDED Requirements

### Requirement: Standard Reference Models B0–B4
The baseline suite MUST implement persistence floor (B0), population meal-mean curve (B1), multi-output ridge regression (B2), gradient-boosted decision trees (B3), and per-patient historical mean (B4).

#### Scenario: Running baseline predictions
- **WHEN** predicting for a test meal event
- **THEN** B0 MUST return `ΔG = 0` for all 36 steps
- **AND** B1 MUST return the historical mean curve for that meal type
- **AND** B2 and B3 MUST predict all 36 steps from static, meal, and anchor features.

### Requirement: Multi-Fold Cross-Validation Reporting
Baseline models MUST be trained and evaluated across all 5 cross-validation folds in `data/processed/splits.json` and logged to MLflow with mandatory tracking metadata.

#### Scenario: Running 5-fold baseline evaluation
- **WHEN** `run_baselines.py` is executed
- **THEN** metrics for B0, B1, B2, B3, and B4 MUST be logged per fold and overall
- **AND** every run MUST log `git_commit`, `dataset_version`, and `seed`.
