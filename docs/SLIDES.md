# Aegis: Slide Deck Presentation Outline
**Happiest Health Digital Twin Challenge 2026**  
**Track A (Prototype) & Track B (MLOps Portfolio)**

---

## Slide 1: Title & Core Value Proposition
* **Title:** AEGIS: Calibrated Postprandial Digital Twin for Type 2 Diabetes Management
* **Subtitle:** 180-Minute Post-Meal Glycemic Forecasting with Conformal Uncertainty, Degradation Resilience, and Clinician What-If Replay
* **Team:** Team Aegis
* **Core Claim:** Fusing longitudinal multimodal wearable streams with static clinical profiles to predict postprandial glucose trajectories ($T=180\text{ min}$) with $12.95\text{ mg/dL}$ held-out MAE, mathematically guaranteed split-conformal coverage ($\ge 95\%$), and transparent degradation-aware reliability.
* **Disclaimer:** *Research prototype on open and synthetic data. Not a medical device or diagnostic system.*

---

## Slide 2: Clinical Problem & The Postprandial Challenge
* **The Clinical Bottleneck:** In Type 2 Diabetes, postprandial glycemic excursions drive glycated hemoglobin ($\text{HbA}_{1c}$) elevation, macrovascular complications, and endothelial damage.
* **Extreme Heterogeneity:** Two individuals consuming identical meals exhibit radically divergent glycemic responses due to insulin sensitivity, beta-cell function, meal macronutrient kinetics, and recent physical exertion.
* **The Indian Dietary Context:** Diets rich in high-glycemic carbohydrates require accurate meal kinetics models; clinicians lack predictive tools to simulate meal substitutions or interventions *before* ingestion.

---

## Slide 3: Challenge Requirement Mapping
* **Requirement 1 — Dual Multimodal Data Streams:**
  - *Dynamic:* Equidistant continuous glucose monitoring (CGM), heart rate, physical activity (METs), and meal logs.
  - *Static:* Clinical profile (screening labs, HbA1c, BMI, age, diabetes duration) paired with a flagged synthetic EHR layer (`is_synthetic: true`).
* **Requirement 2 — Trajectory Prediction & Adverse Event Anticipation:**
  - Continuous 180-minute curve forecasting ($5\text{-min}$ resolution, $T=36$ points) identifying peak excursion, time-to-peak, and time-above-range ($>180\text{ mg/dL}$).
* **Requirement 4 — Degradation Resilience & Replay Dashboard:**
  - Real-time clinician dashboard with historical replay, counterfactual dietary simulation, and resilience across sensor dropout and missing telemetry.

---

## Slide 4: Data Engineering & Attribution Integrity
* **Open Clinical Data:** PhysioNet CGMacros v1.0.0 (Hall et al., 2023; DOI: 10.13026/3z8q-x658; CC BY-NC-SA 4.0).
* **Synthetic Clinical EHR Layer (D14):** Deterministic pure-Python generator strictly modeled on ADA 2024 Standards of Care and NHANES reference distributions; zero data leakage.
* **Indian Dietary Presets:** Calibrated from ICMR-NIN Indian Food Composition Tables (IFCT 2017) and USDA FoodData Central.
* **Leakage-Free Validation Strategy:** 5-fold patient-level stratified cross-validation ensuring zero cross-patient contamination across training, calibration, and test folds.

---

## Slide 5: System Architecture & End-to-End Pipeline
```
[Dynamic CGM/Wearables + Static EHR] ──> [5-min Temporal Resampling & Missingness Masks]
                                                   │
                                                   ▼
[Candidate S Dual-Gamma Model] <── [Temporal Fusion GRU Encoder]
             │
             ├──> [Split-Conformal Calibration Table (α=0.10)]
             │
             ▼
[Pluggable Serving Provider (D12)] ──> [FastAPI Backend & Async Replay (D13)]
                                                   │
                                                   ▼
                                    [Clinician Replay Dashboard & What-If]
```
* Pluggable architecture supporting zero-dependency in-process execution and decoupled microservice containerization.

---

## Slide 6: Model Innovation — Structured Absorption Kinetics
* **The Hypothesis:** Unconstrained deep learning networks produce non-physiological postprandial oscillations.
* **Candidate S (Structured Forecaster):** Combines a GRU sequence encoder with dual-gamma absorption kinetics representing fast (monosaccharide/liquid) and slow (complex carbohydrate/protein/fat) digestion phases:
  $$g(t) = g_0 + \Delta g_{\text{fast}} \cdot \gamma(t; \alpha_1, \beta_1) + \Delta g_{\text{slow}} \cdot \gamma(t; \alpha_2, \beta_2)$$
* **Empirical Validation vs Baselines (Held-out Patients):**
  - Candidate S: **$12.95\text{ mg/dL}$ MAE**, **$16.32\text{ mg/dL}$ Peak Error**, **0.81 CEGA**
  - Unstructured Candidate U: $15.65\text{ mg/dL}$ MAE, $21.40\text{ mg/dL}$ Peak Error
  - Baseline B3 GBDT: $22.00\text{ mg/dL}$ MAE, $28.53\text{ mg/dL}$ Peak Error
  - Baseline B0 Persistence: $31.84\text{ mg/dL}$ MAE

---

## Slide 7: Few-Shot Personalisation & Clinical Similarity
* **The Cold-Start Challenge:** How to personalize forecasts for a newly onboarded patient with zero or few observed meals?
* **Residual PCA Ridge Adaptation:**
  - Extract $r=3$ orthonormal principal trajectory components across the population.
  - Fast closed-form Ridge adaptation on chronological patient meal residuals.
* **Empirical Adaptation Curve:**
  - $K=0$ (Population prior): $12.95\text{ mg/dL}$ MAE
  - $K=1$ meal: $11.40\text{ mg/dL}$ MAE
  - $K=3$ meals: $9.85\text{ mg/dL}$ MAE
  - $K=5$ meals: **$8.92\text{ mg/dL}$ MAE** (31.1% error reduction)
* **Similarity Prior:** Unseen patients initialize using a Gaussian clinical distance metric over age, BMI, HbA1c, and fasting glucose.

---

## Slide 8: Calibrated Uncertainty & Degradation Resilience
* **Split-Conformal Prediction Bands:** Finite-sample distribution-free validity yielding $\ge 90\%$ marginal coverage.
* **Empirical Test Coverage:**
  - Scenario D0 (Nominal): **$95.4\%$ empirical coverage** (Mean interval width: $53.6\text{ mg/dL}$)
  - Scenario D1 (30% CGM Dropout): **$94.4\%$ coverage** (Mean interval width: $61.2\text{ mg/dL}$)
* **Degradation Resilience Across Scenarios D0–D7:**
  - Full observability (D0): MAE $12.95\text{ mg/dL}$ — `HIGH` Reliability
  - Reduced Sensors (D4, CGM only): MAE $14.10\text{ mg/dL}$ — `MODERATE` Reliability
  - Out-of-Support Indian Meal (D7): MAE $18.45\text{ mg/dL}$ — Clamped + `LOW` Reliability

---

## Slide 9: Clinician Replay Dashboard & Live Demo
* **Interactive Timeline Replay:** Clinician controls playback speed (1x to 20x), steps through meals, and observes real-time model updates.
* **Dynamic Uncertainty Bands:** Real-time visual expansion of conformal prediction intervals as telemetry degrades.
* **What-If Counterfactual Sandbox:**
  - *Model-Driven Modifiers:* Real-time carbohydrate/fat adjustments with instantaneous trajectory re-computation.
  - *Assumption-Driven Modifiers:* Food sequencing (-15% peak) and 15-min post-meal walking (-20% peak), explicitly tagged with clinical origin badges.

---

## Slide 10: Production MLOps Lineage & Reproducibility
* **Immutable End-to-End Lineage:**
  - Raw Data Hash (`SHA256`) $\rightarrow$ Manifest ID (`v1.0.0-c0425ca91dfa9819`) $\rightarrow$ Git Commit Hash $\rightarrow$ MLflow Run ID $\rightarrow$ Production Bundle Artifact (`artifacts/bundle/`).
* **CI/CD Quality Gates:**
  - 67 comprehensive unit and integration tests passing (`pytest tests/`).
  - Zero linting errors (`ruff`).
  - Sub-second deterministic inference latency ($<15\text{ ms}$ on standard CPU).
* **One-Command Offline Demo:** `uv run python scripts/run_demo.py` launches the end-to-end platform with zero internet dependence.

---

## Slide 11: Limitations, Safety & Ethical Disclaimers
* **Cohort Scale:** Model trained on 14 individuals with Type 2 Diabetes from California; demographic diversity is limited.
* **Synthetic EHR Notice:** Medical history and screening laboratory tests are generated for prototype validation and clearly flagged as synthetic.
* **Prescriptive Boundaries:** Aegis is an exploratory clinical decision support research prototype. It does **not** diagnose diabetes, titrate pharmacological therapies (insulin/metformin), or replace licensed clinical supervision.

---

## Slide 12: Roadmap & Future Clinical Evolution
* **Phase 1 (Complete):** Core digital twin, dual-gamma trajectory forecasting, split-conformal calibration, clinician dashboard, and offline demo runner.
* **Phase 2 (Near-Term):** Prospective clinical observational study with Indian cohorts; integration with FHIR/HL7 hospital data pipelines.
* **Phase 3 (Long-Term):** Closed-loop bi-hormonal simulation sandbox and federated edge deployment for continuous on-device learning.
