# 01 — PROJECT DEFINITION

## 1. Overview
Aegis is a research-oriented **Type 2 Diabetes digital-twin prototype**. A *twin state* is maintained per patient from (a) a static clinical profile and (b) a dynamic stream of CGM, heart rate, activity and meal events. When a meal occurs, Aegis forecasts the glucose trajectory for the next 180 minutes, reports how reliable that forecast is, and lets a user compare model-based scenarios.

## 2. Problem statement
Post-meal glucose excursions are a major, patient-specific driver of poor glycaemic control in Type 2 diabetes, and people respond very differently to the same food. Existing consumer tools either (a) require a continuous sensor and give one generic response, or (b) hide their uncertainty. Aegis demonstrates a patient-specific forecast whose **confidence visibly changes when data quality changes**, with meal-composition awareness designed for Indian meals.

## 3. Why this is not "just another forecaster"
| Differentiator | What makes it real |
|---|---|
| Meal-structure layer | Fast/slow absorption representation with an ablation proving (or disproving) its value |
| Honest degradation | Error-vs-degradation table, calibrated per-scenario intervals, live "break the sensor" demo |
| Personalisation | Few-shot adaptation + similarity-based cold start, evaluated chronologically on held-out meals |
| Reproducible MLOps | Every number traceable to data version, code commit, config, run ID |

## 4. Target users
- **Primary (demo persona):** a clinician or diabetes educator reviewing one patient's twin and testing meal scenarios before advising.
- **Secondary:** a patient viewing a simplified, plain-language version.
- **Evaluators:** challenge jury (technical + clinical), recruiters, academic reviewers.

## 5. Goals
G1 Two-stream data fusion (static profile + dynamic stream) that the model actually uses.
G2 Working post-meal forecast with honest evaluation on held-out patients.
G3 Personalisation and similarity-based cold start, honestly evaluated.
G4 Scenario simulator with explicit origin labels.
G5 Degradation behaviour with calibrated uncertainty.
G6 End-to-end MLOps and deployment (Track A light, Track B full).
G7 Complete challenge submission package by 14 Oct 2026 (verify the official deadline).

## 6. Non-goals
- Diagnosis, insulin or medication advice, treatment recommendation.
- Glucose estimation from PPG/HR alone (never claimed).
- A validated Indian-population model.
- Multi-disease twins; blood pressure is secondary context only.
- Real patient data, real-time hospital integration, regulatory approval.
- LLM-generated clinical explanations (explanations are templated and citation-locked).

## 7. Functional requirements
| ID | Requirement |
|---|---|
| FR1 | Load a patient twin (profile + history) and display it |
| FR2 | Replay a patient's historical stream as a live feed (speed, pause, resume, restart) |
| FR3 | On a meal event, produce a 180-min forecast with derived metrics and an uncertainty band |
| FR4 | Overlay actual glucose as it arrives and show running forecast error |
| FR5 | Run scenarios: portion, fat level, meal composition preset, meal time (model-driven); food sequencing, post-meal walk (assumption-driven) |
| FR6 | Show baseline vs scenario difference in peak, time-to-peak, delayed-window level, time above threshold |
| FR7 | Inject degradations live and show reliability label, band and reasons |
| FR8 | Show similar patients (de-emphasised) and personalisation status (number of personal meals used) |
| FR9 | Show data-quality status, model version, limitations and disclaimer on every screen |
| FR10 | Show secondary BP context (synthetic EHR layer) clearly labelled |

## 8. Non-functional requirements
| ID | Requirement |
|---|---|
| NFR1 | `POST /predict` p95 latency under 500 ms on a laptop CPU (UNKNOWN—VERIFY, measure) |
| NFR2 | Whole system starts with one command and runs offline |
| NFR3 | Deterministic: fixed seeds; a result reproducible from a run ID |
| NFR4 | No full raw data in git; no secrets in code |
| NFR5 | Accessible dashboard (colour-blind-safe palette, keyboard navigation, text alternatives for charts) |

## 9. Scientific and medical boundaries
Aegis is a research prototype that demonstrates decision-support concepts using open de-identified and synthetic data. It never states or implies diagnosis, treatment, or clinical validation. The disclaimer text is fixed:
> "Research prototype using open and synthetic data. Model-based estimates only — not medical advice and not suitable for treatment decisions."

## 10. Challenge traceability
| Challenge requirement (verify on Unstop page) | Aegis component | Evidence artefact |
|---|---|---|
| One specific condition | Type 2 Diabetes | README, slides |
| Static/historical EHR-type data | `bio.csv` baseline profile + synthetic EHR layer | `docs/02_DATA.md`, DB `ehr_profiles` |
| Dynamic wearable/sensor data | CGMacros CGM, HR, METs, meals via replay | Replay demo |
| Prediction of an adverse/risk event | 180-min glucose trajectory + high-glucose risk | MLflow evaluation report |
| Clinician dashboard | Next.js dashboard | Demo video |
| Anonymised/open/synthetic data only | CGMacros (de-identified, open access) + Synthea (synthetic) | Data provenance statement |
| README, architecture diagram, slides, video, repo naming | `docs/09_SUBMISSION.md` | Submission pack |

## 11. Success criteria
- Track A: all items in `08_ROADMAP.md` Definition of Done (Track A) ticked.
- Forecast beats persistence and the best tabular baseline on held-out patients with a paired patient-level bootstrap interval; if not, the honest result is reported and the headline claim changes.
- Degradation table and calibrated coverage report produced.
- Live demo runs from a clean machine in under 5 minutes.

## 12. Risks
| Risk | Likelihood | Mitigation |
|---|---|---|
| Tiny T2D cohort (14) → noisy estimates | High | Train on all 45; report T2D separately; patient-level bootstrap CIs; say so openly |
| Synthea setup (Java) delays | Medium | Fallback rule-based EHR generator with documented distributions (decision D6) |
| Model does not beat baselines | Medium | Report honestly; pivot headline to degradation + simulator; ship best baseline |
| Meal layer does not help | Medium | Present as tested idea with ablation; keep as feature engineering |
| Time overrun | High | Cut order in `08_ROADMAP.md`; checkpoints C1–C3 |
| Live demo failure | Medium | Offline one-command run + fallback video |
| Licence misuse (NC/SA) | Medium | Gate G-licence; attribution; no full raw data in repo; small attributed demo subset; synthetic-only fallback demo |
| Registration/deadline uncertainty | Medium | Confirm registration and deadlines on the Unstop page immediately |
| Over-claiming | Medium | `reports/claims.csv`; human gate G3 |

## 13. Future expansion (Track B and beyond)
Indian-population CGM+meal validation; multi-condition twin (hypertension) with real paired data; prospective study design; richer food-sequencing evidence; federated personalisation.
