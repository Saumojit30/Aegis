# Change Proposal: Uncertainty Quantification, Degradation Resilience, and Model Export

## Why
Real-world Type 2 Diabetes decision support systems frequently operate under degraded conditions: CGM dropouts (sensor detachment or warm-up), missing wearable sensors (no heart rate/accelerometer), sparse meal records, cold-start new patients ($K=0$), and novel Indian meal compositions far from the training distribution. A clinically trustworthy digital twin must not silently fail or produce false confidence under degradation; instead, it must:
1. Resiliently adapt its inference using available anchors and masking channels.
2. Provide calibrated horizon-wise uncertainty intervals via split-conformal inference that empirically widen under degradation.
3. Classify and communicate reliability state (`HIGH`, `MODERATE`, `LOW`) with clinician-actionable explanations.
4. Export self-contained offline model bundles (`.pt` weights, residual PCA basis, calibration conformal tables, and similarity priors) ready for the backend inference service (Phase A7) and replay dashboard (Phase A8).

## What Changes
1. **Degradation Scenarios (`aegis/degradation/scenarios.py`):**
   - Pure functional transform applying scenarios D0–D7 to input tensors and meal samples.
   - D0 (Identity), D1 (CGM dropout 15/30/60m), D2 (random CGM gaps), D3 (missing HR/METs), D4 (reduced sensor mode without CGM), D5 (incomplete meal macros), D6 (cold-start patient), D7 (out-of-support meal).
2. **Split-Conformal Uncertainty Intervals (`aegis/uncertainty/conformal.py`):**
   - Finite-sample split-conformal predictor computing $(1-\alpha)$ empirical quantiles of horizon residuals ($t \in [1..36]$) per scenario.
   - Serializes `uncertainty_table.json` containing step-wise half-widths for 80% and 90% confidence levels.
3. **Clinical Reliability Assessment (`aegis/uncertainty/reliability.py`):**
   - Deterministic rule engine evaluating degradation flags, interval widths, and support scores to assign `HIGH`, `MODERATE`, or `LOW` confidence and user-facing rationale.
4. **Degradation Evaluation & Ablation A6 (`aegis/evaluation/eval_degradation.py`):**
   - Evaluates Candidate S across D0–D7 and dropout lengths, generating `reports/degradation_summary.md` and `reports/uncertainty_coverage.md`.
5. **Model Artifact Exporter (`aegis/training/export.py`):**
   - Bundles model weights, PCA basis, similarity priors, and calibration tables into `artifacts/bundle/` and provides a clean loader `load_aegis_bundle(...)`.

## Impact
- **Phase A6 Completed:** Full degradation robustness and conformal prediction coverage verified.
- **Inference Service Unblocked:** Provides the frozen artifact bundle for the FastAPI backend and in-process inference provider in Phase A7.
- **Clinician Replay Dashboard Unblocked:** Dashboard can inject scenarios D0–D7 and display calibrated bands and reliability banners.
