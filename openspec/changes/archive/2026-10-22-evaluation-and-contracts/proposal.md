# Proposal: Evaluation Harness, Baselines, and Contract Freeze (Batch 3)

## Why

Aegis is an evidence-based digital twin system where all reported claims, UI figures, and comparisons must originate from logged experiments with honest baselines and frozen interfaces:
1. **Evaluation Harness**: A standardized metrics evaluation module calculating trajectory MAE/RMSE across the 0–120 min, 120–180 min, and full 180 min horizons, peak error, time-to-peak error, iAUC, and patient-level paired bootstrap confidence intervals.
2. **Tabular Baselines (B0–B4)**: Establishing the performance floor and reference models:
   - B0: Persistence floor (`ΔG = 0`)
   - B1: Population mean response curve per meal type
   - B2: Ridge regression on tabular features
   - B3: Gradient Boosted Trees (HistGradientBoostingRegressor)
   - B4: Per-patient historical mean response
3. **Frozen System Contracts**: Strong Pydantic and OpenAPI schemas for `/predict`, `/simulate`, and model metadata, freezing the `[12, 6]` sequence, `[8]` static, `[16]` meal, `[4]` anchor, and `[36]` trajectory input/output contract before deep modeling and UI implementation.

## What Changes

1. **Evaluation Harness**: Create `aegis/evaluation/metrics.py` computing trajectory metrics, peak metrics, risk flags, and paired bootstrap confidence intervals.
2. **Baselines Suite**: Implement `aegis/models/baselines.py` implementing models B0 through B4 with scikit-learn.
3. **Baseline Evaluation Runner**: Implement `aegis/training/run_baselines.py` evaluating B0–B4 across all 5 cross-validation folds in `data/processed/splits.json` and logging metrics to MLflow via `start_tracked_run`.
4. **Contract Freeze**: Create `services/common/contracts.py` and `configs/schema.yaml` defining frozen request/response schemas for `/predict` and `/simulate`.
5. **Unit Tests**: Add tests verifying metric calculation against synthetic known curves, baseline predictions, and contract validation.

## Capabilities

### New Capabilities
- `evaluation`: Multi-horizon trajectory metrics, peak metrics, and patient-level bootstrap confidence interval calculation.
- `baselines`: Reference models B0 (persistence), B1 (population mean), B2 (ridge), B3 (GBDT), and B4 (per-patient mean).
- `contracts`: Frozen typed schemas for inference and what-if simulation requests/responses.

### Modified Capabilities
None (new capabilities building on Phase A1–A2 pipeline).

## Impact

- Establishes the quantitative benchmark that any future deep temporal model (Batch 4) must beat.
- Freezes API contracts so frontend and backend work can develop concurrently against deterministic schemas.
