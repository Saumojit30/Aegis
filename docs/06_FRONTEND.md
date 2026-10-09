# 06 — FRONTEND (CLINICIAN DASHBOARD)

## 1. UX goals
1. A clinician understands the patient's state in 5 seconds.
2. The forecast always shows **how much to trust it**.
3. Scenario comparison needs two clicks.
4. Every number shows its origin (measured, model, assumption, synthetic).
5. The disclaimer is always visible.

## 2. Stack
Next.js (App Router) + TypeScript, charting with Recharts or ECharts (decide in A8, D8), Tailwind CSS, typed API client generated from OpenAPI, WebSocket hook for replay.

## 3. User flow
```text
Select patient → overview (profile, synthetic EHR extras, BP context) → start replay
→ live glucose/HR → meal event → forecast appears (band + metrics + reliability)
→ actual glucose overlays → open What-if → compare scenarios
→ click "Interrupt sensor" → reliability drops, band widens, reasons shown
```

## 4. Layout
Header: patient selector · replay controls · model version · disclaimer strip.
Left column: Patient overview, Personalisation status, Similar patients.
Centre: Forecast chart, Forecast summary, What-if simulator.
Right column: Live state, Data quality and reliability, Model info and limitations.

## 5. Component specification
| Component | Purpose | Data / API | States | Interactions |
|---|---|---|---|---|
| PatientSelector | choose twin | `GET /patients` | loading, empty, error | select |
| PatientOverview | profile (real) and EHR extras (**"synthetic" badge**), BP context (**"synthetic" badge**) | `GET /patients/{id}` | skeleton, error | expand history |
| ReplayControls | start/pause/resume/restart, speed, "jump to next meal" | `POST /replay/*` | disabled when no session | buttons |
| LiveState | latest CGM, HR, METs, last meal, staleness | WS | stale-warning, disconnected | none |
| ForecastChart | history, predicted trajectory, interval band, meal marker, threshold line, **actual overlay** | WS + `/predict` | no forecast yet, unavailable, low-confidence styling | hover, legend toggles |
| ForecastSummary | peak, time-to-peak, delayed-window mean, minutes above threshold, risk flag | `/predict` | placeholder | tooltip with definitions |
| ReliabilityBadge | High / Moderate / Low + reasons | `/predict` | — | click for details |
| PersonalisationPanel | number of personal meals, prior type, "before vs after adaptation" toggle | state | K=0 message | toggle |
| SimilarPatients | 3–5 neighbours, similarity, note "similar profile ≠ same response" | `/similar` | empty | none (de-emphasised) |
| WhatIfPanel | meal preset/macros editor; scenario toggles: portion, fat, meal time, food sequencing, post-meal walk (10/20/30) | `/simulate` | running, error | compare table + overlay curves |
| ScenarioTable | baseline vs scenario deltas with **origin chips** (model-driven / assumption) | `/simulate` | — | sort |
| DegradationPanel | buttons D1…D7 ("Interrupt sensor 30 min", "Remove HR", "Unknown meal", "New patient mode") | `/replay/degrade` | active scenario highlighted | click to apply/clear |
| DataQualityStrip | missing/stale/invalid alerts | WS | ok / warning | click for log |
| ModelInfo | version, dataset/feature versions, limitations list | `/model/info` | — | expand |

## 6. Visualisation requirements
- Colour-blind-safe palette; do not rely on red/green alone.
- Interval band semi-transparent; width visibly changes with reliability.
- Threshold line labelled with units and "configurable".
- Low-confidence state: dashed prediction line + banner.
- Chart has a text summary for screen readers.
- Units everywhere (mg/dL, min).

## 7. Accessibility and responsiveness
Keyboard operable controls, visible focus, ARIA labels on charts and badges, minimum contrast 4.5:1, layout works at 1366×768 (demo laptop) and 1920×1080; tablet view collapses side columns.

## 8. Demo script (≈ 4 min; video target 4:30 total, within the 2–5 min limit — verify)
1. **0:00–0:30** Problem + India framing + disclaimer.
2. **0:30–1:00** Select patient; show real profile vs synthetic EHR extras (badges).
3. **1:00–1:40** Start replay; live CGM/HR; meal event → forecast with band; actual overlays.
4. **1:40–2:30** What-if: preset swap (Indian preset; note support/label), portion/fat (model-driven), sequencing/walk (assumption chip).
5. **2:30–3:15** "Interrupt sensor" → label drops to Low, band widens, reasons, "not suitable for treatment decisions".
6. **3:15–3:45** Personalisation: K=0 vs K=5; similar patients note.
7. **3:45–4:15** Evidence slide: error-vs-degradation table, ablation result, one failure case.
8. **4:15–4:30** Limitations, MLOps (run ID → model version in UI), close.
Fallback: pre-recorded video of the same flow; offline run script.

## 9. Frontend acceptance criteria
- [ ] All components in §5 render with real or mock data
- [ ] Origin chips and synthetic badges present everywhere required
- [ ] Degradation demo works in < 2 clicks
- [ ] Disclaimer visible on every screen
- [ ] Works from a clean machine with `docker compose up`
- [ ] Lighthouse accessibility check run, issues triaged
