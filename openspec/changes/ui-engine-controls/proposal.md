# OpenSpec Change Proposal: Surface Advanced Engine Capabilities in Clinician Dashboard

**Change Name:** `ui-engine-controls`  
**Status:** PROPOSED  
**Author:** Antigravity Pair Programming Session  
**Target Capability:** `dashboard-ui`  
**Date:** 2026-10-31  

---

## 1. Problem Statement
The backend engine recently gained four major physiological and statistical capabilities:
1. **Pharmacological Bolus & Basal Insulin Modeling** (`aegis.models.pharmacology`): Analytical gamma absorption curves, IOB calculation, basal rate differentials, and 1800-Rule clinical estimators.
2. **Interval Conformal Portion Uncertainty Bounds** (`aegis.uncertainty.conformal`): $\pm \delta$ meal portion estimation noise maintaining $\ge 90\%$ finite-sample coverage via robust interval bounds $[L_{\text{robust}}(t), U_{\text{robust}}(t)]$.
3. **Expanded Patient Twin Biomarker Panel** (`services.backend.models`): Weight, height, fasting insulin, lipids, HOMA-IR, and clinical priors stored in SQLite.
4. **Dynamic REST Ingestion Endpoints** (`services.backend.main`): `PUT /patients/{id}/biomarkers`, `POST /patients/{id}/telemetry`, `POST /simulate`.

However, the current frontend dashboard ([`services/backend/static/index.html`](file:///f:/Portfolio%20projects/A_EGIS/Aegis/services/backend/static/index.html) and [`services/frontend/src/app/page.tsx`](file:///f:/Portfolio%20projects/A_EGIS/Aegis/services/frontend/src/app/page.tsx)) does not yet expose visual controls for these capabilities. Users cannot interactively simulate insulin boluses, see the robust portion conformal ribbon, or edit digital twin lab panels.

---

## 2. Proposed Changes

### A. What-If Sandbox: Pharmacological Insulin Therapy Section
- Add an **Insulin Therapy (Bolus & Basal)** card in the What-If Sandbox:
  - Rapid-acting bolus injection slider ($0.0\text{--}15.0\text{ Units}$, step $0.5\text{ U}$, default $0.0\text{ U}$).
  - Bolus timing relative to meal onset ($-30\text{ min}$ pre-bolus to $+60\text{ min}$ post-bolus, step $5\text{ min}$, default $0\text{ min}$).
  - Basal rate differential slider ($-1.0\text{ to } +1.0\text{ U/hr}$, step $0.1\text{ U/hr}$).
  - Real-time display of active Insulin on Board ($IOB(t)$) and negative glycemic deflection ($\Delta G_{\text{insulin}}(t)$).
  - Net counterfactual trajectory reflects endogenous digestion, physical activity, and pharmacological insulin clearance.

### B. Trajectory & Sandbox: Portion Uncertainty Slider & Dual-Band Conformal Ribbon
- Add a **Meal Portion Estimation Noise** slider ($\pm 0\%\dots 50\%$, step $5\%$, default $0\%$).
- When portion uncertainty $> 0\%$, the Chart.js visualizer dynamically renders the robust conformal uncertainty ribbon $[L_{\text{robust}}(t), U_{\text{robust}}(t)]$ as a shaded outer corridor or bounding dashed envelope around the point prediction.

### C. Twin Phenotype Tab: Full Clinical Lab Panel & Biomarker Editor Modal
- Expand Tab 4 (`Twin Phenotype`) to display the full clinical panel:
  - Weight ($78.0\text{ kg}$), Height ($168.0\text{ cm}$), Fasting Insulin ($14.2\text{ \mu U/mL}$), HOMA-IR ($4.84$).
  - Full lipid panel: Triglycerides ($185\text{ mg/dL}$), HDL ($42\text{ mg/dL}$), LDL ($128\text{ mg/dL}$).
  - 1800-Rule Clinical Priors: TDD ($42.9\text{ U}$), ISF ($42.0\text{ mg/dL/U}$), CIR ($11.7\text{ g/U}$).
- Add an **"Edit Twin Biomarkers"** modal:
  - Allows clinicians to update weight, height, fasting glucose, fasting insulin, lipids, or custom ISF/CIR.
  - Submits to `PUT /patients/{id}/biomarkers` and updates the active twin's baseline and what-if calculations.
  - Automatically re-derives BMI, HOMA-IR, and 1800-Rule ISF/CIR in the modal in real time.

### D. Design & Responsiveness Continuity
- Strictly preserve the clean monochrome visual architecture (charcoal `#0f172a`, white `#ffffff`, slate grey accents). Zero garish yellow, red, or purple colors.
- Full responsive wrapping and collapse on mobile/tablet viewports.
- Maintain 100% endpoint compatibility.

---

## 3. Scope & Verification
- Modify `services/backend/static/index.html` (primary dashboard).
- Modify `services/frontend/src/app/page.tsx` (Next.js dashboard).
- Verify with `pytest tests/test_services.py` and `ruff check`.
- Verify interactive UI controls via live browser testing.
