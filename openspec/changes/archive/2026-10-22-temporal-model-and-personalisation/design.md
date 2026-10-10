# Design: Deep Temporal Model, Structured Meal Layer, and Personalisation

## Context

Aegis predicts 36-step trajectory $\Delta G(k)$ for $k=1..36$ (5–180 min). Phase A3 baselines established the benchmark (B1 population mean MAE 17.36 mg/dL, B2 ridge MAE 17.80 mg/dL). Per `AGENTS.md`, the model must be evaluated on held-out patients; if candidate neural models fail to beat baselines, the winning baseline ships and the deep model is documented honestly.

## Goals / Non-Goals

**Goals:**
- Provide PyTorch dataset formatting `[B, 12, 6]` sequence, `[B, 8]` static, `[B, 16]` meal, and `[B, 4]` anchor tensors.
- Implement GRU sequence encoder with hidden size 32, static MLP (16), meal MLP (16), and fusion layer (32).
- Implement Unstructured Head (U) with linear projection to 36 outputs.
- Implement Structured Head (S) with fast/slow gamma basis curves parameterized by fat/fiber ratios + residual head.
- Implement weighted Huber loss with higher penalty for peak under-prediction on high excursions.
- Implement few-shot ridge adaptation on residual PCA basis ($r=3$) across chronological $K \in \{0, 1, 3, 5, 10\}$.
- Implement Gaussian kernel patient similarity for cold start ($K=0$).
- Compare Candidate S, Candidate U, and Baseline B3 across the 5 cross-validation folds.

**Non-Goals:**
- Heavy Transformer architectures (excluded per `03_ML.md` due to small 45-patient cohort).
- Live deployment containers (Batch 6).

## Decisions

- **Complexity Budget:** Parameter count under 25,000 parameters, ensuring rapid CPU training (seconds to minutes).
- **Structured Head Formulation:** $\Delta G(k) = K_p \cdot \text{carbs\_eff} \cdot [(1-\phi) B_{\text{fast}}(k) + \phi B_{\text{slow}}(k)] + \text{residual}(k)$ where $\phi = \sigma(w \cdot \text{ratios} + b)$ and $B(k) \propto (k/\tau) e^{1 - k/\tau}$.
- **Residual Regularization:** L2 regularization on residual head outputs to force the structural kinetics to carry the primary signal.
- **Chronological Adaptation:** When adapting patient twin on meal $m$, only meals $1..m-1$ are allowed as adaptation inputs.

## Risks / Trade-offs

- **Risk of Overfitting on Small Cohort:** Prevented by lightweight GRU dimensions, dropout ($p=0.2$), weight decay ($10^{-4}$), and early stopping on validation patients.
- **Structured Head Non-Superiority:** If Candidate S does not outperform Candidate U or B3 on delayed window (120–180 min), it is demoted to feature engineering per Decision Log.
