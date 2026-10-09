# Design: Foundation and Configuration

## Context

Aegis is entering Phase A0. The repository currently contains only documentation, task checklists, and agent rules. `AGENTS.md` mandates that no fabricated metrics, untracked runs, or secret leaks occur, and that all development adheres to strict contracts. Decision D12 also establishes pluggable dual-mode inference (`INFERENCE_MODE=inprocess|http`).

## Goals / Non-Goals

**Goals:**
- Provide a clean Python project structure adhering to `docs/07_DEVOPS_TESTING.md`.
- Enforce reproducible tracking via MLflow with strict metadata validation (raising errors on missing commit or dataset/feature hashes).
- Provide typed configuration management loading from YAML and environment variables.
- Enable `pytest` to collect and pass smoke tests on clean checkout.
- Provide a clear `STATUS.md` dashboard for tracking phase and gate progress.

**Non-Goals:**
- Downloading raw CGMacros data (deferred to Phase A1 / Batch 2).
- Implementing model training or inference logic (deferred to Batches 3–6).
- Building the Next.js frontend (deferred to Batch 6).

## Decisions

- **Dependency management:** Standard `pyproject.toml` using `setuptools`/`pip` compatible specification for cross-platform compatibility on Windows and Linux.
- **Tracking wrapper:** `aegis.common.tracking.start_tracked_run()` wraps MLflow's `start_run()` to enforce tags: `git_commit`, `dataset_version`, `feature_version`, `config_name`, `seed`.
- **Config parser:** Pydantic v2 `BaseSettings` + `pyyaml` with explicit model validation and clear error messaging for missing or out-of-range parameters.
- **Inference Mode default:** `INFERENCE_MODE` defaults to `inprocess` for rapid local execution, toggleable to `http`.

## Risks / Trade-offs

- **MLflow local tracking:** MLflow writes to `mlruns/` or sqlite by default. `mlruns` must be explicitly gitignored to prevent binary/artifact bloat.
- **Windows vs POSIX Makefile:** Makefile targets should use cross-platform commands or python-driven commands so they work seamlessly under PowerShell and bash.
