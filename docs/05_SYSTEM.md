# 05 — SYSTEM ARCHITECTURE

## 1. High-level architecture
```text
                   ┌──────────────┐        ┌────────────────┐
   Next.js UI ◄──► │  Backend API │ ─HTTP─►│ Inference svc  │ ◄── model artefact (MLflow / folder)
   (REST + WS)     │  (FastAPI)   │        │ (FastAPI)      │
                   │  replay eng. │        └────────────────┘
                   └──────┬───────┘
                          │ SQL
                    ┌─────▼─────┐          ┌──────────┐
                    │ PostgreSQL│          │  MLflow  │ (training/registry; optional at runtime)
                    └───────────┘          └──────────┘
```
Technology choices:
| Choice | Why | Alternative | Fit |
|---|---|---|---|
| FastAPI | typed contracts, async, WebSocket support | Flask/Django | fastest path to validated APIs |
| Separate inference service | demonstrates train/serve separation | in-process model | cheap, strong MLOps story; fall back to in-process behind the same interface if short on time (D7) |
| PostgreSQL | relational patient/event data, JSONB for predictions | SQLite | realistic deployment; Docker makes it cheap |
| In-process async replay + WebSocket | no broker needed | Kafka/Redis/Celery | avoids infrastructure theatre |
| Next.js + TypeScript | component UI | plain React/Streamlit | judge-ready dashboard |

## 2. Patient state
```json
{
  "patient_id": "P014",
  "profile": {"age": 56, "sex": "F", "bmi": 31.2, "hba1c": 7.1, "fasting_glucose": 128},
  "ehr_extras": {"synthetic": true, "medications": ["..."], "bp_history": [{"ts": "...", "sys": 138, "dia": 86}]},
  "stream": {"last_glucose": 142, "last_glucose_ts": "...", "hr": 78, "mets": 1.3, "last_meal_id": "M0231"},
  "personalisation": {"n_personal_meals": 6, "method": "residual_pca_ridge", "prior": "similarity"},
  "data_quality": {"glucose_stale_min": 0, "hr_missing": false, "degradation": "D0"},
  "reliability": "high|moderate|low",
  "model": {"version": "3", "dataset_version": "...", "feature_version": "..."}
}
```
(Example values are illustrative placeholders, not data.)

## 3. API
Common: JSON, UTC ISO timestamps, errors `{ "error": {"code": "...", "message": "...", "details": {}} }`. Every prediction/simulation response carries `model` and `disclaimer`.

| Endpoint | Purpose |
|---|---|
| `GET /health` | liveness + dependency status |
| `GET /model/info` | model/dataset/feature versions, lineage, limitations |
| `GET /patients` | list twins (id, group, summary) |
| `GET /patients/{id}` | profile + EHR extras (synthetic flag) |
| `GET /patients/{id}/state` | current twin state |
| `GET /patients/{id}/similar?k=` | nearest patients with similarity scores and borrowed parameters |
| `GET /patients/{id}/trajectory?from=&to=` | stored observations + predictions |
| `GET /meal-presets` | preset list with source, value type, support score |
| `POST /ingest` | push one sensor/meal event into a session (validated) |
| `POST /predict` | forecast for a meal event |
| `POST /simulate` | baseline vs scenario comparison |
| `POST /replay/start` · `/pause` · `/resume` · `/stop` | control replay |
| `POST /replay/degrade` | set/clear a degradation scenario for the active session |
| `WS /ws/replay/{session_id}` | stream events, forecasts and actual-vs-predicted updates |

### 3.1 `POST /predict`
Request (placeholders):
```json
{"patient_id":"P014","session_id":"S1","t0":"<ISO timestamp>",
 "meal":{"preset_id":null,"carbs_g":0,"protein_g":0,"fat_g":0,"fiber_g":0,"amount_pct":100,"meal_type":"dinner"},
 "degradation":"D0"}
```
Response (shape only):
```json
{"horizon_min":[5,10,"..."],"delta_glucose":["..."],"glucose":["..."],
 "interval":{"level":0.9,"lower":["..."],"upper":["..."],"scenario":"D0"},
 "metrics":{"peak":null,"time_to_peak_min":null,"delayed_mean_120_180":null,"minutes_above_threshold":null,"risk_flag":null},
 "reliability":{"label":"moderate","reasons":["only 2 personal meals used"]},
 "personalisation":{"n_personal_meals":2,"prior":"similarity"},
 "model":{"version":"3","dataset_version":"...","feature_version":"..."},
 "disclaimer":"Research prototype ... not medical advice."}
```
Validation: macros ≥ 0 and within training ranges (else `out_of_support` flag, not error); `t0` ordered with session; unknown patient → 404; invalid degradation → 422. Dependencies: inference service, DB.

### 3.2 `POST /simulate`
Request: `predict` request plus `scenarios:[{"type":"sequencing"},{"type":"walk","minutes":20},{"type":"portion","amount_pct":70},{"type":"fat","delta_g":-10},{"type":"preset","preset_id":"..."},{"type":"meal_time","shift_min":-60}]`.
Response: `baseline` (same as predict), `scenarios:[{type, origin:"model_driven|assumption_driven", trajectory, interval, metrics, delta_vs_baseline:{peak, time_to_peak, delayed_mean, minutes_above}, reliability, notes}]`. Assumption-driven results always include `assumption:{source, factor, verify:true}`.

### 3.3 Mock inference
`inference_mock` returns deterministic plausible curves with the same schema and `model.version="mock"`. All backend/frontend work starts here. The mock must never be presented as a real model.

## 4. Database (PostgreSQL)
| Table | Key columns / constraints |
|---|---|
| `patients` | `patient_id` PK, group, profile columns, `source_id` unique |
| `ehr_profiles` | `patient_id` FK unique, `synthetic_pairing` bool NOT NULL default true, JSONB diagnoses/medications, `pairing_distance` |
| `bp_observations` | `patient_id` FK, `ts`, `systolic`, `diastolic`, `synthetic` bool |
| `observations` | `patient_id` FK, `ts`, `glucose`, `hr`, `mets`, flags; unique `(patient_id, ts)` |
| `meals` | `meal_id` PK, `patient_id` FK, `ts_start`, macros, `amount_pct`, `meal_type` |
| `replay_sessions` | `session_id` PK, `patient_id`, `speed`, `status`, `degradation`, `started_at`, `cursor_ts` |
| `predictions` | `prediction_id` PK, `session_id`, `meal_id`, `t0`, `payload` JSONB, `model_version`, `degradation`, `reliability`, `created_at` |
| `simulations` | `simulation_id` PK, `prediction_id` FK, `scenario` JSONB, `payload` JSONB |
| `model_versions` | `model_version`, `dataset_version`, `feature_version`, `mlflow_run_id`, `alias`, `created_at` |
| `data_quality_events` | `session_id`, `ts`, `type`, `detail` JSONB |
Constraints: foreign keys, non-negative macros, glucose within 20–600 check (store clipped flag), timestamps UTC. Migrations: Alembic.

## 5. Dynamic ingestion flow
```text
incoming event → schema validation → normalisation (units, 5-min grid)
→ state update → quality check (stale/missing/out-of-range → data_quality_events)
→ if meal event: build features (shared module) → degradation applied if active → inference → store prediction → push to WS
→ if sensor event during open forecast: update actual-vs-predicted overlay + running error
```

## 6. Live historical replay
| Aspect | Rule |
|---|---|
| Source | processed `sensor_5min` + `meals` for one patient (preloaded in DB; demo patients come from `data/demo`) |
| Ordering | strict by timestamp; meals before the sensor row at the same timestamp |
| Speed | configurable: 1 simulated minute = 0.2–2 s; default 1 s per 5-min tick |
| Control | start, pause, resume, stop, seek to next meal (demo helper) |
| Duplicates | ignored by `(patient_id, ts)`; logged |
| Invalid | quarantined + `data_quality_events`; stream continues |
| Late events | older than cursor − tolerance are rejected and logged |
| Degradation | `POST /replay/degrade` applies shared `aegis/degradation` ops to subsequent events/features |
| Failure | if inference fails, send `forecast_unavailable` with reason; never fabricate a forecast |
| Label | UI banner "Replay mode: historical open dataset" |

## 7. What-if engine
```text
baseline meal → predict
scenario → (model-driven: modify features → predict) / (assumption-driven: apply configured modifier)
comparison → differences + labels + reliability
```
Assumption modifiers live in `configs/assumptions.yaml` with `source` and `verify` fields. The UI shows the origin label next to every number.

## 8. Explanations (no LLM)
Templated, citation-locked text: top contributing factors from simple attributions (permutation importance by feature group, precomputed per prediction) rendered into fixed sentences ("Higher fat ratio predicted to delay the peak"). No free-text generation.

## 9. Error handling and logging
Structured JSON logs with `request_id`, `session_id`, `patient_id`, `model_version`. Error classes: validation (422), not found (404), dependency down (503 with `forecast_unavailable`), internal (500, no stack to client). Inference timeout default 2 s → degrade gracefully.

## 10. System acceptance criteria
- [ ] All endpoints implemented against the mock, then the real model
- [ ] Replay streams a patient for ≥ 10 min without error; pause/resume/restart work
- [ ] Meal event triggers forecast and overlay of actuals
- [ ] `/simulate` returns baseline + all six scenario types with origin labels
- [ ] Degradation switch changes reliability, interval and reasons
- [ ] Failure of inference service produces `forecast_unavailable`, not a crash
- [ ] Migrations run on empty DB; seed script loads demo patients from `data/demo`
