# Spec Delta: Contracts

## Purpose
Specifies typed request and response contracts for model prediction and scenario simulation, freezing schema dimensions and origin labels.

## ADDED Requirements

### Requirement: Typed Predict and Simulate Contracts
The system contracts MUST enforce valid macronutrient bounds, UTC timestamps, horizon dimensions, and explicit scenario origin labels.

#### Scenario: Validating a predict request
- **WHEN** a client submits a prediction request
- **THEN** meal macros MUST be non-negative
- **AND** the response MUST return 36 horizon steps, derived metrics, and reliability assessment.

#### Scenario: Validating a scenario simulation
- **WHEN** a client submits a what-if simulation request
- **THEN** every scenario in the response MUST carry an origin label (`model_driven` or `assumption_driven`)
- **AND** assumption-driven scenarios MUST include a citation or factor notice.
