# features Specification

## Purpose
Specifies the single source of truth feature engineering module, including sequence formatting, wearable missingness masks, and meal support calculation.

## Requirements

### Requirement: Unified Feature Tensor Extraction
The feature extraction module MUST produce standardized tensors for `seq`, `static`, `meal`, and `anchor` feature groups without using future information.

#### Scenario: Extracting features at prediction time t0
- **WHEN** features are extracted for a meal event at time `t0`
- **THEN** all observations with timestamp > `t0` MUST be strictly excluded
- **AND** the `seq` tensor MUST include explicit binary masks for glucose, HR, and METs
- **AND** missing wearable channels MUST be zero-imputed.

### Requirement: Meal Support Score Calculation
The support module MUST compute the distance of meal macronutrient compositions from the training distribution and flag out-of-distribution meals.

#### Scenario: Evaluating an extreme or Indian preset meal
- **WHEN** a meal with macronutrient ratios outside the training distribution is evaluated
- **THEN** a support score between 0.0 and 1.0 is computed
- **AND** meals below the support threshold MUST be flagged as `is_out_of_support=True`.
