# Tasks: Foundation and Configuration

## 1. Repository Layout & Packaging (A0.1, A0.2)

- [x] 1.1 Create directory tree: `aegis/`, `services/`, `configs/`, `tests/`, `reports/`, `scripts/`.
- [x] 1.2 Create `.gitignore` ignoring `data/raw`, `mlruns`, `.env`, `*.egg-info`, `__pycache__`, `.venv`.
- [x] 1.3 Create `.env.example` with standard defaults (`INFERENCE_MODE`, `MLFLOW_TRACKING_URI`, `PORT`, `SEED`).
- [x] 1.4 Create `pyproject.toml` with project metadata, dependencies, and tool configs (ruff, pytest, mypy).
- [x] 1.5 Create `STATUS.md` recording Phase A0 start, gates checklist, and environment state.
- [x] 1.6 Create `Makefile` with targets: `setup`, `test`, `data`, `train`, `up`, `demo`.

## 2. Experiment Tracking Guardrails (A0.3)

- [x] 2.1 Implement `aegis/common/tracking.py` providing `TrackedRunContext` and `start_tracked_run`.
- [x] 2.2 Add validation logic requiring `git_commit`, `dataset_version`, `feature_version`, `config`, and `seed`.
- [x] 2.3 Write unit test in `tests/test_tracking.py` verifying that missing metadata raises `ValueError`.

## 3. Configuration Management (A0.5)

- [x] 3.1 Implement `aegis/common/config.py` with Pydantic models for Data, Training, Model, Replay, and System.
- [x] 3.2 Create baseline YAML configs in `configs/`: `base.yaml`, `assumptions.yaml`, `degradation.yaml`.
- [x] 3.3 Write unit tests in `tests/test_config.py` verifying YAML parsing, validation, and invalid config rejections.

## 4. CI & Verification (A0.4)

- [x] 4.1 Create `.github/workflows/ci.yml` with linting, formatting, and pytest steps.
- [x] 4.2 Run `pytest` to verify all test suites collect and pass.
