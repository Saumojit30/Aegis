# configuration Specification

## Purpose
Provides strongly typed Pydantic models and YAML configuration loaders for pipeline parameters, model hyperparameters, assumption factors, and system run modes.

## Requirements

### Requirement: Typed Configuration Parsing
The configuration system MUST parse YAML files and environment overrides into validated Pydantic schemas.

#### Scenario: Loading valid configuration
- **WHEN** a valid YAML config file is loaded via `load_app_config`
- **THEN** it returns a typed configuration object with validated parameters
- **AND** `inference_mode` defaults to `inprocess` unless overridden to `http`.

#### Scenario: Loading invalid or malformed configuration
- **WHEN** an invalid YAML or out-of-range value (e.g. negative seed, invalid mode) is provided
- **THEN** Pydantic validation raises a `ValidationError` with details specifying the invalid field.
