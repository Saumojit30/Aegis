# Proposal: Foundation and Configuration (Phase A0)

## Why

Aegis is an end-to-end MLOps research prototype for Type 2 Diabetes post-meal glucose forecasting. Before writing data processing, machine learning models, or services, the project requires a rock-solid, reproducible foundation:
1. Standardised Python packaging and directory layout following the blueprint in `docs/07_DEVOPS_TESTING.md`.
2. Developer automation via `Makefile` targets (`setup`, `test`, `data`, `train`, `up`, `demo`).
3. Experiment tracking guardrails (`aegis/common/tracking.py`) enforcing mandatory metadata (git commit, dataset version, feature version, seed) so that zero untracked numbers enter reports or the UI.
4. Typed configuration management (Pydantic + YAML) with support for the refined dual-mode inference (`INFERENCE_MODE=inprocess|http`).
5. Linting, formatting, and CI testing skeletons so all future code adheres to quality gates from day one.

## What Changes

1. **Repository Structure**: Initialize Python package directories for `aegis`, `services/backend`, `services/inference`, `services/common`, `configs`, and `tests`.
2. **Packaging & Dependencies**: Create `pyproject.toml` with dependencies (FastAPI, PyTorch, MLflow, DVC, Pydantic, Ruff, Pytest).
3. **Developer Ergonomics**: Create `Makefile`, `.gitignore` (safeguarding raw datasets and secrets), `.env.example`, and `STATUS.md`.
4. **Tracking Guardrails**: Create `aegis/common/tracking.py` enforcing MLflow run validation and run-id traceability.
5. **Configuration System**: Implement `aegis/common/config.py` with Pydantic settings loading `configs/*.yaml` and environment variables.
6. **CI Skeleton**: Add `.github/workflows/ci.yml` running linting, formatting, and unit tests.

## Capabilities

### New Capabilities
- `foundation`: Core repository scaffolding, Makefile automation, and dev environment setup.
- `tracking`: Enforced MLflow metadata logging wrapper preventing unversioned/untraced experiment runs.
- `configuration`: Pydantic settings and YAML schema loader for pipeline, model, assumptions, and deployment parameters.

### Modified Capabilities
None (initial foundation batch).

## Impact

- Sets up root directories and project-wide virtual environment definitions.
- Establishes non-negotiable coding conventions and test runners (`pytest`).
- Provides baseline configs used by all subsequent data, ML, and backend batches.
