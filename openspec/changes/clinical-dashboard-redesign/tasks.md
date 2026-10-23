# Implementation Tasks: Clinical Dashboard UI/UX Redesign

**Change:** `clinical-dashboard-redesign`  
**Status:** COMPLETED  

---

## Task List

### Phase 1: Layout Skeleton, Navigation & Theme Architecture
- [x] 1.1 Refactor `services/backend/static/index.html` structure: persistent clinical header, patient twin switcher, and replay cockpit.
- [x] 1.2 Implement accessible clinical design system: calm dark surfaces (`bg-slate-950`, `bg-slate-900`), semantic medical borders, and strict typography floor ($\ge 12\text{px}$).
- [x] 1.3 Implement tab navigation system with 4 distinct views (`forecast`, `whatif`, `profile`, `audit`).
- [x] 1.4 Add keyboard shortcuts (`Space` to toggle replay, `N` for next meal).

### Phase 2: Tab 1 — Live Replay & Trajectory Forecasting View
- [x] 2.1 Build real-time biometric telemetry strip (Current Glucose, HR, METs, Last Meal).
- [x] 2.2 Construct spacious Chart.js time-series canvas with explicit axes labels.
- [x] 2.3 Wire WebSocket streaming to update Candidate S forecast, 90% conformal band, and ground-truth amber overlay.
- [x] 2.4 Render clinical metric cards (Peak, Time to Peak, Delayed Elevation, Time > 180).
- [x] 2.5 Implement dynamic Reliability badge (`HIGH`, `MODERATE`, `LOW`) with human-readable diagnostic messages.

### Phase 3: Tab 2 — Interactive What-If Meal Simulator View
- [x] 3.1 Build interactive meal composer: preset selector (Indian dishes), portion stepper, and nutrient inputs (carbs, fat, protein).
- [x] 3.2 Add behavioral intervention toggles (Food Sequencing, Post-Meal Walk).
- [x] 3.3 Implement side-by-side comparative chart rendering baseline vs simulated curves.
- [x] 3.4 Display quantitative delta cards ($\Delta$ Peak, $\Delta$ Time to Peak, $\Delta$ Delayed Mean) with explicit `MODEL-DRIVEN` vs `ASSUMPTION` badges.

### Phase 4: Tab 3 — Patient Digital Twin Profile & EHR View
- [x] 4.1 Render clinical profile card: age, sex, BMI, fasting glucose, HbA1c, and eGFR.
- [x] 4.2 Display synthetic EHR records with prominent `SYNTHETIC` provenance badges.
- [x] 4.3 Construct Few-Shot Personalisation (K-Curve) learning card showing adaptation progression ($K=0 \rightarrow K=5$).
- [x] 4.4 Render nearest clinical phenotype neighbors.

### Phase 5: Tab 4 — Sensor Quality & Reliability Audit View
- [x] 5.1 Implement stress-test panel for Scenarios D1–D7 (CGM dropout, sensor gaps, missing wearables).
- [x] 5.2 Demonstrate real-time conformal interval expansion and reliability downgrade under stress.
- [x] 5.3 Display clinical guardrail warning banners.

### Phase 6: Automated Verification & Browser Testing
- [x] 6.1 Verify all integration tests in `tests/test_services.py` pass (11/11 passed).
- [x] 6.2 Check HTTP endpoints and WebSocket streaming connectivity.
- [x] 6.3 Audit code with `ruff` and verify zero styling regressions.
