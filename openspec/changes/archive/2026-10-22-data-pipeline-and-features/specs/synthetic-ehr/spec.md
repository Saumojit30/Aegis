# Spec Delta: Synthetic EHR

## Purpose
Specifies the pure-Python clinical synthetic EHR generator for demographic matching, medication histories, and blood pressure records.

## ADDED Requirements

### Requirement: Deterministic Clinical Profile Generation
The synthetic EHR generator MUST produce reproducible clinical profiles and blood pressure readings matched to patient screening demographics using a fixed random seed.

#### Scenario: Generating synthetic profiles for participants
- **WHEN** synthetic profiles are generated for a list of patient profiles
- **THEN** every profile MUST include `synthetic_pairing=True`
- **AND** hypertension staging and BP trajectories MUST adhere to published clinical distributions
- **AND** matching distance between the real profile and synthetic template MUST be recorded.
