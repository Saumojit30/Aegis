# Aegis: Clinician Replay & Video Walk-Through Script
**Target Duration:** 4 minutes 15 seconds (within Unstop 2–5 min window)  
**Deliverable:** Demo Video & Evaluator Live Replay Guide (Gate G5)  
**Presenter Setup:** Single screen, 1920x1080 resolution, offline runner active via `uv run python scripts/run_demo.py`.

---

## Pre-Recording Checklist
- [x] Run `python scripts/run_demo.py` to ensure local backend & static dashboard are active at `http://localhost:8000/dashboard`.
- [x] Clear browser cache and ensure audio levels are normalized.
- [x] Set display scaling to 100% and browser zoom to 100%.

---

## Detailed Timing, Cues, and Actions

### 1. Introduction, Clinical Framing & Disclaimer (0:00 – 0:35)
* **Visual:** Aegis Clinician Dashboard landing page at `http://localhost:8000/dashboard`. Header badge showing model version `Candidate S (Dual-Gamma Forecaster)`.
* **Presenter Spoken Script:**
  > "Welcome to Aegis, a Type 2 Diabetes Digital Twin research prototype built for the Happiest Health Digital Twin Challenge 2026.
  >
  > Postprandial glucose management is one of the hardest challenges in metabolic medicine. Identical meals cause wildly varying glucose excursions across different patients due to individual insulin sensitivity, carbohydrate absorption kinetics, and physiological variability.
  >
  > Today we demonstrate how Aegis combines continuous wearable streams with static clinical profiles to predict 180-minute post-meal trajectories with calibrated uncertainty and degradation resilience.
  >
  > *Important disclaimer:* Aegis is a research prototype on open and synthetic data. It is not a certified medical device, does not diagnose disease, and does not prescribe medication."

---

### 2. Patient Digital Twin & Synthetic EHR Layer (0:35 – 1:05)
* **Visual:** Click patient selector dropdown. Select `Patient 2133-002`. Point cursor to the Patient Overview card.
* **Presenter Spoken Script:**
  > "Let's inspect our digital twin for Patient 2133-002, a 64-year-old male with an HbA1c of 7.2% and a BMI of 28.4.
  >
  > Notice the interface clearly distinguishes real physiological baselines—sourced from PhysioNet's open-access CGMacros dataset under CC BY-NC-SA 4.0—from auxiliary electronic health records, which are deterministically generated and prominently labelled with yellow `SYNTHETIC` badges. This ensures absolute clinical provenance and transparency."

---

### 3. Replay Engine, Live Meal Detection & Conformal Forecasting (1:05 – 1:45)
* **Visual:** Click **"Start Replay"** at 5x playback speed. Watch cursor advance along the time-series chart. Click **"Jump to Next Meal"**.
* **Presenter Spoken Script:**
  > "We now initiate our asynchronous replay engine. As continuous glucose, heart rate, and metabolic activity stream into the system, a meal event occurs: 65 grams of carbohydrates and 24 grams of protein.
  >
  > Instantly, our model—Candidate S, powered by a temporal GRU encoder and a dual-gamma absorption head—projects the postprandial trajectory for the next 180 minutes.
  >
  > Observe the shaded prediction interval. This is not an uncalibrated heuristic; it is a split-conformal 90% prediction band guaranteeing finite-sample coverage. The dynamic reliability badge reports `HIGH` reliability, and as the true trajectory unfolds in yellow, the forecast tracks peak excursion and time-to-peak with an empirical held-out error under 13 mg/dL."

---

### 4. Interactive What-If Counterfactual Sandbox (1:45 – 2:35)
* **Visual:** Scroll to the What-If Simulator panel. Select preset `Masala Dosa with Sambar`. Toggle `Post-Meal 15-min Walk`. Click **"Run What-If Simulation"**.
* **Presenter Spoken Script:**
  > "In clinical practice, a patient asks: *'What happens if I eat a traditional Indian breakfast, or go for a brisk walk after eating?'*
  >
  > With Aegis's What-If Simulator, clinicians can test dietary hypotheses counterfactually. Here, we select a Masala Dosa preset calibrated from the Indian Food Composition Tables.
  >
  > Notice the table partitions our findings into two distinct classes of evidence:
  > - Blue `MODEL-DRIVEN` chips: The dual-gamma model re-evaluates the trajectory using altered macronutrient kinetics.
  > - Purple `ASSUMPTION` chips: Evidence-based literature modifiers—such as a 15-minute post-meal walk attenuating peak glucose by 20%.
  >
  > The comparison chart overlays both curves, allowing immediate visual contrast between the baseline and the modified regimen."

---

### 5. Degradation Stress-Testing & Reliability Clamping (2:35 – 3:15)
* **Visual:** Scroll to the Degradation Controls panel. Click **"Scenario D1: 30% CGM Dropout"**, then click **"Scenario D7: Out-of-Distribution Meal"**.
* **Presenter Spoken Script:**
  > "Real-world medical devices must fail gracefully. Aegis incorporates a strict Reliability Rules Engine evaluated across degradation scenarios D0 through D7.
  >
  > When we inject Scenario D1—simulating continuous sensor signal dropout—the system does not emit false certainty. Instead, the conformal uncertainty band immediately widens from ±26 mg/dL to ±34 mg/dL, and the reliability badge drops to `MODERATE`.
  >
  > If we inject an out-of-distribution meal with extreme carbohydrates exceeding our physiological bounds, the model clamps predictions to clinical safety ranges and flags the forecast as `LOW` reliability, explicitly advising the clinician that telemetry is uncalibrated for treatment decisions."

---

### 6. Few-Shot Personalisation & Clinical Similarity (3:15 – 3:45)
* **Visual:** Point to Personalisation Panel showing Adaptation meals $K=5$ and the Similar Patients table.
* **Presenter Spoken Script:**
  > "Generalised models struggle with inter-individual metabolic variation. Aegis solves this with closed-form residual Ridge personalisation.
  >
  > On held-out patients, moving from zero prior meals ($K=0$) to just 5 recorded meals ($K=5$) reduces postprandial MAE from 12.95 mg/dL down to 8.92 mg/dL—a 31% precision improvement.
  >
  > For newly onboarded patients with zero history, Aegis initializes a clinical similarity prior based on age, BMI, and fasting glycemia, gracefully bridging the cold-start gap."

---

### 7. Evidence, MLOps Lineage & Closing (3:45 – 4:15)
* **Visual:** Open Model Information footer modal showing MLflow Run ID, Dataset Hash, Git Commit Hash, and PyTorch Artifact Path.
* **Presenter Spoken Script:**
  > "Behind this clinician interface is an enterprise-grade MLOps system. Every inference output is linked to a deterministic dataset hash, a Git commit, and an MLflow experiment run.
  >
  > Our candidate model decisively outperformed all 5 standard clinical baselines, achieving an 81% Clarke Error Grid Zone A rating across 5-fold cross-validation with zero data leakage.
  >
  > Aegis demonstrates how calibrated uncertainty, physiological inductive bias, and rigorous software engineering can transform AI into a trustworthy partner for diabetes care.
  >
  > Thank you."

---

## Offline Fallback Instructions
If reviewing without an active internet connection or container runtime:
1. Clone the repository.
2. Ensure Python 3.12 is installed with `uv`.
3. Run:
   ```bash
   uv run python scripts/run_demo.py
   ```
4. The dashboard will automatically open at `http://localhost:8000/dashboard` backed by SQLite and pre-seeded demonstration data.
