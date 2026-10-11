# Split-Conformal Uncertainty Quantification & Coverage Report

> **Methodology:** Split-conformal prediction intervals computed on patient-held-out cross-validation residuals per 5-minute horizon step ($t \in [1..36]$).

## 1. Empirical Coverage vs Nominal Confidence (Target: 90.0%)

| Scenario ID | Target Coverage | Empirical Coverage (0-180m) | Coverage (0-120m) | Coverage (120-180m) | Mean Width (mg/dL) |
|---|---|---|---|---|---|
| **D0** | 90.0% | **96.1%** | 94.5% | 99.2% | 59.3 |
| **D1_15m** | 90.0% | **95.8%** | 94.4% | 98.6% | 61.0 |
| **D1_30m** | 90.0% | **95.8%** | 94.6% | 98.1% | 61.3 |
| **D1_60m** | 90.0% | **95.9%** | 94.7% | 98.3% | 61.0 |
| **D2_20** | 90.0% | **95.9%** | 94.4% | 99.1% | 60.0 |
| **D2_50** | 90.0% | **95.9%** | 94.5% | 98.6% | 59.8 |
| **D3** | 90.0% | **95.4%** | 94.1% | 98.0% | 60.8 |
| **D4** | 90.0% | **95.9%** | 94.7% | 98.3% | 61.0 |
| **D5** | 90.0% | **95.7%** | 94.1% | 98.8% | 82.8 |
| **D6** | 90.0% | **95.7%** | 94.2% | 98.6% | 78.6 |
| **D7** | 90.0% | **96.1%** | 94.5% | 99.2% | 59.3 |

## 2. Horizon-Wise Quantile Growth
As time from meal ingestion progresses from 0 to 180 minutes, uncertainty half-widths $q_t$ grow monotonically:

| Horizon Step | Time (min) | D0 Half-Width (90%) | D1_30m Half-Width (90%) | D4 Half-Width (90%) |
|---|---|---|---|---|
| Step 6 | 30 min | ±18.1 mg/dL | ±18.5 mg/dL | ±18.4 mg/dL |
| Step 12 | 60 min | ±23.4 mg/dL | ±24.5 mg/dL | ±24.2 mg/dL |
| Step 18 | 90 min | ±30.0 mg/dL | ±33.0 mg/dL | ±32.6 mg/dL |
| Step 24 | 120 min | ±37.8 mg/dL | ±38.3 mg/dL | ±38.3 mg/dL |
| Step 30 | 150 min | ±39.9 mg/dL | ±39.6 mg/dL | ±39.5 mg/dL |
| Step 36 | 180 min | ±39.9 mg/dL | ±39.6 mg/dL | ±39.5 mg/dL |

## 3. Calibration Validity
- Finite-sample conformal correction preserves $\ge 90\%$ empirical coverage across held-out test patients.
- No uncalibrated parametric assumptions (e.g. Gaussian error) are made.