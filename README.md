# Aegis — Type 2 Diabetes Digital Twin (Research Prototype)

> Built for the Happiest Health **Digital Twin Challenge 2026** and as an end-to-end MLOps portfolio project.
> **Not a medical device. Not a diagnostic tool. Not a treatment recommender.** Outputs are model-based scenario simulations on open and synthetic data.

Repository name for submission: `<TeamName>_<CollegeName>` (rename before publishing).

## What Aegis does
1. Holds a **patient twin state** built from a static clinical profile (screening labs and anthropometrics from CGMacros `bio.csv`, plus a clearly flagged synthetic EHR layer) and a dynamic stream (CGM, heart rate, METs, meals).
2. **Forecasts the post-meal glucose trajectory** (up to 180 min) when a meal event occurs, with peak, time-to-peak, delayed-window elevation and time-above-threshold.
3. **Adapts to the individual** from their own earlier meals, and starts new patients from *similar* patients.
4. Runs **what-if scenarios**: model-driven (meal composition, portion, timing) and assumption-driven (food sequencing, post-meal walk), always labelled by origin.
5. Shows **how reliability changes when data degrades** (CGM dropout, missing wearable, unknown meal, new patient) and refuses to look confident when it should not.
6. Ships as a **reproducible MLOps system**: tracked experiments, versioned data and models, containerised inference, CI, monitoring (Track B), deployment.

## Architecture (summary)
```text
CGMacros (open)  Synthea (synthetic)         Indian meal presets (source-labelled)
      │                 │                              │
      └────── data pipeline (DVC, validated, leakage-tested) ──────┘
                              │
                 training (MLflow-tracked, config-driven)
                              │
                 model artifact (versioned, aliased)
                              │
   Postgres ◄── Backend API + Replay engine ──► Inference service
                              │
                     Next.js clinician dashboard
```

## Documentation map
| File | Purpose |
|---|---|
| `AGENTS.md` | Operating rules for the coding agent |
| `docs/01_PROJECT.md` | Scope, requirements, challenge traceability |
| `docs/02_DATA.md` | Datasets, integration, features, splits, leakage, repository data policy |
| `docs/03_ML.md` | Models, meal layer, personalisation, uncertainty, degradation, evaluation |
| `docs/04_MLOPS.md` | Tracking, versioning, registry, CI/CD, monitoring |
| `docs/05_SYSTEM.md` | Backend, API, database, replay, simulation |
| `docs/06_FRONTEND.md` | Dashboard and demo script |
| `docs/07_DEVOPS_TESTING.md` | Repo layout, Docker, CI, tests, deployment, security |
| `docs/08_ROADMAP.md` | Phases, day plan, checkpoints, decision log |
| `docs/09_SUBMISSION.md` | Challenge deliverables, licence handling, video, slides, Q&A |
| `tasks/IMPLEMENTATION_TASKS.md` | Agent-executable task list |

## Quick start (target state)
```text
make setup        # env + dependencies
make data         # download CGMacros from PhysioNet + verify checksums + build features (DVC)
make train        # train + log to MLflow
make up           # docker compose up (frontend, backend, inference, db, mlflow)
make demo         # start replay for the demo patient (uses data/demo, works offline)
```

## Data and licence notes
- **CGMacros v1.0.0** (PhysioNet, open access) is licensed **CC BY-NC-SA 4.0**: sharing and adapting are allowed with attribution, for non-commercial use, with adaptations shared under the same licence. See `docs/09_SUBMISSION.md` §2 for the repository data policy.
- The repository contains **code, configs, synthetic test fixtures and a small attributed demo subset** — not the full raw dataset. Fetch the full data with `make data` (downloads from PhysioNet and verifies checksums).
- Code licence: Apache-2.0 (code only). Data and data-derived files under `data/demo/` keep CC BY-NC-SA 4.0 (`LICENSE-DATA`, `ATTRIBUTION.md`).
- Citation: cite the CGMacros PhysioNet DOI (10.13026/3z8q-x658) and the associated Scientific Data paper listed on the dataset page.

## Limitations (read before using any number)
CGMacros participants were recruited in California; breakfasts were protein shakes and lunches were a fast-casual restaurant meal. The cohort is small (14 participants with Type 2 diabetes). Indian meals are represented through source-labelled composition presets, not through Indian training data. Food-sequencing and walking effects are literature-based assumptions unless an experiment in `03_ML.md` shows otherwise.
