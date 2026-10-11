# Tasks: Uncertainty Quantification, Degradation Resilience, and Model Export

## 1. Degradation Scenarios (A6.1)

- [x] 1.1 Implement `aegis/degradation/scenarios.py` with functional transforms for D0–D7.
- [x] 1.2 Write unit tests in `tests/test_degradation.py` testing each scenario D0–D7, shape preservation, and mask integrity.

## 2. Conformal Prediction & Calibration (A6.2)

- [x] 2.1 Implement `aegis/uncertainty/conformal.py` for horizon-wise split-conformal calibration and interval generation.
- [x] 2.2 Compute and write `uncertainty_table.json` across all degradation scenarios.
- [x] 2.3 Write tests in `tests/test_uncertainty.py` verifying interval coverage, monotonic width, and schema validity.

## 3. Reliability Assessment (A6.3)

- [x] 3.1 Implement `aegis/uncertainty/reliability.py` with deterministic rules and clinician-facing explanatory messages.
- [x] 3.2 Write tests in `tests/test_uncertainty.py` verifying correct label assignment for high, moderate, and low confidence conditions.

## 4. Degradation Evaluation & Reporting (A6.4)

- [x] 4.1 Implement `aegis/evaluation/eval_degradation.py` evaluating Candidate S under all degradation scenarios.
- [x] 4.2 Generate `reports/degradation_summary.md` and `reports/uncertainty_coverage.md`.

## 5. Model Export & Bundle Loader (A6.5)

- [x] 5.1 Implement `aegis/training/export.py` exporting full artifact bundle (`model.pt`, `pca_basis.json`, `uncertainty_table.json`, `metadata.json`).
- [x] 5.2 Implement `load_aegis_bundle` and write round-trip loading tests.
