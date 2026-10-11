# Tasks: Backend Architecture, Pluggable Inference, and Replay Engine

## 1. Pluggable Inference Providers (A7.1)

- [x] 1.1 Implement `services/backend/inference/provider.py` with `InferenceProvider`, `InProcessInferenceProvider`, `HttpInferenceProvider`, and `MockInferenceProvider`.
- [x] 1.2 Implement `services/inference/main.py` standalone FastAPI microservice.

## 2. Database Models & Seeding (A7.2)

- [x] 2.1 Implement `services/backend/models.py` and `services/backend/db.py` with SQLite / PostgreSQL support.
- [x] 2.2 Add database seeder loading patients, observations, meals, and synthetic EHR profiles from `data/processed/`.

## 3. Replay Engine (A7.3)

- [x] 3.1 Implement `services/backend/replay/engine.py` with cursor progression, speed control, degradation injection, and WebSocket broadcaster.

## 4. Backend API Endpoints (A7.4)

- [x] 4.1 Implement `services/backend/main.py` with all required REST endpoints and WebSocket handler.
- [x] 4.2 Implement what-if counterfactual scenario simulator supporting portion, walk, and sequencing interventions.

## 5. Verification & Testing (A7.5)

- [x] 5.1 Write integration tests in `tests/test_services.py` testing health, patient retrieval, in-process prediction, simulation, and replay control.
