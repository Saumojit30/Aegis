# Proposal: Deep Temporal Model, Structured Meal Layer, and Personalisation (Batch 4)

## Why

Aegis forecasts individualised post-meal glucose trajectories up to 180 minutes. While tabular baselines B1/B2 provide an initial reference, predicting the non-linear, multi-phase glucose dynamics requires:
1. **Temporal Sequence & Feature Fusion**: A multi-stream GRU network that processes historical continuous sensor sequences (`[12, 6]`), patient static profiles (`[8]`), meal compositions (`[16]`), and baseline anchors (`[4]`).
2. **Structured Meal-Kinetics Head (Candidate S)**: Modeling gastric emptying and carbohydrate absorption via bounded gamma basis curves (fast vs slow pools governed by fat/protein/fiber ratios) versus an unstructured MLP head (Candidate U).
3. **Few-Shot Personalisation**: Adapting to a patient's historical response curves using a low-rank residual PCA basis with chronological shrinkage ($K \in \{0, 1, 3, 5, 10\}$).
4. **Similarity Cold-Start**: Bootstrapping new patients ($K=0$) using a Gaussian kernel similarity prior over screening clinical profiles.
5. **Evidence-Based Champion Selection**: Meeting **Checkpoint C2** by comparing Candidate S, Candidate U, and Baseline B3 on held-out patients across 5 folds.

## What Changes

1. **PyTorch Dataset**: Implement `aegis/models/dataset.py` with tensor batching, sequence masks, and target truncation handling.
2. **Temporal Model Architecture**: Implement `aegis/models/gru_fusion.py` with GRU sequence encoder, static/meal MLPs, fusion layer, and Unstructured Head (U).
3. **Structured Meal Head**: Implement `aegis/models/meal_head.py` with fast/slow gamma absorption functions, learnable parameter bounds, and residual regularization.
4. **Training Loop & Loss**: Implement `aegis/training/train.py` with weighted Huber loss, peak under-prediction penalty, early stopping, and MLflow tracking.
5. **Personalisation & Similarity**:
   - `aegis/personalisation/basis.py`: PCA basis extraction on training residuals.
   - `aegis/personalisation/adapt.py`: Chronological Ridge adaptation over earlier $K$ meals.
   - `aegis/personalisation/similarity.py`: Gaussian kernel similarity and nearest-neighbor prior.
6. **Model Decision & Checkpoint C2**: Implement `aegis/training/evaluate_models.py` generating `reports/model_decision.md` and selecting the champion forecaster.

## Capabilities

### New Capabilities
- `temporal-model`: PyTorch dataset, multi-stream GRU fusion encoder, weighted Huber loss, and training loop.
- `meal-head`: Structured fast/slow absorption basis functions parameterizing carbohydrate absorption curves.
- `personalisation`: Residual PCA basis fitting, chronological few-shot adaptation, and similarity kernel cold-start.

### Modified Capabilities
None (new capabilities building on Phase A1–A3 pipeline).

## Impact

- Provides the core machine learning inference artifact for the backend and dashboard.
- Generates logged ablation comparisons (S vs U vs B3) satisfying Checkpoint C2.
