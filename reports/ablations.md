# Aegis Model Ablations Report (Phase A4)

- **Dataset Version:** `v1.0.0-c0425ca91dfa9819`
- **Commit:** `a31b538f3b27f72e0377b183087e7d6d611fec69`
- **Evaluation Protocol:** 5-fold grouped cross-validation stratified at patient level

## Model Comparison on Held-Out Patients

| Architecture | Variant | MAE (0–120 min) [95% CI] | RMSE (0–120 min) | MAE (120–180 min) | Peak Error (mg/dL) |
|---|---|---|---|---|---|
| `Baseline B1` | Population Mean Curve | 17.36 [7.81, 26.98] | 18.76 | 20.04 | 20.69 |
| `Baseline B2` | Ridge Regression | 17.80 [7.76, 28.04] | 19.20 | 20.48 | 21.38 |
| `Baseline B3` | Tabular HistGBDT | 22.00 [14.87, 28.96] | 23.55 | 24.09 | 26.29 |
| `Candidate_U_Unstructured` | GRU + MLP Fusion (Direct 36-Step Head) | **49.03** [38.87, 59.14] | 50.78 | 35.86 | 60.33 |
| `Candidate_S_Structured` | GRU + Structured Fast/Slow Absorption Head | **12.95** [5.56, 21.43] | 14.05 | 15.84 | 15.69 |
| `Adapted_S_Personalised` | Candidate S + Few-Shot Residual Adaptation | **8.92** [5.69, 12.07] | 10.02 | 12.15 | 10.60 |
