# Spec Delta: Data Pipeline

## Purpose
Specifies data ingestion, timestamp alignment, 5-minute grid resampling, meal event isolation, and leakage-free dataset splitting.

## ADDED Requirements

### Requirement: Uniform 5-Minute Grid Resampling
The cleaning module MUST align 1-minute raw sensor readings to a uniform 5-minute grid, interpolate glucose gaps <= 15 minutes, and quarantine corrupt records.

#### Scenario: Normal 5-minute resampling
- **WHEN** raw sensor observations with 1-minute timestamps are processed
- **THEN** output timestamps are aligned to exact 5-minute boundaries
- **AND** gaps <= 15 minutes are interpolated and flagged with `glucose_interpolated=True`
- **AND** gaps > 15 minutes remain missing with `glucose_missing=True`.

### Requirement: Meal Event and Macro Extraction
The meal extraction module MUST extract unique meal start events and calculate effective macronutrients scaled by the reported consumption percentage.

#### Scenario: Processing meal start row
- **WHEN** a row containing non-empty `Meal Type` is encountered
- **THEN** effective carbs, fat, protein, and calories are calculated as `macro * (amount_consumed / 100.0)`.

### Requirement: Zero Patient Leakage in Splits
Dataset splits MUST be grouped strictly at the patient level such that no patient appears across multiple split sets within the same cross-validation fold.

#### Scenario: Cross-validation split verification
- **WHEN** 5-fold cross-validation splits are generated
- **THEN** the intersection of patient IDs between training, validation, calibration, and test sets MUST be empty.
