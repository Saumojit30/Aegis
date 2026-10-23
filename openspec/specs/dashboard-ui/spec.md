# Capability Specification: Clinical Dashboard UI/UX (`dashboard-ui`)

This specification defines the presentation standards, layout requirements, and interaction behaviors for the Aegis clinician digital twin dashboard.

---

### Requirement 1: Tabbed Progressive Disclosure
- The dashboard **SHALL** provide a persistent top navigation bar partitioning functionality into four distinct views:
  1. `Live Replay & Forecast` (Real-time telemetry and postprandial curve).
  2. `What-If Simulator` (Counterfactual meal composition and behavioral intervention sandbox).
  3. `Patient Twin Profile` (Clinical screening labs, synthetic EHR history, and few-shot personalisation).
  4. `Sensor Quality & Audit` (Degradation stress-testing and uncertainty reliability).
- Switching tabs **MUST NOT** interrupt active WebSocket replay sessions or disconnect streaming telemetry.

### Requirement 2: Accessible Clinical Typography
- All textual labels, numerical data, and badges **SHALL** enforce a strict minimum font size of `12px` (`text-xs`).
- Sub-12px microtext (such as `text-[10px]` or `text-[11px]`) **SHALL NOT** be used in any view.
- Clinical metrics and glucose values **SHALL** use a clean monospaced font family for numerical clarity and tabular alignment.

### Requirement 3: Real-Time Trajectory Visualization
- The trajectory chart **SHALL** render:
  - Candidate S 180-minute neural prediction curve in solid emerald (`#10b981`).
  - 90% split-conformal uncertainty band as a semi-transparent shaded envelope.
  - Actual observed ground-truth postprandial measurements in dashed amber (`#f59e0b`).
  - Hyperglycemic safety threshold at $180\text{ mg/dL}$ in dashed rose (`#f43f5e`).
- The chart canvas **SHALL** provide responsive scaling with explicit axes labels (`Time in Minutes`, `Glucose in mg/dL`).

### Requirement 4: Counterfactual What-If Interaction
- The What-If view **SHALL** allow clinicians to select pre-calibrated regional Indian meal presets or modify carbohydrates, protein, fat, and portion percentage.
- The interface **SHALL** simultaneously display both the baseline trajectory and the modified intervention trajectory.
- Every simulated scenario **MUST** display an explicit badge indicating whether the result is `MODEL-DRIVEN` or `ASSUMPTION-DRIVEN`.

### Requirement 5: Keyboard Shortcuts & Ergonomics
- The replay cockpit **SHALL** support keyboard shortcuts:
  - Pressing `Space` **SHALL** toggle playback between Play and Pause.
  - Pressing `N` **SHALL** jump directly to the next clinical meal event.
