# Design Document: Backend Architecture, Pluggable Inference, and Replay Engine

## Architecture

```
  ┌─────────────────────────────────────────────────────────────┐
  │                    FastAPI Backend API                      │
  │                                                             │
  │  REST Endpoints:                     WebSocket:             │
  │    - GET  /patients, /patients/{id}    - WS /ws/replay/{id} │
  │    - POST /predict                                          │
  │    - POST /simulate                                         │
  │    - POST /replay/{start,pause,stop}                        │
  └─────────────┬────────────────────────────────┬──────────────┘
                │                                │
                ▼                                ▼
  ┌───────────────────────────┐    ┌───────────────────────────┐
  │    InferenceProvider      │    │       ReplayEngine        │
  │  ┌─────────────────────┐  │    │  (Async in-memory cursor, │
  │  │ InProcessProvider   │  │    │   speed factor 1x-100x,   │
  │  ├─────────────────────┤  │    │   degradation injection)  │
  │  │ HttpProvider (Micro)│  │    └─────────────┬─────────────┘
  │  ├─────────────────────┤  │                  │
  │  │ MockProvider        │  │                  │
  │  └─────────────────────┘  │                  │
  └─────────────┬─────────────┘                  │
                ▼                                ▼
       artifacts/bundle/             SQL Database (SQLite / Postgres)
```

## 1. Pluggable Inference Provider (D12)
`InferenceProvider` interface defines:
- `async predict(request: PredictRequest) -> PredictResponse`
- `async simulate(request: SimulateRequest) -> SimulateResponse`

Implementation variants:
- **`InProcessInferenceProvider`:** Uses `load_aegis_bundle("artifacts/bundle")`. Converts `PredictRequest` into required feature tensors on the fly, calls `bundle.predict(...)`, and formats response strictly matching `PredictResponse`. Zero network overhead.
- **`HttpInferenceProvider`:** Uses `httpx.AsyncClient` to dispatch requests to `http://inference:8001/predict`.
- **`MockInferenceProvider`:** Returns mathematically plausible synthetic trajectory curves with `model.version="mock"`.

Configured via `INFERENCE_MODE=inprocess|http|mock` in environment / config.

## 2. In-Memory Asynchronous Replay Engine (D13)
- Stores session state in memory:
  - `patient_id`
  - `cursor_idx`: current observation index in historical 5-minute series
  - `status`: `IDLE`, `RUNNING`, `PAUSED`, `STOPPED`
  - `speed`: multiplier (1, 5, 10, 50, 100)
  - `active_degradation`: `D0` to `D7`
- Background asyncio task advances cursor at `5.0 / speed` seconds per step:
  - Broadcasts `TICK` event with current glucose, HR, METs, and sensor masks.
  - When cursor reaches a meal event $t_0$, automatically generates and broadcasts a `PREDICTION` event with 180-minute forecast and conformal interval.
  - As time proceeds through the 180-minute postprandial window, broadcasts `ACTUAL_VS_PREDICTED` update comparing realized glucose against interval bounds.

## 3. What-If Counterfactual Simulator
Evaluates physiological interventions:
- **Portion Adjustment:** Scales carbs, calories, and structured absorption amplitudes by `amount_pct / 100`. (Origin: `model_driven`).
- **Post-Meal Walking:** Incorporates 20–30 min activity offset reducing postprandial peak. (Origin: `assumption_driven` with literature citation: Reynolds et al., Diabetologia 2016).
- **Food Sequencing (Carb-last):** Delays fast carbohydrate absorption kinetics $\tau_{fast}$ by 15–20 minutes. (Origin: `assumption_driven` with literature citation: Shukla et al., BMJ Open Diab Res 2017).
