# Aegis Baselines Evaluation Summary (Phase A3)

- **Dataset Version:** `v1.0.0-c0425ca91dfa9819`
- **Git Commit:** `b48e57333722e562c608354d76d32558349f43dd`
- **Evaluation Scheme:** 5-fold grouped cross-validation stratified at patient level
- **Sample Count:** 54 meals

## Overall Held-Out Performance (Primary Window: 0–120 min)

| Baseline ID | Description | MAE (0–120) [95% CI] | RMSE (0–120) | MAE (120–180) | Peak Error (mg/dL) |
|---|---|---|---|---|---|
| `B0_persistence` | Persistence Floor (ΔG = 0) | **50.03** [39.76, 60.19] | 51.75 | 36.79 | 62.60 |
| `B1_pop_mean` | Population Meal Mean Curve | **17.36** [7.81, 26.98] | 18.76 | 20.04 | 20.69 |
| `B2_ridge` | Multi-Output Ridge Regression | **17.80** [7.76, 28.04] | 19.20 | 20.48 | 21.38 |
| `B3_gbdt` | Gradient Boosted Trees (HistGBDT) | **22.00** [14.87, 28.96] | 23.55 | 24.09 | 26.29 |
| `B4_patient_mean` | Per-Patient Historical Mean | **22.00** [14.87, 28.96] | 23.55 | 24.09 | 26.29 |
