# Specification: Conformal Uncertainty and Clinical Reliability

## Requirements

### REQ-UNC-01: Split-Conformal Calibration
The conformal quantification module SHALL compute empirical error quantiles:
$$q_{t, 1-\alpha} = \text{Quantile}\left(|y_t - \hat{y}_t|, \frac{\lceil (n+1)(1-\alpha) \rceil}{n}\right)$$
for every prediction horizon step $t \in \{1, \dots, 36\}$ (5-minute increments up to 180 minutes).

### REQ-UNC-02: Calibrated Quantile Table
The quantiles SHALL be persisted in `uncertainty_table.json` for target coverage levels $80\%$ ($\alpha=0.20$) and $90\%$ ($\alpha=0.10$), indexed by degradation scenario.

### REQ-UNC-03: Prediction Intervals
Inference intervals SHALL be constructed as:
$$\text{lower}_t = \max(40.0, \hat{y}_t - q_{t, 1-\alpha}), \quad \text{upper}_t = \min(400.0, \hat{y}_t + q_{t, 1-\alpha})$$
strictly respecting physiological glucose bounds $[40, 400]\text{ mg/dL}$.

### REQ-UNC-04: Reliability Engine
The reliability engine SHALL classify forecasts into:
- `HIGH`: Nominal operation (D0), complete sensor data, personal meals $K \ge 3$, interval width $\le 30\text{ mg/dL}$.
- `MODERATE`: Mild sensor gap or dropout ($N \le 30\text{ min}$), missing wearables (D3), or $1 \le K < 3$.
- `LOW`: Severe degradation (D4 reduced-sensor mode, CGM dropout $> 30\text{ min}$), out-of-support meal (D7), or interval width $> 45\text{ mg/dL}$.
A descriptive clinician message SHALL accompany each reliability assessment.
