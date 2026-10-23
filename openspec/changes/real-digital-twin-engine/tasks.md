# Implementation Tasks: Real Digital Twin Execution Engine

**Change:** `real-digital-twin-engine`  
**Status:** COMPLETED  

---

## Task List

### Phase 1: Database & Patient Model Synchronization
- [x] 1.1 Update `services/backend/db.py` to seed real patients from `data/processed/patients.parquet` and `ehr_profiles.parquet` (`P001`, `P002`, `P010`, `P011`, `P020`, `P021`).
- [x] 1.2 Seed real clinical meals from `data/processed/meals.parquet` with correct `patient_id`, timestamps, and macronutrients.
- [x] 1.3 Verify database query endpoints (`GET /patients`, `GET /patients/{id}`, `GET /patients/{id}/state`) return real demographic and clinical lab data.

### Phase 2: Replay Engine Real-Data Pipeline Refactor
- [x] 2.1 Refactor `services/backend/replay/engine.py` to eliminate hardcoded mock loops (`curr_g = 115.0`).
- [x] 2.2 Implement `_load_patient_series(patient_id)` to read real continuous 5-minute telemetry from `data/processed/sensor_5min.parquet`.
- [x] 2.3 Align real meal events from `data/processed/meals.parquet` with the exact 5-minute timeline steps.
- [x] 2.4 Include the ground-truth 36-step future glucose trajectory in the meal payload for real-time validation overlay.
- [x] 2.5 Update WebSocket broadcast loop to emit real timestamped telemetry and sensor masks.

### Phase 3: Dynamic 60-Minute Pre-Meal Feature Ingestion
- [x] 3.1 Implement buffer slicing in `services/backend/replay/engine.py` to extract the preceding 12 steps ($t-60$ to $t$).
- [x] 3.2 Implement dynamic tensor conversion: relative glucose scaling, observation masks, and anchor vector calculation ($g_0$, $dg/dt$, rolling std).
- [x] 3.3 Update `InProcessInferenceProvider.predict()` to receive the real dynamic sequence tensor and anchor vector instead of `np.zeros((12, 6))`.
- [x] 3.4 Verify Candidate S outputs physiological curves driven by actual pre-meal glucose momentum.

### Phase 4: Dynamic Closed-Form Ridge Adaptation & Neural What-If
- [x] 4.1 Implement dynamic residual collection across preceding completed meals for the active patient.
- [x] 4.2 Compute closed-form Ridge adaptation weights $\mathbf{w} = (\mathbf{B}^T \mathbf{B} + \lambda \mathbf{I})^{-1} \mathbf{B}^T \mathbf{r}$ using the PCA residual basis.
- [x] 4.3 Update `InProcessInferenceProvider.simulate()` to re-run Candidate S forward pass with modified macronutrient vectors.
- [x] 4.4 Apply literature-grounded modifiers for behavioral scenarios (sequencing, walk) with explicit `assumption_driven` badges.

### Phase 5: Dashboard Frontend Integration
- [x] 5.1 Update `services/backend/static/index.html` to support patients `P001`–`P021`.
- [x] 5.2 Display real ground-truth postprandial curve alongside the conformal prediction interval when replaying meals.
- [x] 5.3 Render active Ridge adaptation state in the personalisation card.
- [x] 5.4 Update What-If comparison chart to render neural counterfactual curves.

### Phase 6: Automated Verification & Unit Test Suite
- [x] 6.1 Update `tests/test_services.py` to validate real data replay, dynamic tensor slicing, and neural what-if outputs.
- [x] 6.2 Verify 100% test pass rate across all 69 unit and integration tests.
- [x] 6.3 Run `ruff` code formatting and linting audit.
