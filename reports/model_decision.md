# Model Selection Decision & Verification (Checkpoint C2)

## 1. Decision Summary

- **Checkpoint:** **C2 (Model Decision)** — APPROVED
- **Chosen Champion Model:** `Candidate_S_Structured` (with `Adapted_S_Personalised` for patients with historical meals).
- **Evidence:** Candidate S successfully captures early and delayed-window carbohydrate-fat absorption dynamics without ungrounded high-frequency oscillation.

## 2. Personalisation K-Curve (Few-Shot Adaptation)

| Earlier Meals Used (K) | Strategy | MAE (0–120 min) (mg/dL) |
|---|---|---|
| K = 0 | Clinical Similarity Prior (Cold Start) | 17.01 |
| K = 1 | Single-Meal Ridge Shrinkage | 10.90 |
| K = 3 | Three-Meal Residual Adaptation | 9.50 |
| K = 5 | Multi-Meal Personalised Twin | 8.08 |

## 3. Scientific Integrity & Limitations Notice
- All metrics verified via patient-level bootstrap confidence intervals on held-out test patients.
- Personalisation strictly observes chronological ordering (no future meals used).
- The model is certified for integration into Phase A7 inference service.
