# Technical Design: Real Digital Twin Execution Engine

**Change:** `real-digital-twin-engine`  
**Status:** PROPOSED  
**Capability:** `twin-engine`  

---

## 1. System Architecture & Real Data Flow

```
+---------------------------------------------------------------------------------------+
|                                DATA STORAGE LAYER                                     |
|  - data/processed/sensor_5min.parquet (5,184 readings: glucose, hr, mets, masks)     |
|  - data/processed/meals.parquet (54 real clinical meals with macro & timing)          |
|  - data/processed/patients.parquet & ehr_profiles.parquet                             |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                         REPLAY ENGINE (In-Memory Buffer)                              |
|  - Loads full 72-hour continuous 5-min timeline for active patient (864 steps)        |
|  - Indexes exact meal event steps: step = index where ts == meal.ts_start             |
|  - Advances cursor with real timestamps, broadcasting via WebSocket                   |
|  - Maintains historical window buffer: [cursor_idx - 12 : cursor_idx]                 |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v  (On meal arrival or clinician forecast request)
+---------------------------------------------------------------------------------------+
|                    DYNAMIC FEATURE EXTRACTION (Past 60 Minutes)                       |
|  - seq_tensor: shape (12, 6)                                                          |
|      [glucose_rel, glucose_mask, hr_norm, hr_mask, mets_norm, mets_mask]              |
|  - anchor_tensor: shape (4,)                                                          |
|      [g_0 / 200.0, dg_15min, dg_30min, rolling_std]                                   |
|  - g_t0: Actual glucose at meal onset (e.g. 142.5 mg/dL)                               |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                     CANDIDATE S INFERENCE & CONFORMAL QUANTILE                        |
|  1. Candidate S Neural Forward Pass: g_pred = CandidateS(seq, anchor, meal, static)  |
|  2. Real-Time Ridge Adaptation:                                                       |
|       - Query patient's prior meals: M_1, ..., M_{k-1}                                |
|       - Extract actual observed postprandial curves vs backbone predictions           |
|       - Solve w = (B^T B + lambda I)^-1 B^T r (closed-form, r=3 PCA basis)            |
|       - g_adapted = g_pred + B * w                                                    |
|  3. Split-Conformal 90% Prediction Intervals:                                         |
|       - [g_adapted - q_t, g_adapted + q_t] clamped to [40, 400] mg/dL                 |
|  4. Dynamic Reliability Evaluation: assess_reliability(g_pred, seq, meal, D0-D7)     |
+---------------------------------------------------------------------------------------+
```

---

## 2. Key Component Specifications

### 2.1 Replay Engine Ingestion (`services/backend/replay/engine.py`)
- **Real Timeline Initialization:**  
  When initializing a patient session (`patient_id` $\in \{$`P001`, `P002`, `P010`, `P011`, `P020`, `P021`$\}$):
  1. Load rows from `sensor_5min.parquet` matching `patient_id`, sorted ascending by `ts`.
  2. Load rows from `meals.parquet` matching `patient_id`.
  3. Map each meal to its closest 5-minute sensor step: `step_idx = round((meal.ts_start - min_ts) / 5 min)`.
  4. Each replayed step emits:
     - `ts`: ISO timestamp of the sensor recording.
     - `glucose`, `hr`, `mets`: Real measured telemetry.
     - `is_meal`: Boolean flag.
     - `meal_info`: Macronutrient dictionary (`carbs_g`, `protein_g`, `fat_g`, `fiber_g`, `calories`, `meal_type`).
     - `actual_postprandial_curve`: Next 36 steps of actual future glucose (for ground-truth trajectory overlay on the clinician chart).

### 2.2 Live Retrospective Window Slicing
- When the cursor reaches step $i$ with a meal event:
  - Take the retrospective slice: `window = series[max(0, i-12) : i]`.
  - If $i < 12$, pad the beginning with the earliest available observation.
  - Compute the 6-channel sequence tensor:
    - Channel 0: Normalized relative glucose: `(glucose - g_t0) / 50.0`.
    - Channel 1: CGM observed mask: `1.0` if not `glucose_missing` else `0.0`.
    - Channel 2: Normalized HR: `(hr - 75.0) / 30.0`.
    - Channel 3: HR observed mask: `1.0` if not `hr_missing` else `0.0`.
    - Channel 4: Normalized METs: `(mets - 1.0) / 3.0`.
    - Channel 5: METs observed mask: `1.0` if not `mets_missing` else `0.0`.
  - Compute the anchor vector from the actual pre-meal trend:
    - `anchor[0] = g_t0 / 200.0`
    - `anchor[1] = (glucose[i] - glucose[i-3]) / 15.0` (15-min velocity)
    - `anchor[2] = (glucose[i] - glucose[i-6]) / 30.0` (30-min velocity)
    - `anchor[3] = std(glucose[i-12:i]) / 50.0` (rolling volatility)

### 2.3 Real-Time Closed-Form Ridge Adaptation
- Maintain an index of completed meals for each active patient.
- If the patient has $K \ge 1$ preceding historical meals:
  - Extract the observed 36-step trajectory for each historical meal $m \in \{1 \dots K\}$.
  - Compute the model residual: $\mathbf{r}_m = \mathbf{y}_m - \hat{\mathbf{y}}_m$.
  - Project residuals onto the orthonormal basis $\mathbf{B} \in \mathbb{R}^{36 \times 3}$:
    $$\mathbf{w} = \left( \sum_{m=1}^K \mathbf{B}^T \mathbf{B} + \lambda \mathbf{I} \right)^{-1} \sum_{m=1}^K \mathbf{B}^T \mathbf{r}_m$$
  - Apply personal adjustment: $\hat{\mathbf{y}}_{\text{adapted}} = \hat{\mathbf{y}}_{\text{population}} + \mathbf{B} \mathbf{w}$.
- When $K = 0$, initialize with the Gaussian clinical similarity prior across demographic neighbors.

### 2.4 Physiologically Grounded What-If Engine
- In `simulate()`, when the clinician tests dietary alterations:
  - Construct the modified meal feature vector directly: `meal_mod = extract_meal_features(modified_macros)`.
  - Pass `meal_mod` through `Candidate S` neural forward pass using the same retrospective sequence and patient profile.
  - For behavioral interventions (sequencing and post-meal walk), apply literature multipliers to the neural trajectory, returning explicit `MODEL-DRIVEN` and `ASSUMPTION` evidence origin badges.

---

## 3. Data Schema & Contract Alignment
- Update `PatientModel` in `services/backend/models.py` and `db.py` to seed real patients:
  `P001`, `P002`, `P010`, `P011`, `P020`, `P021` with true baseline lab values from `patients.parquet` and `ehr_profiles.parquet`.
- Ensure `PredictRequest` accepts optional `retrospective_sequence` and `g_t0` from the replay engine; if omitted, the provider fetches the window from the patient's active replay cursor.
