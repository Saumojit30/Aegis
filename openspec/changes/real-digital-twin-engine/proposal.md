# OpenSpec Change Proposal: Real Digital Twin Execution Engine

**Change Name:** `real-digital-twin-engine`  
**Status:** PROPOSED  
**Author:** Pair Programming Session  
**Target Capability:** `twin-engine`  
**Date:** 2026-10-23  

---

## 1. Problem Statement
The current service layer (`services/backend/replay/engine.py` and `services/backend/inference/provider.py`) functions as a **mock data representator** rather than a genuine digital twin:
1. **Hardcoded Synthetic Replay:** The replay engine synthesizes fake 144-step sinusoidal glucose curves in memory with hardcoded spikes at steps 24 and 72, completely ignoring the 5,184 actual 5-minute sensor readings in `data/processed/sensor_5min.parquet` and the 54 real clinical meals in `data/processed/meals.parquet`.
2. **Disconnected Inference Input Tensors:** When forecasting postprandial trajectories, `InProcessInferenceProvider` hardcodes `g_t0 = 120.0` and passes dummy zeros `seq = np.zeros((12, 6))` into Candidate S, ignoring the patient's actual preceding 60-minute wearable buffer ($t-60$ to $t$).
3. **Canned Adaptation & Simulation:** Personalisation returns static bundle defaults rather than computing closed-form Ridge adaptation on the patient's actual prior meals. What-If simulations apply fixed mathematical multipliers to curve coordinates rather than re-evaluating the neural model with modified macronutrient vectors.

This disconnect prevents the platform from functioning as a true digital twin for postprandial Type 2 Diabetes management.

---

## 2. Proposed Changes
This change replaces the mock service layer with a **genuine end-to-end digital twin pipeline**:
1. **Real-Data Replay Engine:** Stream continuous 5-minute equidistant readings (`glucose`, `hr`, `mets`, `cal_activity`, and missingness masks) directly from `data/processed/sensor_5min.parquet` for active patients (`P001`, `P002`, `P010`, `P011`, `P020`, `P021`), seamlessly indexed with real meal events from `meals.parquet`.
2. **Live Dynamic Tensor Ingestion:** When the replay cursor advances to a meal event (or when a manual forecast is requested), extract the patient's **actual preceding 12 steps (60 minutes)** from the replay buffer, compute true glucose velocity $dg/dt$ and anchor momentum, and feed the real dynamic sequence tensor into PyTorch Candidate S.
3. **Dynamic Ridge Personalisation:** Retrieve all verified chronological meals for this patient up to the current timestamp $t$, compute their actual postprandial residuals, and calculate real-time Ridge adaptation weights $\mathbf{w} = (\mathbf{B}^T \mathbf{B} + \lambda \mathbf{I})^{-1} \mathbf{B}^T \mathbf{r}$.
4. **Physiologically Grounded Counterfactual What-If:** Pass altered macronutrient vectors (carbohydrates, protein, fat, fiber) directly into Candidate S forward passes, combined with calibrated literature modifiers for behavioral scenarios (food sequencing and post-meal exercise).

---

## 3. Scope & Boundaries
- **In Scope:**
  - `services/backend/replay/engine.py`: Complete refactor to load and stream real patient parquet timeseries and meals.
  - `services/backend/inference/provider.py`: Connect real 60-min replay buffer tensors to `Candidate S` neural forward pass, real-time Ridge adaptation, and model-driven what-if recomputation.
  - `services/backend/models.py` & `db.py`: Align patient IDs and schemas (`P001`, `P002`, `P010`, etc.) with real processed data.
  - `services/backend/static/index.html`: Update dashboard to render real patient timelines, actual meal event markers, real historical overlays, and dynamic adaptation stats.
  - Regression testing in `tests/test_services.py` and integration tests.
- **Out of Scope:**
  - Re-training the foundational PyTorch weights (Candidate S weights in `artifacts/bundle/model.pt` are already trained on 5-fold CV).
  - Modifying the raw PhysioNet data acquisition scripts.
