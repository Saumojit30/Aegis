# 10 — ARCHITECTURAL REFINEMENTS & RISK MITIGATIONS

This document formalises the architectural refinements identified during pre-implementation stress-testing of the Aegis blueprint. These refinements eliminate friction points, dependency bottlenecks, and failure modes while preserving full compliance with `AGENTS.md` and the challenge requirements.

---

## 1. Summary of Refinements & Decision Mappings

| Refinement Area | Primary Risk / Loophole | Architectural Solution | Decision Log ID |
|---|---|---|---|
| **Inference Topology** | Microservice latency & multi-container orchestration friction during live WebSocket replay | Pluggable `InferenceClient` (in-process for dev/demo, HTTP container for MLOps deployment) | **D12** |
| **Replay Engine State** | High-frequency DB blocking writes during accelerated time-series replay (2x–10x) | In-memory cursor state + asynchronous milestone checkpointing | **D13** |
| **Synthetic EHR Layer** | Java runtime & Synthea setup overhead for a secondary synthetic layer | Pure Python deterministic clinical synthetic EHR generator with fixed seed | **D14** |
| **Wearable Missingness** | Dense sequence expectations failing when real-world HR/METs drop out | Explicit sensor missingness masks + zero-imputed z-scores + degradation tagging | **D15** |
| **Indian Preset OOD Risk** | Neural net/GBDT extrapolating ungrounded curves outside California training domain | Support-score boundary enforcement + physiological clamping + forced LOW reliability | **D16** |

---

## 2. Detailed Refinement Specifications

### Refinement 1: Pluggable Inference Provider (Decision D12)
- **Problem:** Running separate backend and inference microservices over HTTP during live 1-second WebSocket replay introduces serialization overhead, inter-container latency, and port-binding complexity on local development and demo setups.
- **Specification:**
  - Define a shared abstract interface `InferenceProvider` in `services/common` or `aegis/models/interface.py`:
    ```python
    class InferenceProvider(Protocol):
        async def predict(self, req: PredictRequest) -> PredictResponse: ...
        async def get_model_info(self) -> ModelInfoResponse: ...
    ```
  - Implement two concrete providers:
    1. `InProcessInferenceProvider`: directly imports model bundle and executes inference within the FastAPI backend process (zero network overhead, default for local dev, offline demo, and unit tests).
    2. `HttpInferenceProvider`: dispatches HTTP requests to the standalone containerised `services/inference` service (used in full multi-container deployment to demonstrate train/serve separation).
  - Selected via environment variable: `INFERENCE_MODE=inprocess` (default) vs. `INFERENCE_MODE=http`.

### Refinement 2: In-Memory Replay Engine with Milestone Checkpointing (Decision D13)
- **Problem:** Persisting every 5-minute sensor event to PostgreSQL during high-speed replay (e.g. 5x or 10x speed) creates event-loop blocking and DB connection churn.
- **Specification:**
  - The `ReplaySession` maintains its active cursor and observation buffer in memory.
  - Streaming events are dispatched directly to active WebSocket subscribers.
  - Database writes are batched and executed on key milestone events:
    - Session start, pause, resume, and stop.
    - Meal events and generated forecasts (`predictions` table).
    - Scenario simulations (`simulations` table).
    - Data quality / degradation changes (`data_quality_events` table).
  - An optional flag `REPLAY_PERSIST_ALL_OBSERVATIONS=false` allows full logging when required for audit replay.

### Refinement 3: Pure Python Synthetic EHR Generator (Decision D14)
- **Problem:** Installing Java, building Synthea, and parsing complex FHIR bundles creates a high barrier to entry and cross-platform installation risks for a dataset explicitly flagged as `synthetic_pairing=true`.
- **Specification:**
  - Commit directly to a pure Python clinical generator `aegis/data/ehr_synthetic.py`.
  - Uses standard Python libraries (`numpy`, `pydantic`) with documented demographic distributions (age, sex, BMI, HbA1c, hypertension stage) derived from NHANES and published T2D literature.
  - Generates matched synthetic EHR records seeded deterministically (`seed=42`).
  - Output schema identical to the intended Synthea export: `ehr_profiles` and `bp_observations`.

### Refinement 4: Wearable Missingness Resilience (Decision D15)
- **Problem:** CGMacros wearable streams (HR from Empatica E4, METs from Fitbit) have 30%–60% real-world dropout across participants. Models requiring rigid non-null `[12, 6]` inputs will crash or corrupt predictions.
- **Specification:**
  - Feature tensors always include explicit mask channels:
    - Channel 0: Glucose Δ
    - Channel 1: Glucose observed mask (1.0 = measured, 0.0 = interpolated/missing)
    - Channel 2: HR z-score (0.0 if missing)
    - Channel 3: HR observed mask (1.0 = present, 0.0 = missing)
    - Channel 4: METs z-score (0.0 if missing)
    - Channel 5: METs observed mask (1.0 = present, 0.0 = missing)
  - All models (baselines B0–B4 and GRU fusion) must train and evaluate with random masking augmentation (D1 degradation scenario).
  - If HR or METs are missing at prediction time `t0`, the reliability assessor automatically downgrades confidence and notes missing wearable stream in `reasons`.

### Refinement 5: OOD Guardrails for Indian Meal Presets (Decision D16)
- **Problem:** Simulating high-carb/high-fat Indian dishes on a model trained purely on American meal data risks physiologically implausible outputs.
- **Specification:**
  - `aegis/features/support.py` computes the convex hull / normalized distance of the meal's macronutrient ratios (`carbs_g`, `fat_g`, `protein_g`, `fiber_g`) relative to the training distribution.
  - If a preset or user-modified scenario meal has a `support_score < threshold_support` (e.g., < 0.3):
    1. Predicted glucose trajectory is strictly clamped within physiological limits: `ΔG ∈ [-40, +180] mg/dL`, absolute glucose `G ∈ [40, 400] mg/dL`.
    2. Prediction interval is widened by an OOD penalty factor.
    3. Reliability label is forced to `low`.
    4. Response payload adds: `"reasons": ["Meal macronutrient profile is outside the training data distribution (OOD extrapolation)"]`.
    5. The UI scenario chip renders as `assumption_driven (OOD extrapolation)`.

---

## 3. Integration with OpenSpec Workflow

These refinements do not bypass the OpenSpec process; they form the architectural foundation for upcoming OpenSpec change proposals:
- **Batch 1 (Foundation):** Includes `INFERENCE_MODE` in `configs/settings.py` and mock provider structure.
- **Batch 2 (Pipeline):** Implements `aegis/data/ehr_synthetic.py` and sensor masks in `aegis/features`.
- **Batch 3 (Baselines & Contracts):** Embeds missingness masks in input schema and support score in prediction contracts.
- **Batch 4 (Temporal Model):** Uses GRU architecture with masked wearable fusion.
- **Batch 5 (Degradation & Uncertainty):** Incorporates OOD clamping and wearable dropout conformal intervals.
- **Batch 6 (System & Frontend):** Uses in-memory replay engine and dual-mode inference provider.
