# Change Proposal: Backend API, Pluggable Inference Provider, and Replay Engine

## Why
With the core forecasting model, few-shot personalisation, split-conformal prediction intervals, and degradation engine validated, Aegis requires its operational serving infrastructure (Phase A7):
1. **Pluggable Inference Architecture (Decision D12):** Support both `inprocess` provider (direct Python runtime for zero-overhead local development and demo scripts) and `http` provider (decoupled microservice for containerized deployment).
2. **Clinician Replay Engine (Decision D13):** Asynchronous time-series replay engine with speed throttling (1x–100x), live WebSocket broadcasting, pause/resume/step controls, and real-time degradation scenario injection (D0–D7).
3. **What-If Scenario Simulation:** Counterfactual physiological simulation endpoint comparing baseline meals against interventions (portion adjustment, walking, macronutrient sequencing) with strict `model_driven` vs `assumption_driven` attribution.
4. **Relational Patient Twin State:** SQLite / PostgreSQL database tracking patients, biometric timeseries, synthetic EHR extras, meals, and simulation logs.

## What Changes
1. **Inference Providers (`services/backend/inference/provider.py`):**
   - Abstract `InferenceProvider` base class.
   - `InProcessInferenceProvider`: loads `artifacts/bundle/` via `load_aegis_bundle` and runs real model inference.
   - `HttpInferenceProvider`: delegates to HTTP inference microservice.
   - `MockInferenceProvider`: deterministic mock responses for testing.
2. **Standalone Inference Service (`services/inference/main.py`):**
   - FastAPI microservice exposing `/health`, `/info`, `/predict`.
3. **Database Models & Seeding (`services/backend/db.py`, `models.py`):**
   - SQLAlchemy tables for patients, observations, meals, replay sessions, predictions, and simulations.
   - Automatic seeding on startup from processed dataset samples.
4. **Replay Engine (`services/backend/replay/engine.py`):**
   - Asynchronous cursor-based event streamer with WebSocket notification.
5. **FastAPI Backend Application (`services/backend/main.py`):**
   - Implements `/health`, `/model/info`, `/patients`, `/patients/{id}`, `/patients/{id}/state`, `/patients/{id}/similar`, `/meal-presets`, `/predict`, `/simulate`, `/replay/*`, and `/ws/replay/{session_id}`.

## Impact
- Unblocks Phase A8 (Clinician Dashboard) and Phase A9 (Docker containerization).
- Satisfies Checkpoint C3 requirements for end-to-end replay, forecasting, and simulation.
