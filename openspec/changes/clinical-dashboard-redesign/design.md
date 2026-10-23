# Technical Design: Clinical Dashboard UI/UX Redesign

**Change:** `clinical-dashboard-redesign`  
**Status:** PROPOSED  
**Capability:** `dashboard-ui`  

---

## 1. Design Philosophy & Anti-"AI Slop" Standards

To avoid the cluttered, generic look of typical AI-generated interfaces, this design adheres to strict **clinical software design standards** (inspired by systems like Dexcom Clarity and Epic MyChart):

| Anti-Pattern ("AI Slop") | Clinical Production Standard |
|---|---|
| Tiny unreadable fonts (`text-[10px]`, `text-[11px]`) | **Typography Floor:** Minimum font size of `12px` (`text-xs`) with legible line heights and font weights (`font-medium`, `font-semibold`). |
| Overcrowded 3-column screen fighting for space | **Tabbed Progressive Disclosure:** Tasks separated into 4 dedicated, focused views (`Monitoring`, `What-If`, `Profile`, `Audit`). |
| Generic rainbow gradients and glowing shadows | **Restrained Medical Palette:** Calm dark surfaces (`#0f172a`, `#1e293b`), high-contrast text (`#f8fafc`, `#94a3b8`), semantic medical accents (Emerald `#10b981`, Amber `#f59e0b`, Rose `#f43f5e`, Indigo `#6366f1`). |
| Non-interactive or confusing sliders | **Rich Interactive Controls:** Direct meal presets, portion steppers, numerical inputs, and keyboard shortcuts (`Space` for play/pause, `N` for next meal). |
| Hidden or mysterious data origins | **Explicit Evidence Badging:** Every counterfactual scenario displays an unmistakable `MODEL-DRIVEN` or `ASSUMPTION` badge with publication citations. |

---

## 2. Layout & Information Architecture

```
+---------------------------------------------------------------------------------------------------------+
| [AE] Aegis Clinician Twin  |  Patient Selector [P020 (T2D, 58y, HbA1c 7.4%)]  |  Replay HUD: [▶] [⏭] [⏸] |
+---------------------------------------------------------------------------------------------------------+
| Tabs: [ 📈 Live Replay & Forecast ]  [ 🧪 What-If Sandbox ]  [ 👤 Patient Twin Profile ]  [ 🛡️ Audit ] |
+---------------------------------------------------------------------------------------------------------+
|                                                                                                         |
|  ACTIVE TAB VIEW (Spacious, full-width container with clean card hierarchy)                             |
|                                                                                                         |
|  - TAB 1: Live Telemetry Bar + Large Forecast Chart (Candidate S + 90% Conformal + Ground Truth)       |
|  - TAB 2: Interactive Meal Builder + Side-by-Side Before/After Comparison Chart + Delta Cards           |
|  - TAB 3: Biometric Labs + Synthetic EHR Timeline + Personalisation Learning Curve                      |
|  - TAB 4: Sensor Degradation Lab (D0-D7) + Reliability Rules Engine Diagnostic                         |
|                                                                                                         |
+---------------------------------------------------------------------------------------------------------+
| Footer: Model Architecture (Candidate S) | Dataset Lineage | Research Disclaimer (Non-Medical Device)   |
+---------------------------------------------------------------------------------------------------------+
```

---

## 3. Detailed Component Specifications

### 3.1 Persistent Header & Replay HUD
- **Twin Selector:** Dropdown displaying real patient IDs, diagnosis group (`T2D`, `Prediabetes`, `Healthy`), age, and baseline $\text{HbA}_{1c}$.
- **Replay Control Group:**
  - `Play / Pause` button with dynamic icon and green/slate states.
  - `Next Meal ⏭` button to jump instantly to verified clinical meals.
  - `Speed Selector` (1x, 5x, 10x, 50x).
  - Live WebSocket connectivity indicator with real-time ping indicator.

### 3.2 Tab 1: Live Monitoring & Trajectory Forecast
- **Telemetry Strip:** Clean cards for Current Glucose (with delta arrow), Heart Rate, METs, and Last Meal timestamp.
- **Main Trajectory Chart:**
  - High-resolution Chart.js canvas with 180-minute post-meal timeline ($T=36$ five-minute intervals).
  - Datasets:
    1. `Threshold Line`: $180\text{ mg/dL}$ dashed red line.
    2. `90% Conformal Band`: Shaded emerald semi-transparent region.
    3. `Candidate S Forecast`: Solid emerald curve with smooth tension.
    4. `Observed Ground Truth`: Dashed amber line representing actual clinical trial measurements.
- **Clinical Summary Cards:**
  - `Peak Glucose`: Numerical peak and risk alert.
  - `Time to Peak`: Minutes from ingestion to maximum excursion.
  - `Delayed Elevation`: Mean glucose in hours 2–3 (120–180 min).
  - `Reliability Badge`: Clear `HIGH`, `MODERATE`, or `LOW` badge with explicit diagnostic explanations.

### 3.3 Tab 2: What-If Dietary Simulator
- **Left Panel (Meal & Scenario Composer):**
  - Preset Selector: Pre-calibrated regional Indian dishes (Masala Dosa, Dal Roti, Chicken Biryani) from ICMR-NIN IFCT 2017.
  - Custom Nutrient Controls: Sliders and numerical inputs for Carbohydrates (g), Protein (g), Fat (g), and Portion (%).
  - Behavioral Toggles: "Food Sequencing" (veggies/protein first) and "15-min Post-Meal Walk".
- **Right Panel (Comparative Analysis):**
  - Dual-curve Chart overlaying Baseline Meal vs Simulated Intervention.
  - Delta Cards: $\Delta$ Peak ($\text{mg/dL}$), $\Delta$ Time to Peak ($\text{min}$), and $\Delta$ Delayed Mean.
  - Evidence Origin Badges: Explains whether the curve modification was computed by the neural network or grounded in clinical literature.

### 3.4 Tab 3: Patient Digital Twin Profile & EHR
- **Clinical Demographics:** Age, Sex, BMI, Fasting Glucose, HbA1c, and Estimated GFR.
- **Synthetic EHR Records:** Medical history, diagnoses, and antihypertensive medications clearly flagged with `SYNTHETIC` markers.
- **Few-Shot Personalisation (K-Curve):** Interactive progress card showing current meal count $K$, adaptation method (Residual Ridge on $r=3$ PCA basis), and accuracy progression ($12.95\text{ mg/dL}$ at $K=0 \rightarrow 8.92\text{ mg/dL}$ at $K=5$).

### 3.5 Tab 4: Sensor Quality & Degradation Audit
- **Stress-Test Scenarios:** One-click triggers for Scenarios D1 (CGM Dropout), D2 (Gaps), D3 (Missing Wearables), D4 (CGM Absence), and D7 (Out-of-Support Meal).
- **Audit Response:** Live demonstration of uncertainty interval expansion, reliability downgrades, and clinical guardrail notices.
