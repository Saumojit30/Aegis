# Tasks: Evaluation Harness, Baselines, and Contract Freeze

## 1. Evaluation Harness (A3.1)

- [x] 1.1 Implement `aegis/evaluation/metrics.py` computing trajectory MAE/RMSE (0–120, 120–180, 0–180), peak error, time-to-peak error, and iAUC.
- [x] 1.2 Implement patient-level paired bootstrap confidence intervals (95% CI) and subgroup slice metrics (overall vs T2D).
- [x] 1.3 Write unit tests in `tests/test_metrics.py` verifying exact calculations against known synthetic trajectories.

## 2. Baselines B0–B4 (A3.2)

- [x] 2.1 Implement `aegis/models/baselines.py` with classes for B0 (Persistence), B1 (Population Mean), B2 (Ridge), B3 (GBDT), and B4 (Per-Patient Mean).
- [x] 2.2 Implement `aegis/training/run_baselines.py` to fit and evaluate B0–B4 across all 5 cross-validation folds in `data/processed/splits.json`.
- [x] 2.3 Wire MLflow run logging into baseline evaluation using `start_tracked_run` and generate `reports/baselines_summary.md`.

## 3. Contract Freeze (A3.3)

- [x] 3.1 Implement `services/common/contracts.py` with Pydantic request and response schemas for `/predict`, `/simulate`, and model metadata.
- [x] 3.2 Create `configs/schema.yaml` documenting input/output dimensions and constraints.
- [x] 3.3 Write unit tests in `tests/test_contracts.py` verifying request/response validation, serialization, and origin labels.
