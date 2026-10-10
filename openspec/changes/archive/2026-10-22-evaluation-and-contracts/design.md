# Design: Evaluation Harness, Baselines, and Contract Freeze

## Context

Aegis evaluates post-meal glucose trajectory predictions over a 180-minute window (36 steps at 5-min intervals). Per `AGENTS.md`, every metric in reports and UI must be traceable to logged runs, patient-level splits must be respected, and the final forecaster must beat tabular baselines on held-out patients or report the honest comparison.

## Goals / Non-Goals

**Goals:**
- Provide standard evaluation functions for MAE, RMSE (0–120, 120–180, 0–180 min), peak glucose error, time-to-peak error, and iAUC.
- Compute patient-level paired bootstrap 95% confidence intervals to measure statistical significance across small cohorts.
- Implement reference baselines B0, B1, B2, B3, and B4 using scikit-learn and NumPy.
- Train and evaluate all baselines across the 5 patient-level cross-validation folds in `data/processed/splits.json` with MLflow tracking.
- Freeze the `/predict` and `/simulate` API contracts in `services/common/contracts.py` and `configs/schema.yaml`.

**Non-Goals:**
- Deep learning neural network training (Batch 4).
- Conformal prediction intervals (Batch 5).
- Live WebSocket streaming (Batch 6).

## Decisions

- **Multi-Horizon Slicing:** Primary evaluation window is 0–120 min (steps 1..24); delayed window is 120–180 min (steps 25..36); full window is 0–180 min.
- **Bootstrap Level:** Bootstrap resampling occurs at the *patient* level, not the sample level, preserving within-patient correlation.
- **Tabular GBDT Architecture:** Multi-output regression using scikit-learn's `MultiOutputRegressor(HistGradientBoostingRegressor())` or `Ridge(alpha=1.0)` on flattened static + meal + anchor vectors.
- **Contract Schema Structure:** Pydantic v2 schemas enforcing non-negative macros, UTC ISO timestamps, and required origin labels (`model_driven` vs `assumption_driven`).

## Risks / Trade-offs

- **Small Cohort Size:** 6 demo patients or 45 full participants. Paired bootstrap over patient IDs provides honest variance estimates without over-claiming statistical power.
- **Delayed Window Noise:** Excursions in 120–180 min are sensitive to meal completion and gastric emptying. Separate reporting prevents early errors from skewing late assessment.
