# Spec Delta: Meal Head

## Purpose
Specifies the structured fast/slow carbohydrate and fat absorption kinetic head (Candidate S).

## ADDED Requirements

### Requirement: Bounded Dual-Pool Absorption Kinetics
The structured meal head MUST decompose the meal response into fast and slow gamma basis curves parameterized by meal macronutrient ratios.

#### Scenario: Forward pass through structured head
- **WHEN** effective carbohydrates, fat ratio, and fiber are input to the structured head
- **THEN** the slow fraction $\phi$ MUST be strictly bounded in $(0, 1)$ via a sigmoid activation
- **AND** fast basis time-to-peak MUST be bounded between 20 and 60 minutes
- **AND** slow basis time-to-peak MUST be delayed relative to the fast pool.
