# Spec Delta: Personalisation

## Purpose
Specifies few-shot residual adaptation and patient similarity cold-start bootstrapping.

## ADDED Requirements

### Requirement: Chronological Residual Ridge Adaptation
The personalisation engine MUST fit adaptation coefficients exclusively on meals preceding the target meal in chronological order.

#### Scenario: Adapting to target patient meals
- **WHEN** predicting for meal $m$ of patient $P$ with $K$ adaptation meals
- **THEN** only meals with timestamp $< t_m$ MUST be included in the adaptation set
- **AND** fitted coefficients MUST shrink toward the prior mean.

### Requirement: Similarity Kernel Prior for Cold Start
The similarity module MUST compute clinical profile similarity using a Gaussian kernel, strictly excluding the target patient from neighbor sets.

#### Scenario: Calculating cold-start prior
- **WHEN** computing the prior coefficients for a new patient ($K=0$)
- **THEN** target patient $P$ MUST be excluded from neighbor selection
- **AND** neighbor weights MUST sum to 1.0.
