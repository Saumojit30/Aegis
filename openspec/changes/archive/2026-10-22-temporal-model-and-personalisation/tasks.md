# Tasks: Deep Temporal Model, Structured Meal Layer, and Personalisation

## 1. PyTorch Dataset & Data Loader (A4.1)

- [x] 1.1 Implement `aegis/models/dataset.py` with `MealForecastingDataset` and collate functions supporting masks.
- [x] 1.2 Write shape and deterministic batching tests in `tests/test_temporal_model.py`.

## 2. Multi-Stream Architecture & Heads (A4.2, A4.3)

- [x] 2.1 Implement `aegis/models/gru_fusion.py` with GRU sequence encoder, static/meal MLPs, fusion layer, and Unstructured Head U.
- [x] 2.2 Implement `aegis/models/meal_head.py` with fast/slow gamma basis kinetics, learnable parameters, and residual head (Candidate S).
- [x] 2.3 Write tests in `tests/test_meal_head.py` verifying gradient flow, parameter bounds, and basis curve normalization.

## 3. Training Loop & Loss (A4.2, A4.4)

- [x] 3.1 Implement `aegis/training/train.py` with weighted Huber loss, peak penalty, early stopping, and MLflow logging.
- [x] 3.2 Add one-batch overfit test and smoke training tests.

## 4. Personalisation & Similarity (A5.1, A5.2, A5.3)

- [x] 4.1 Implement `aegis/personalisation/basis.py` fitting low-rank PCA residual basis ($r=3$).
- [x] 4.2 Implement `aegis/personalisation/adapt.py` executing chronological ridge adaptation across $K \in \{0, 1, 3, 5, 10\}$.
- [x] 4.3 Implement `aegis/personalisation/similarity.py` computing Gaussian clinical similarity and neighbor priors.
- [x] 4.4 Write unit tests in `tests/test_personalisation.py` verifying neighbor exclusion and chronological ordering.

## 5. Model Evaluation & Decision (A4.4, A5.4, Checkpoint C2)

- [x] 5.1 Implement `aegis/training/evaluate_models.py` evaluating S vs U vs B3 across 5 folds and computing $K$-curves.
- [x] 5.2 Generate `reports/model_decision.md` and `reports/ablations.md` satisfying Checkpoint C2.
