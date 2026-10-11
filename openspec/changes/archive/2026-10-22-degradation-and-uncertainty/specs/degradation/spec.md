# Specification: Degradation Scenarios (D0–D7)

## Requirements

### REQ-DEG-01: Deterministic Transformation
The degradation engine SHALL provide pure, deterministic transforms parameterized by scenario ID and random seed.

### REQ-DEG-02: Scenario Definitions
The following scenarios SHALL be supported:
- **D0 (None):** Exact identity.
- **D1 (CGM Dropout):** For given duration $N \in \{15, 30, 60\}$ minutes, glucose values in the last $N/5$ time steps are set to 0.0 and `glucose_mask` set to 0.0. The `anchor_age_min` attribute is updated to $N$.
- **D2 (CGM Gaps):** Given dropout rate $r \in [0, 1)$, glucose entries are randomly masked (`glucose_mask = 0`, `glucose = 0.0`).
- **D3 (Wearables Missing):** `heart_rate` and `mets` channels zeroed, with `hr_mask = 0` and `mets_mask = 0`.
- **D4 (Reduced Sensor / No CGM):** All 24 historical glucose steps masked (`glucose_mask = 0`). The anchor glucose falls back to profile fasting glucose with `anchor_age_min = 720`.
- **D5 (Incomplete Meal):** Missing nutrient fields filled with meal-type population medians.
- **D6 (Cold-Start Patient):** Few-shot history meals $K=0$, forcing adaptation to use similarity prior.
- **D7 (Out of Support):** High-distance meal input flagged, bounding forecasts to physiological interval $[40, 400]\text{ mg/dL}$.

### REQ-DEG-03: Tensor Shape Invariance
All transforms applied to sequence tensors SHALL preserve the exact shape $(B, 24, 8)$ and data type (float32).
