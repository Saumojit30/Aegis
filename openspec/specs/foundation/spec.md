# foundation Specification

## Purpose
Establishes the core repository scaffolding, dependency management, automation scripts, and status reporting required for reproducible execution.

## Requirements

### Requirement: Repository Structure
The codebase MUST provide standard package directories, environment templates, and ignore rules preventing secret or raw-data leakage.

#### Scenario: Clean checkout inspection
- **WHEN** a developer inspects the repository root
- **THEN** `.gitignore` must ignore `data/raw/`, `mlruns/`, `.env`, and python cache files
- **AND** `.env.example` must document all required runtime environment variables
- **AND** `STATUS.md` must record project phase, active gates, and current status.

### Requirement: Automation Targets
The repository MUST provide standard `Makefile` targets for core lifecycle actions.

#### Scenario: Running lifecycle targets
- **WHEN** `make test` or equivalent python test runner is executed
- **THEN** pytest runs and collects tests from `tests/` without errors.
