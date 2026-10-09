# 07 — DEVOPS, TESTING, DEPLOYMENT

## 1. Repository structure
```text
<TeamName>_<CollegeName>/
├── README.md  AGENTS.md  STATUS.md  LICENSE  LICENSE-DATA  ATTRIBUTION.md  Makefile  pyproject.toml  dvc.yaml  docker-compose.yml
├── configs/        data.yaml  train.yaml  schema.yaml  assumptions.yaml  degradation.yaml
├── docs/           01..09 + architecture/ (diagram sources, exports)
├── tasks/          IMPLEMENTATION_TASKS.md
├── data/           raw/ (gitignored, DVC)  demo/ (committed, attributed)  processed/ (DVC)
├── aegis/
│   ├── data/  features/  degradation/  models/  training/  evaluation/
│   ├── personalisation/  similarity/  uncertainty/  simulation/
│   └── common/
├── services/
│   ├── backend/        FastAPI app, replay engine, DB models, migrations
│   ├── inference/      FastAPI model server (+ mock)
│   └── frontend/       Next.js app
├── reports/        data_audit.md  error_analysis.md  claims.csv  model_card.md  figures/
├── tests/          unit/  data/  ml/  api/  integration/  e2e/  fixtures/
├── scripts/        seed_db.py  run_replay.py  promote_model.py  offline_demo.sh
└── .github/workflows/ci.yml
```

## 2. Development environment
Python 3.11 (verify library compatibility), `uv` or `pip-tools` for pinned deps, Node 20 LTS, Docker + Docker Compose, PostgreSQL 15+ (container), MLflow server (container, optional at runtime), Java (for Synthea only). Pre-commit: ruff, formatter, mypy (light), eslint, prettier.

## 3. Configuration
`.env.example` documents: `DATABASE_URL`, `INFERENCE_URL`, `MLFLOW_TRACKING_URI`, `MODEL_ALIAS=champion`, `MODEL_DIR` (offline), `REPLAY_DEFAULT_SPEED`, `LOG_LEVEL`, `NEXT_PUBLIC_API_URL`. Environments: `development`, `testing`, `production` via `APP_ENV`. Secrets only in `.env` (git-ignored) or CI secrets.

## 4. Docker
| Service | Notes |
|---|---|
| `frontend` | Node build → standalone server |
| `backend` | Python slim, uvicorn, Alembic on start |
| `inference` | Python slim + CPU torch (or ONNX runtime if exported; D9), loads artefact |
| `db` | postgres, named volume |
| `mlflow` | optional profile (`--profile mlops`) |
Healthchecks on all; `depends_on` with health conditions; one command `docker compose up`. Offline demo: model artefact and **demo subset** loaded from volume/seed; no internet needed.

## 5. CI (GitHub Actions)
```text
push/PR → lint (ruff, eslint) → unit tests → data tests (fixture) → ML smoke (1 epoch on fixture)
→ API tests (backend + mock inference) → build Docker images → compose smoke test (/health) → (main) e2e
```
CI uses **synthetic fixtures only** — no CGMacros data required.

## 6. Test plan
| Layer | Examples |
|---|---|
| Unit | feature functions, unit conversions, degradation ops, similarity, conformal quantiles |
| Data | schema, ranges, timestamps, duplicates, meal construction, **leakage tests** |
| ML | shapes, determinism with seed, no NaN, coverage computation |
| Training smoke | one epoch writes MLflow run with required tags |
| API | contract tests for `/predict`, `/simulate`, errors, validation |
| Integration | ingest → state → features → inference → DB → WS message |
| E2E | Playwright: start replay → forecast → scenario compare → degrade → label changes |
| Non-functional | `/predict` latency; replay stability 10 min |

## 7. Deployment
| Option | Verdict |
|---|---|
| **Local Docker Compose** | Challenge demo (offline, reliable) — Track A |
| **Single VM + Compose + reverse proxy (HTTPS)** | Public portfolio demo — Track B |
| Managed container hosting + managed Postgres | Alternative; verify pricing/limits at the time |
| Kubernetes | Rejected — unjustified for this scope |
Track B CD: GitHub Actions builds images, pushes to a registry, deploys by SSH/compose pull; smoke test after deploy; rollback = previous image tag. A **public** deployment shows only the attributed demo subset and the disclaimer (non-commercial, research use).

## 8. Security and data handling
No real patient data; full raw CGMacros not committed; secrets via env; CORS restricted to frontend origin; pydantic input validation; rate limiting on public deployment; logs exclude profile payloads; dependency scanning in CI (pip-audit/npm audit).

## 9. DevOps acceptance criteria
- [ ] Clean-machine setup documented and verified
- [ ] `docker compose up` brings the stack healthy
- [ ] CI green on main
- [ ] Offline demo script works with network disabled
- [ ] (Track B) deployed URL reachable with health check and rollback documented
