# 04 — MLOPS

Principle: every component has a practical purpose; nothing decorative. Two layers: **Track A** (built during the challenge window) and **Track B** (portfolio hardening afterwards).

## 1. Lifecycle
```text
data (DVC) → validation → feature pipeline → training (config) → MLflow tracking
→ evaluation report → model artefact + registration → inference service → monitoring → retraining
```

## 2. Component table
| Component | Tool | Why | Track |
|---|---|---|---|
| Code versioning | Git + GitHub | traceability | A |
| Data versioning | DVC (local or S3-compatible remote) | reproduce any dataset; raw data stays out of git | A |
| Config | YAML + pydantic-validated settings | reproducible runs | A |
| Experiment tracking | MLflow Tracking (Postgres or SQLite backend; local artefact store) | compare runs, store artefacts | A |
| Pipeline entry points | Makefile + Python CLI (`python -m aegis.*`) | one command per stage | A |
| Feature definitions | single module `aegis/features` | identical training/inference preprocessing | A |
| Data/ML tests | pytest + schema checks | stop bad data/leakage | A |
| Model artefact | MLflow model + preprocessing artefacts + `uncertainty_table.json` | one deployable bundle | A |
| Registry | MLflow Model Registry using **aliases** (`candidate`, `champion`); stages are deprecated in recent MLflow versions — `UNKNOWN—VERIFY` installed version behaviour | controlled promotion | A (aliases) / B (full rules) |
| Inference service | FastAPI container loading the champion artefact | separate training and serving | A |
| CI | GitHub Actions | lint, tests, smoke training, Docker build | A |
| Monitoring | Postgres prediction log + scheduled drift/performance job (PSI/KS; Evidently optional) + service metrics | detect drift/degradation | B |
| Retraining | script + manual or scheduled trigger | refresh model | B |
| CD / cloud | Docker Compose on a VM or managed container host | public demo | B |

## 3. Experiment tracking contract
Every run logs: git commit, `dataset_version`, `feature_version`, config file, seed, fold, parameters, metrics (overall, T2D-only, delayed-window, per-scenario), artefacts (model, scalers, splits, plots, `uncertainty_table.json`, evaluation report), run tags (`track=A`, `candidate=...`). A run without these is rejected by the training CLI.

## 4. Dataset and model versioning
- `dataset_version` = hash of `data/MANIFEST.json`; `feature_version` = hash of the feature code + `configs/schema.yaml`.
- `model_version` = MLflow registered model version; lineage = run ID → dataset/feature versions → commit.
- Trained weights are published only after gate G-licence (adaptation status of weights is `UNKNOWN—VERIFY`).

## 5. Registry and promotion
`candidate → validated → champion → retired`, implemented with aliases/tags.
**Promotion rules (champion):** beats B0 and the best tabular baseline on held-out patients (paired CI), passes degradation tests, passes coverage check (tolerance in config), passes API contract test, has a model card. Promotion is a human-approved script (`make promote`).

## 6. Inference pipeline
Inference service loads `champion` at start; exposes `model_version`; uses the same `aegis/features` and `aegis/degradation`; returns trajectory, derived metrics, interval, reliability label and reasons. Offline mode loads the artefact from a mounted folder (no MLflow server required) so the demo runs without network.

## 7. Monitoring (Track B)
| Area | Signal | Method |
|---|---|---|
| Data quality | missingness, stale readings, out-of-range | rule checks per incoming event |
| Data drift | feature distributions vs training | PSI/KS on a schedule |
| Prediction drift | forecast distribution shifts | PSI on predicted peak/iAUC |
| Model performance | forecast vs actuals once the 180-min window completes (replay provides ground truth) | rolling MAE/peak error, coverage |
| System | latency, errors, replay lag | counters or structured logs |
Alert logic is documented; in the portfolio demo thresholds trigger a banner and a log entry.

## 8. Retraining
Triggers: drift above threshold, rolling error above threshold, new data version. Procedure: run training CLI with new `dataset_version`, compare to champion, promote only through §5. Cadence is documented but **not claimed as automated unless it is**.

## 9. Real vs decorative checklist
| Real | Decorative (do not do) |
|---|---|
| Run reproduces from `run_id` | Empty `monitoring/` folder |
| CI fails on leakage | Fake Grafana screenshots |
| Inference loads versioned artefact | "Kubernetes-ready" claims |
| Drift job produces report from logged predictions | Hardcoded drift numbers |

## 10. MLOps acceptance criteria
- [ ] Any reported number traceable to an MLflow run ID
- [ ] `make data` reproduces processed data from raw
- [ ] Training CLI refuses runs without required metadata
- [ ] Champion alias set; inference loads it; `/model/info` shows lineage
- [ ] CI runs lint, unit, data, smoke-train, API tests and Docker build
- [ ] (Track B) monitoring job produces a report from logged predictions
- [ ] (Track B) promotion script enforces the rules in §5
