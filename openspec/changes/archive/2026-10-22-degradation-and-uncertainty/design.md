# Design Document: Uncertainty Quantification, Degradation Resilience, and Model Export

## Architecture & Data Flow

```
                      Raw Input Sample
                             │
                             ▼
              ┌──────────────────────────────┐
              │ aegis.degradation.scenarios  │
              │  (Applies D0-D7 Transforms)  │
              └──────────────┬───────────────┘
                             │ Degraded Features & Masks
                             ▼
              ┌──────────────────────────────┐
              │  Candidate S GRU Forecaster  │
              │   + Few-Shot Personalisation │
              └──────────────┬───────────────┘
                             │ Point Trajectory y_hat
                             ▼
              ┌──────────────────────────────┐
              │  aegis.uncertainty.conformal │
              │   (q_t from calibration)     │
              └──────────────┬───────────────┘
                             │ Intervals [y_hat - q_t, y_hat + q_t]
                             ▼
              ┌──────────────────────────────┐
              │ aegis.uncertainty.reliability│
              │  (HIGH / MODERATE / LOW)     │
              └──────────────┬───────────────┘
                             │
                             ▼
                   Inference / Replay Output
```

## 1. Degradation Scenarios (D0–D7)
All degradation operations take the historical sequence tensor $X \in \mathbb{R}^{B \times 24 \times 8}$ (or single sample), the static clinical vector, and the meal dictionary.
- **D0 (None):** Unmodified identity.
- **D1 (CGM Dropout $N$ min):** For $N \in \{15, 30, 60\}$ minutes (which corresponds to $k = N/5$ time steps), mask the last $k$ steps: set `glucose` values to 0.0 and `glucose_mask` to 0.0. The `anchor_age_min` metadata is updated to $N$ minutes.
- **D2 (CGM Gaps):** Randomly drop CGM measurements with rate $r \in \{0.2, 0.5\}$ by setting `glucose_mask = 0` and `glucose = 0`.
- **D3 (Wearables Missing):** Zero out heart rate and METs, setting `hr_mask = 0` and `mets_mask = 0`.
- **D4 (Reduced-Sensor Mode):** Complete absence of CGM in the 120-min window (`glucose_mask = 0` for all 24 steps). Glucose anchor falls back to fasting glucose from patient clinical profile, and `anchor_age_min` is marked 720 minutes.
- **D5 (Meal Incomplete):** Carbs, protein, fat, or fiber set to population median defaults for that meal type, flagged as estimated.
- **D6 (Cold Start):** Target patient has $K=0$ historical meals; prediction relies on similarity-weighted neighbor prior.
- **D7 (Out of Support):** Support score distance exceeds threshold; physiological clamping to $[40, 400]\text{ mg/dL}$ applied, reliability forced to `LOW`.

## 2. Split-Conformal Uncertainty Intervals
- For calibration samples $i \in \{1, \dots, n_{cal}\}$, compute absolute residuals:
  $$R_{i, t} = |y_{i, t} - \hat{y}_{i, t}| \quad \text{for each horizon step } t \in \{1, \dots, 36\}$$
- Finite-sample calibrated quantile $q_{t, 1-\alpha}$ at level $1-\alpha$ (e.g. 80% and 90%):
  $$k = \lceil (n_{cal} + 1)(1 - \alpha) \rceil, \quad q_{t, 1-\alpha} = \text{order-statistic}_{(k)}(R_{\cdot, t})$$
- Serialized in JSON format with horizon-wise upper and lower offsets for each scenario $s \in \{\text{D0, D1\_15m, D1\_30m, D1\_60m, D2, D3, D4, D5, D7}\}$.
- If test coverage $< (1-\alpha) - 0.05$ due to distribution shift, an empirical inflation multiplier is logged.

## 3. Reliability Assessment Engine
Rules:
- `HIGH`: Scenario is D0, $K \ge 3$ personal meals, support score $\ge 0.5$, no missing sensor masks, mean interval width $\le 30\text{ mg/dL}$.
- `MODERATE`: Mild degradation (e.g., D1 with $N \le 30$, D2 with $r \le 0.2$, D3 missing wearables, or $1 \le K < 3$), interval width $\le 45\text{ mg/dL}$.
- `LOW`: Reduced sensor D4, CGM dropout $> 30$ min, $K=0$, out-of-support D7, or interval width $> 45\text{ mg/dL}$.
- Returns user-facing clinician rationale string suitable for UI display.

## 4. Export Bundle
`aegis/training/export.py` writes to `artifacts/bundle/`:
- `model.pt`: Candidate S torch state dict.
- `pca_basis.json`: PCA components ($3 \times 36$) and mean trajectory.
- `similarity_priors.json`: Normalized patient profile embeddings and ridge coefficient vectors.
- `uncertainty_table.json`: Conformal quantile tables per scenario and horizon.
- `metadata.json`: Model version, training git commit, metric performance, input feature schema.
- Clean loader function: `bundle = load_aegis_bundle("artifacts/bundle")`.
