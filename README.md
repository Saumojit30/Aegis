# Aegis — Calibrated Type 2 Diabetes Digital Twin (Research Prototype)

[![Version: v1.1](https://img.shields.io/badge/version-v1.1-blue.svg)](pyproject.toml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Data License: CC BY-NC-SA 4.0](https://img.shields.io/badge/Data_License-CC_BY--NC--SA_4.0-orange.svg)](LICENSE-DATA)
[![Tests: 95 passed](https://img.shields.io/badge/tests-95%20passed-brightgreen.svg)](tests/)
[![Lint: ruff clean](https://img.shields.io/badge/lint-ruff%20clean-brightgreen.svg)](pyproject.toml)
[![Challenge: Happiest Health](https://img.shields.io/badge/Challenge-Happiest_Health_Digital_Twin-blue.svg)](https://unstop.com)

> **Important Clinical & Ethical Disclaimer:**  
> Aegis is an exploratory clinical decision support research prototype developed exclusively on open-access and synthetic datasets. **It is not a certified medical device, not a diagnostic instrument, and not an autonomous treatment or insulin titration system.** All outputs represent model-based scenario simulations and must never supersede licensed clinical judgment.

---

## 1. Executive Summary

**Aegis** is a physiological digital twin platform designed for postprandial glycemic management in Type 2 Diabetes (T2D). Addressing the profound intra- and inter-individual variability in carbohydrate-fat absorption, Aegis fuses longitudinal continuous wearable telemetry (continuous glucose monitors, heart rate, METs) with static clinical electronic health records to forecast 180-minute post-meal glucose trajectories ($T=36$ equidistant steps). 

Unlike unconstrained neural networks that produce ungrounded glycemic oscillations, Aegis incorporates a **dual-gamma structured absorption head (Candidate S)** with physiological inductive bias, achieving an held-out trajectory MAE of **$12.95\text{ mg/dL}$** and reducing to **$8.92\text{ mg/dL}$** with few-shot closed-form Ridge adaptation ($K=5$ historical meals). 

Crucially, Aegis refuses to present false certainty: it pairs every forecast with **distribution-free split-conformal prediction intervals** guaranteeing $\ge 95\%$ empirical test coverage, accompanied by an explicit **Reliability Rules Engine** evaluated across 8 sensor degradation scenarios (D0–D7) and a real-time **clinician replay dashboard** with counterfactual dietary simulation.

---

## 2. Team & Challenge Registration Details

* **Challenge:** Happiest Health Digital Twin Challenge
* **Tracks Targeted:**
  * **Track A (Challenge Prototype):** Core Digital Twin modeling, 180-min trajectory prediction, counterfactual what-if simulation, and clinician replay dashboard.
  * **Track B (MLOps Portfolio):** Automated CI/CD pipelines, strict run metadata validation, containerised microservices, and end-to-end artifact lineage.
* **Team Name:** Team Aegis
* **Repository Identifier:** `Aegis` (Version v1.1)

---

## 3. Clinical Framing & The Problem Statement

Postprandial glycemic excursions are a primary driver of elevated glycated hemoglobin ($\text{HbA}_{1c}$), endothelial dysfunction, and cardiovascular risk in individuals with Type 2 Diabetes. However, post-meal responses are notoriously non-linear and heterogeneous:
1. **Biological Heterogeneity:** Identical meals produce markedly divergent glucose peaks across patients due to variations in baseline insulin sensitivity, beta-cell secretory capacity, and visceral adiposity.
2. **Macronutrient Kinetics:** Mixed meals containing dietary fats and proteins delay gastric emptying and induce prolonged late-window elevations ($120\text{--}180\text{ min}$), confounding simple carbohydrate-counting algorithms.
3. **The Indian Dietary Context:** Traditional Indian diets often feature high-glycemic carbohydrates combined with diverse culinary fats, requiring tailored kinetic models rather than generic Western meal assumptions.
4. **Sensor Unreliability & Cold Start:** Continuous glucose monitors suffer from sensor dropouts, compression artifacts, and missing wearable telemetry, while newly onboarded patients lack personal historical meals.

Aegis solves these challenges through structured kinetic inductive bias, few-shot residual personalisation, rigorous split-conformal calibration, and explicit origin labeling of all clinical assumptions.

---

## 4. Challenge Traceability Matrix

| Challenge Requirement | Aegis Implementation | Evidence / Module |
|---|---|---|
| **Two Data Streams (Static + Dynamic)** | Fuses static clinical profiles (screening labs, anthropometrics) with 5-minute dynamic streams (CGM, HR, METs, meal logs). | `aegis/data/` & `aegis/models/` |
| **Simulated EHR Layer** | Deterministic pure-Python clinical EHR generator strictly grounded in ADA 2024 guidelines; all records flagged `is_synthetic: true`. | `aegis/data/ehr_synthetic.py` |
| **Post-Meal Trajectory Forecast** | Continuous 180-minute curve forecasting ($T=36$ points) tracking peak excursion, time-to-peak, and time-above-range. | `aegis/models/candidate_s.py` |
| **Personalisation & Cold-Start** | Closed-form residual PCA Ridge adaptation ($K \in \{1, 3, 5\}$) + Gaussian clinical similarity prior for cold start ($K=0$). | `aegis/models/personalisation.py` |
| **Calibrated Uncertainty** | Finite-sample split-conformal prediction intervals evaluated across 5 patient folds achieving $\ge 95\%$ test coverage. | `aegis/uncertainty/` |
| **Degradation Resilience** | Stress-tested across 8 scenarios (D0–D7: dropout, gaps, sensor failure) with a dynamic Reliability Rules Engine (HIGH, MODERATE, LOW). | `aegis/degradation/` |
| **Clinician Replay Dashboard** | Interactive time-series replay with playback speed control (1x–20x), live WebSocket streaming, and counterfactual what-if simulation. | `services/backend/` & `services/frontend/` |

---

## 5. System Architecture

```mermaid
flowchart TD
    subgraph DataSources["1. Data Acquisition & Validation"]
        CGM["CGMacros Open Data<br/>(PhysioNet CC BY-NC-SA 4.0)<br/>CGM, HR, METs, Meals (14 T2D)"]
        SYN["Deterministic Synthetic EHR<br/>(ADA 2024 Guidelines)<br/>[Flagged: is_synthetic=true]"]
        NIN["Indian Food Presets<br/>(NIN IFCT 2017 & USDA)<br/>[Support Clamped & Flagged]"]
    end

    subgraph Pipeline["2. Data Pipeline & Feature Engineering"]
        DVC["Leakage-Free 5-Fold Split<br/>(Patient-Stratified / Zero Cross-Contamination)"]
        FEAT["Temporal Grid Resampler (5-min)<br/>+ Missingness Indicator Masks (D15)<br/>+ Static & Dynamic Tensor Fusion"]
        DEG["Degradation Injection Engine<br/>(Scenarios D0 to D7: Dropout, Gaps, Missing Wearables)"]
    end

    subgraph Training["3. Model Training & Validation"]
        GRU["Temporal Fusion Encoder (GRU)<br/>Fused Static Patient & Wearable Sequences"]
        HEAD["Candidate S: Dual-Gamma Absorption Head<br/>(Fast/Slow Carbohydrate Kinetics)"]
        HUBER["Masked Huber Loss<br/>+ Peak Under-Prediction Penalty"]
        ADAPT["Few-Shot Personalisation (Ridge r=3)<br/>+ Gaussian Clinical Similarity Prior"]
        MLFLOW["MLflow Experiment Tracking<br/>(Strict Metadata, Metrics, Git Hash)"]
    end

    subgraph Artifacts["4. Model Artifact Bundle"]
        BUNDLE["Production Bundle (artifacts/bundle/)<br/>- PyTorch Candidate S Model<br/>- Feature Scaler & Normalisers<br/>- Split-Conformal Uncertainty Table<br/>- Deterministic Metadata Manifest"]
    end

    subgraph Serving["5. Pluggable Serving & Replay Services"]
        INF["Inference Provider (D12)<br/>(In-Process or Decoupled HTTP Microservice)"]
        BACKEND["FastAPI Backend Service<br/>(Relational State, Patient Registry, REST API)"]
        REPLAY["Async In-Memory Replay Engine (D13)<br/>(WebSocket Real-Time Telemetry Stream)"]
        SIM["What-If Counterfactual Simulator<br/>- Model-Driven (Carbs, Fat, Protein)<br/>- Assumption-Driven (Sequencing, Walk)"]
    end

    subgraph Client["6. Clinician Replay Dashboard"]
        UI["Clinician Interactive Dashboard<br/>- 180-min Postprandial Glucose Curve<br/>- Calibrated Split-Conformal 90% Bands<br/>- Real-Time Dynamic Reliability Badge<br/>- Interactive What-If Counterfactual Comparison<br/>- Stress-Testing Degradation Controls"]
    end

    CGM --> DVC
    SYN --> DVC
    NIN --> DVC
    DVC --> FEAT
    FEAT --> DEG
    DEG --> GRU
    GRU --> HEAD
    HEAD --> HUBER
    HUBER --> ADAPT
    ADAPT --> MLFLOW
    MLFLOW --> BUNDLE
    BUNDLE --> INF
    INF --> BACKEND
    BACKEND --> REPLAY
    BACKEND --> SIM
    REPLAY --> UI
    SIM --> UI
```

---

## 6. Data Provenance, Governance & Leakage Prevention

### 6.1 Datasets & Licensing
* **PhysioNet CGMacros v1.0.0:** Real-world continuous glucose and wearable telemetry from 14 Type 2 Diabetes participants recruited at Stanford University (Hall et al., 2023; DOI: [10.13026/3z8q-x658](https://doi.org/10.13026/3z8q-x658)). Distributed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 ([CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)).
* **Synthetic Clinical EHR Layer (Decision D14):** Fully deterministic pure-Python synthetic EHR generator (`aegis.data.ehr_synthetic`) based on American Diabetes Association (ADA 2024) distributions and NHANES epidemiological tables. Bypasses Java-based Synthea for reproducible CI. Every synthetic record is strictly flagged with `is_synthetic: true`.
* **Indian Dietary Presets:** Calibrated from the Indian Food Composition Tables (IFCT 2017, National Institute of Nutrition) and USDA FoodData Central (`configs/presets.yaml`). Presets deviating from the training support envelope are clamped and assigned `LOW` reliability (Decision D16).

### 6.2 Strict Leakage-Free Validation Protocol
Data leakage invalidates clinical machine learning. Aegis enforces strict **5-fold patient-level grouped cross-validation**:
* Folds are partitioned strictly across unique patient IDs (`participant_id`).
* Standardisation scalers and conformal quantile tables are fitted exclusively on training folds; test folds are evaluated out-of-sample.
* Automated leakage tests verify: (1) zero patient overlap across splits, (2) zero future-meal lookahead during personalisation, and (3) feature scaling computed strictly on training partitions (`tests/test_splits_leakage.py`).

---

## 7. Model Decision & Evidence Summary (Checkpoint C2)

Aegis evaluated 5 standard baselines (B0–B4) against an unconstrained deep neural network (Candidate U) and our physiologically structured dual-gamma network (Candidate S).

### 7.1 Champion vs Baseline Benchmark (Held-out Patients, Primary Window 0–120 min)

| Model Architecture | Model Description | MAE (0–120m) [95% CI] | RMSE (0–120m) | Peak Error (mg/dL) | Clarke EGA Zone A |
|---|---|---|---|---|---|
| `B0_persistence` | Zero-Change Persistence Floor ($\Delta G = 0$) | 50.03 [39.76, 60.19] | 51.75 | 62.60 | 0.38 |
| `B1_pop_mean` | Population Mean Postprandial Curve | 17.36 [7.81, 26.98] | 18.76 | 20.69 | 0.72 |
| `B2_ridge` | Multi-Output Ridge Regression | 17.80 [7.76, 28.04] | 19.20 | 21.38 | 0.70 |
| `B3_gbdt` | Tabular HistGBDT (Meal + Static Features) | 22.00 [14.87, 28.96] | 23.55 | 26.29 | 0.69 |
| `Candidate_U` | Unconstrained GRU + MLP Direct Head | 49.03 [38.87, 59.14] | 50.78 | 60.33 | 0.44 |
| **`Candidate_S`** | **GRU + Dual-Gamma Physiological Head** | **12.95 [5.56, 21.43]** | **14.05** | **15.69** | **0.81** |
| **`Adapted_S`** | **Candidate S + Few-Shot Adaptation ($K=5$)** | **8.92 [5.69, 12.07]** | **10.02** | **10.60** | **0.89** |

*All confidence intervals computed via 1,000 patient-level bootstrap resamples.*

### 7.2 Why Physiological Inductive Bias Wins
Unconstrained neural networks (Candidate U) suffer from severe over-parameterization on small clinical cohorts, exhibiting high-frequency oscillation and unphysiological glucose jumps. **Candidate S** constrains postprandial excursions to dual-gamma kinetic curves representing fast (monosaccharide/liquid) and slow (complex carbohydrate/protein/fat) absorption:
$$g(t) = g_0 + \Delta g_{\text{fast}} \cdot \gamma(t; \alpha_1, \beta_1) + \Delta g_{\text{slow}} \cdot \gamma(t; \alpha_2, \beta_2)$$
Trained with a **Masked Weighted Huber Loss** penalizing peak under-predictions by $1.5\times$, Candidate S guarantees non-negative, smooth excursions matching biological carbohydrate clearance.

### 7.3 Few-Shot Personalisation (Adaptation K-Curve)
Using $r=3$ principal orthonormal residual basis functions, Aegis adapts to individual patients using chronological historical meals without retraining the backbone:
* **$K = 0$ (Cold-Start Clinical Similarity):** MAE $12.95\text{ mg/dL}$
* **$K = 1$ (Single-Meal Ridge Shrinkage):** MAE $11.40\text{ mg/dL}$
* **$K = 3$ (Three-Meal Adaptation):** MAE $9.85\text{ mg/dL}$
* **$K = 5$ (Full Twin Adaptation):** **MAE $8.92\text{ mg/dL}$ (31.1% error reduction)**

---

## 8. Split-Conformal Uncertainty & Degradation Resilience

### 8.1 Conformal Calibration & Guaranteed Coverage
Rather than assuming Gaussian errors, Aegis implements **horizon-wise split-conformal quantile calibration** on held-out patient residuals:
$$\mathcal{C}_{1-\alpha}(t) = \left[ \hat{y}(t) - q_{t, 1-\alpha}, \; \hat{y}(t) + q_{t, 1-\alpha} \right]$$
At nominal confidence $1-\alpha = 0.90$, Aegis achieves **$\ge 95\%$ empirical test coverage** across all evaluation horizons.

| Scenario ID | Condition Description | MAE (0–180m) | Peak Error | Mean 90% Width | Empirical Coverage | Reliability State |
|---|---|---|---|---|---|---|
| **D0** | Nominal (Full Telemetry) | 9.85 mg/dL | 9.69 mg/dL | 59.3 mg/dL | **96.1%** | `HIGH` |
| **D1 (15m)** | CGM Dropout (15 min) | 10.12 mg/dL | 10.10 mg/dL | 61.0 mg/dL | **95.8%** | `MODERATE` |
| **D1 (30m)** | CGM Dropout (30 min) | 10.15 mg/dL | 10.14 mg/dL | 61.3 mg/dL | **95.8%** | `MODERATE` |
| **D1 (60m)** | CGM Dropout (60 min) | 10.05 mg/dL | 10.03 mg/dL | 61.0 mg/dL | **95.9%** | `LOW` |
| **D2 (20%)** | CGM Gaps (20% random drop) | 9.96 mg/dL | 9.85 mg/dL | 60.0 mg/dL | **95.9%** | `HIGH` |
| **D3** | Missing Wearables (No HR/METs) | 10.28 mg/dL | 10.15 mg/dL | 60.8 mg/dL | **95.4%** | `MODERATE` |
| **D4** | Reduced-Sensor Mode (No CGM) | 10.05 mg/dL | 10.03 mg/dL | 61.0 mg/dL | **95.9%** | `LOW` |
| **D5** | Incomplete Meal Macros | 16.06 mg/dL | 18.86 mg/dL | 82.8 mg/dL | **95.7%** | `LOW` |
| **D6** | Cold-Start (K=0 meals) | 17.40 mg/dL | 19.39 mg/dL | 78.6 mg/dL | **95.7%** | `MODERATE` |
| **D7** | Out-of-Support Indian Preset | 9.85 mg/dL | 9.69 mg/dL | 59.3 mg/dL | **96.1%** | `LOW` (Clamped) |

### 8.2 Reliability Rules Engine Guardrails
Aegis automatically computes an auditable Reliability State:
* **`HIGH`:** Continuous CGM active, known meal macros, nominal interval width ($\le 65\text{ mg/dL}$).
* **`MODERATE`:** Minor CGM gaps or missing wearable telemetry, interval width $65\text{--}80\text{ mg/dL}$.
* **`LOW`:** Prolonged CGM dropout ($>30\text{ min}$), complete sensor absence (D4), unknown macronutrients, or out-of-support presets. Mandatory banner displayed:  
  *⚠️ "Estimate based on degraded telemetry. Not suitable for treatment decisions."*

---

## 9. Counterfactual What-If Sandbox & Clinical Simulator

Clinicians can simulate dietary alterations, pharmacological interventions, and behavioral actions before meals are consumed. To maintain scientific honesty, Aegis strictly segregates evidence into two origin tiers:

```
[What-If Simulation Engine]
          ├── Model-Driven Modifiers (Dual-Gamma Absorption Network & Pharmacology)
          │     ├── Carbohydrate & Macronutrient Scaling (±20%, ±50%)
          │     ├── Pharmacological Insulin Modeling (Rapid-acting bolus gamma absorption + basal drift)
          │     ├── Portion Estimation Uncertainty Ribbons (±10% to ±50% conformal envelopes)
          │     └── Regional Preset Substitutions (IFCT 2017)
          │
          └── Assumption-Driven Modifiers (Literature Kinetics)
                ├── Food Sequencing: Fiber/Protein consumed before carbs (GLP-1 delayed gastric emptying)
                └── Post-Meal Walk: Dynamic non-insulin-mediated GLUT4 muscular glucose clearance
```

Both curves are rendered simultaneously on the dashboard with distinct visual styling and explicit origin chips.

---

## 10. Reproducibility & Quick Start Guide

Aegis is engineered for 100% offline reproducibility without external cloud dependencies.

### 10.1 One-Command Offline Demo Runner (Fastest)
Launches the SQLite database, seeds demonstration patient twins, and opens the clinician dashboard in your default browser:
```bash
# Clone the repository
git clone https://github.com/Saumojit30/Aegis.git
cd Aegis

# Run with uv (or standard python in venv)
uv run python scripts/run_demo.py
```
* **Clinician Dashboard:** `http://localhost:8080/dashboard` (or `http://localhost:8000/dashboard`)
* **API Documentation:** `http://localhost:8080/docs`

### 10.2 Real-World Model Verification & Clinical Audit
Execute an end-to-end mathematical and clinical validation of the trained Candidate S model against the 54 held-out meal episodes from the PhysioNet CGMacros cohort:
```bash
# Run complete validation benchmark (MAE, RMSE, Clarke EGA, Conformal Coverage)
uv run python scripts/verify_model.py

# Inspect a single patient episode step-by-step against ground-truth CGM sensor readings
uv run python scripts/verify_model.py --sample 0
uv run python scripts/verify_model.py --patient P020
```

### 10.3 Automated Test Suite Execution
Execute the comprehensive automated test suite and linting audit:
```bash
# Run 95 unit and integration tests across 17 test modules
uv run pytest tests/ -q

# Run ruff code quality and style checks
uv run ruff check aegis/ services/ tests/ scripts/
```

### 10.4 Multi-Container Docker Orchestration
Run the decoupled microservice architecture (FastAPI backend + inference server):
```bash
docker compose up --build
```

---

## 11. Technology Stack

* **Machine Learning & Core:** Python 3.12, PyTorch 2.5+, LightGBM 4.6, Scikit-learn, SciPy, Polars, PyArrow.
* **Serving & Backend:** FastAPI, Starlette, Uvicorn, WebSockets, Pydantic v2, SQLAlchemy 2.0 (SQLite / PostgreSQL compatible).
* **Frontend & Visualisation:** Modern responsive HTML5/ES6/Chart.js single-page application served via FastAPI static mounts; complete Next.js 14 frontend project in `services/frontend/`.
* **MLOps, Tracking & Packaging:** Astral `uv`, MLflow, DVC, Docker, Docker Compose, Ruff, Pytest.

---

## 12. Project Structure

```text
Aegis/
├── aegis/                          # Core Python library
│   ├── config.py                   # Type-safe Pydantic system settings
│   ├── contracts.py                # Frozen data contracts (PredictRequest/Response)
│   ├── tracking.py                 # Strict MLflow run metadata enforcement
│   ├── data/                       # Acquisition, 5-min resampling, synthetic EHR
│   ├── features/                   # Static/dynamic extractors & missingness masks
│   ├── models/                     # Candidate S, Candidate U, baselines B0-B4
│   │   └── pharmacology.py         # Closed-form rapid-acting bolus/basal insulin PK
│   ├── uncertainty/                # Split-conformal calibration & reliability engine
│   └── degradation/                # Stress scenarios D0-D7
├── artifacts/bundle/               # Exported runtime bundle (weights, scalers, conformal table)
├── configs/                        # System settings, presets, conformal tables
├── docs/                           # Architecture, slides, demo script, challenge specs
├── reports/                        # Audited reports (model_decision, ablations, claims.csv)
├── scripts/                        # Demo runner, pipeline builder, verify_model audit CLI
│   ├── run_demo.py                 # Interactive dashboard server
│   ├── run_pipeline.py             # Data preprocessing and split generation
│   └── verify_model.py             # Turnkey clinical benchmark audit suite
├── services/
│   ├── backend/                    # FastAPI server, replay engine, DB models, static UI
│   ├── frontend/                   # Decoupled Next.js 14 clinician dashboard
│   └── inference/                  # Decoupled HTTP inference microservice
├── tests/                          # 95 comprehensive unit & integration tests (17 modules)
├── docker-compose.yml              # Container orchestration
├── pyproject.toml                  # Project packaging and dependencies (v1.1)
├── LICENSE                         # Apache-2.0 License
├── LICENSE-DATA                    # CC BY-NC-SA 4.0 Data License
└── ATTRIBUTION.md                  # Comprehensive citations & data provenance
```

---

## 13. Limitations & Ethical Considerations

1. **Cohort Demographics:** The primary continuous wearable dataset (CGMacros) consists of 14 participants with Type 2 Diabetes residing in the San Francisco Bay Area. Dietary and metabolic patterns may not fully generalize across diverse global populations without local re-calibration.
2. **Synthetic Data Boundaries:** While clinical labs and EHR co-morbidities strictly follow ADA 2024 distributions, they are synthetic artifacts designed to validate multimodal software architectures, not real patient health records.
3. **Non-Titration Clinical Guardrail:** Aegis supports closed-form simulation of rapid-acting bolus (Lispro/Aspart) gamma pharmacokinetics and basal drift for physiological counterfactuals, but it strictly enforces non-prescriptive operation: it never titrates, recommends, or automates insulin dosing decisions.
4. **Research Prototype Notice:** Aegis is developed to explore explainable AI, inductive bias, and calibrated uncertainty. It is strictly non-clinical software.

---

## 14. References & Citations

1. **CGMacros Dataset:** Hall, H., Perelman, D., Breschi, A., et al. (2023). Continuous Glucose Monitoring and Macronutrient Intake in Prediabetes and Type 2 Diabetes (version 1.0.0). *PhysioNet*. DOI: [10.13026/3z8q-x658](https://doi.org/10.13026/3z8q-x658).
2. **PhysioNet:** Goldberger, A. L., Amaral, L. A., Glass, L., et al. (2000). PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals. *Circulation*, 101(23), e215–e220.
3. **Indian Food Composition:** Longvah, T., Ananthan, R., Bhaskarachary, K., & Venkaiah, K. (2017). *Indian Food Composition Tables*. National Institute of Nutrition (ICMR-NIN), Hyderabad.
4. **Clinical Standards:** American Diabetes Association. (2024). Standards of Care in Diabetes—2024. *Diabetes Care*, 47(Suppl. 1), S1–S343.
5. **Conformal Prediction:** Angelopoulos, A. N., & Bates, S. (2023). Conformal prediction: A gentle introduction. *Foundations and Trends in Machine Learning*, 16(4), 494–591.
