# Spec Delta: Temporal Model

## Purpose
Specifies the PyTorch multi-stream sequence and feature fusion neural network for predicting post-meal glucose excursions.

## ADDED Requirements

### Requirement: Multi-Stream GRU Fusion Encoder
The temporal model MUST encode sequence history with a GRU, static and meal features with MLPs, and fuse all streams into a unified representation.

#### Scenario: Forward pass through fusion encoder
- **WHEN** tensors of shape `seq [B, 12, 6]`, `static [B, 8]`, `meal [B, 16]`, and `anchor [B, 4]` are input
- **THEN** the network MUST output a 36-step trajectory vector `[B, 36]`.

### Requirement: Masked Weighted Huber Loss
Training MUST evaluate loss using a Huber function masked by target availability, with higher weights applied to peak under-predictions.

#### Scenario: Computing training loss
- **WHEN** loss is computed between predicted and target trajectories
- **THEN** masked steps with `target_mask == 0` MUST contribute zero loss
- **AND** under-predicted excursions when target $\Delta G > 50\text{ mg/dL}$ MUST be penalized with an extra penalty multiplier.
