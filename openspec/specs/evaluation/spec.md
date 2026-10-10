# evaluation Specification

## Purpose
Specifies multi-horizon trajectory error metrics, peak metrics, and patient-level bootstrap confidence intervals for validating forecasts.

## Requirements

### Requirement: Multi-Horizon Trajectory Metrics
The evaluation module MUST calculate Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) across primary (0–120 min), delayed (120–180 min), and full (0–180 min) horizons.

#### Scenario: Calculating trajectory metrics
- **WHEN** predicted and ground truth trajectories are evaluated
- **THEN** separate MAE and RMSE values MUST be computed for steps 1..24, steps 25..36, and steps 1..36
- **AND** invalid/masked points MUST be excluded from error aggregation.

### Requirement: Patient-Level Bootstrap Confidence Intervals
The evaluation module MUST compute paired bootstrap confidence intervals (95% CI) resampled at the patient level rather than sample level.

#### Scenario: Generating confidence intervals
- **WHEN** evaluating metrics across a cohort of held-out test patients
- **THEN** bootstrap resampling MUST draw whole patients with replacement
- **AND** return empirical 2.5th and 97.5th percentiles.
