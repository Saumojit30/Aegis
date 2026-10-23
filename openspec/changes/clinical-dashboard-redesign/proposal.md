# OpenSpec Change Proposal: Clinical Dashboard UI/UX Redesign

**Change Name:** `clinical-dashboard-redesign`  
**Status:** PROPOSED  
**Author:** Pair Programming Session  
**Target Capability:** `dashboard-ui`  
**Date:** 2026-10-23  

---

## 1. Problem Statement
The current clinician dashboard (`services/backend/static/index.html`) suffers from severe UI/UX deficiencies:
1. **Visual Clutter & Cognitive Overload ("AI Slop"):** All functionalities—patient selector, 72-hour replay controls, real-time telemetry, 180-min neural forecast, What-If simulator, Indian meal presets, personalisation metrics, nearest clinical twins, and sensor degradation buttons—are cramped into a single 3-column view.
2. **Illegible Microtext & Poor Visual Hierarchy:** Excessive use of tiny `text-[10px]` and `text-[11px]` labels, crammed cards, and low-contrast borders makes the interface look like an unpolished prototype rather than an intentional clinical software application (like Dexcom Clarity or Epic).
3. **Lack of Focused Clinical Workflows:** Clinicians and researchers perform distinct tasks that require dedicated focus:
   - *Task A:* Observing live continuous telemetry and post-meal trajectory response.
   - *Task B:* Experimenting with dietary counterfactuals and meal substitutions.
   - *Task C:* Inspecting patient digital twin demographics, synthetic EHR history, and few-shot adaptation curves.
   - *Task D:* Auditing sensor reliability under dropout scenarios.

---

## 2. Proposed Changes
Redesign the frontend into a **calm, modern, production-grade clinical application** with tabbed progressive disclosure:
1. **Header & Context Bar:**
   - Clean clinical identity, patient twin quick-switcher with rich badges (Age, Condition, Baseline $\text{HbA}_{1c}$, Fasting Glucose).
   - Replay control cockpit with prominent Play/Pause, Speed multiplier, and "Jump to Next Meal" button.
   - Clear WebSocket connectivity status and clinical research disclaimer.
2. **Tab 1: Live Monitoring & Trajectory Forecast (Primary View):**
   - High-impact, full-width time-series chart with generous padding.
   - Clean visualization of:
     - Baseline continuous CGM, HR, and METs streaming over WebSocket.
     - Candidate S 180-minute neural prediction curve.
     - Shaded 90% conformal prediction interval band.
     - Observed ground-truth trajectory overlay in amber dashed line.
     - Clinical threshold line at $180\text{ mg/dL}$.
   - Clear metric cards (Peak, Time to Peak, Delayed Elevation, Time > 180) with readable typography ($\ge 12\text{px}$).
   - Dynamic Reliability badge (`HIGH`, `MODERATE`, `LOW`) with human-readable clinical rationale.
3. **Tab 2: Counterfactual What-If Sandbox:**
   - Dedicated side-by-side dietary simulator.
   - Interactive Meal Composer: select Indian presets (Masala Dosa, Dal Roti, Biryani) or adjust custom carbohydrates, fat, and portion percentage.
   - Behavioral intervention toggles (Food Sequencing, Post-Meal Walk) with transparent `MODEL-DRIVEN` vs `ASSUMPTION` badges.
   - Delta impact cards displaying exact numerical changes in Peak Glucose and Time to Peak.
4. **Tab 3: Patient Digital Twin Profile & EHR:**
   - Patient baseline profile (demographics, screening labs, BMI).
   - Flagged synthetic EHR history (comorbidities, hypertension, medications).
   - Personalisation learning curve: visual display of how the model adapts from Cold Start ($K=0$) to Multi-Meal ($K=5$).
   - Clinical phenotype neighbors (nearest twins).
5. **Tab 4: Sensor Quality & Reliability Audit:**
   - Stress-testing lab to inject sensor dropouts (D1–D7) and observe real-time conformal interval expansion and warning banners.

---

## 3. Scope & Acceptance Criteria
- **In Scope:**
  - Complete refactor of `services/backend/static/index.html` with clean semantic Tailwind styling, accessible typography ($\ge 12\text{px}$ minimum floor), and responsive tabs.
  - Seamless integration with existing backend REST and WebSocket endpoints (`/patients`, `/replay/*`, `/predict`, `/simulate`, `/ws/replay/*`).
  - Tactile keyboard accessibility (`Space` to toggle replay, `N` for next meal).
- **Out of Scope:**
  - Modifying the underlying PyTorch Candidate S weights or feature extraction pipelines (already verified).
