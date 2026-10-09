# 09 — SUBMISSION PACK (Challenge)

Verify every requirement on the live Unstop page before submitting (`UNKNOWN—VERIFY`: deadline, video length, file formats, scoring weights, registration status).

## 1. Deliverables checklist
| Item | Requirement (as understood) | Status |
|---|---|---|
| Public GitHub repo | named `<TeamName>_<CollegeName>`; all files and links accessible to evaluators | [ ] |
| README | team details, project title, problem statement, use case, tech stack, open-source licence | [ ] |
| Architecture diagram | PDF or PPT | [ ] |
| Slide deck | PDF or PPT | [ ] |
| Demo video | 2–5 min; unlisted YouTube or recorded presentation | [ ] |
| Data provenance statement | sources, licences, synthetic flags | [ ] |
| Limitations + ethics statement | clear, unhedged | [ ] |

## 2. Licence handling and repository data policy
**What the licence says** (CC BY-NC-SA 4.0, per the Creative Commons deed and the PhysioNet page): you may **share** and **adapt** the data if you (1) give attribution, link the licence and indicate changes, (2) use it **non-commercially**, and (3) distribute adaptations under the **same licence**; you may not add extra restrictions. PhysioNet states the files are accessible to anyone who conforms to that licence. The deed is a summary, not legal advice. The dataset's `LICENSE.txt` is listed as empty on PhysioNet, so rely on the stated CC licence and re-check before release.

**A public repository is permitted within these conditions.** The policy below is a practical choice, not a legal prohibition:
| Item | Policy |
|---|---|
| Full raw CGMacros (~628 MB) | **Not committed** (size). Evaluators download it from PhysioNet via `make data` (open access) |
| Download script + `SHA256SUMS` check | Committed |
| Synthetic test fixtures | Committed (Apache-2.0) |
| Demo subset (a few participants, trimmed windows) for the offline demo | Committed under `data/demo/` with `LICENSE-DATA` (CC BY-NC-SA 4.0), `ATTRIBUTION.md`, and a "modified: resampled, trimmed, de-duplicated" notice |
| Full processed tables, trained weights | Not committed by default. Whether weights count as an adaptation is `UNKNOWN—VERIFY`; publish only if you accept CC BY-NC-SA 4.0 for them |
| Code | Apache-2.0 or MIT; LICENSE states the data keeps its own licence |
| Attribution | README + slide: cite DOI 10.13026/3z8q-x658 and the Scientific Data paper listed on the dataset page |

**Non-commercial question:** a student hackathon with prizes and an internship is probably non-commercial use, but "primarily intended for commercial advantage or monetary compensation" is a judgement and not settled for prize contests. Mitigation: describe the project as research/educational, do not market a product, and keep a synthetic-only demo seed as a fallback. `UNKNOWN—VERIFY`; ask the organisers or PhysioNet for certainty.

## 2b. What the Unstop listing allows (from a listing mirror; confirm on Unstop)
- Teams "are strictly required to use anonymized, open-source, or synthetic datasets for training".
- EHR: synthetic generators (e.g., Synthea) or anonymised clinical databases (e.g., MIMIC-IV). Sensor data: open-source wearable datasets or synthetic time series.
- The prototype must fuse static/historical data (simulated EHR: demographics, diagnoses, labs, genetic markers) with dynamic data (CGM, HRV, sleep, steps) and predict an adverse event.
- The listing does not require a particular dataset, or that data be included in the repo. It does require that "all files and links are accessible to the evaluation team" — met by a working download step plus the demo subset.
- Check on Unstop: the mirror shows registration closed on 26 Sep 2026; Phase 1 text mentions the top 5 while Phase 2 describes the top 10 presenting virtually.

## 3. Architecture diagram contents
Layers: Data sources → Data pipeline (DVC) → Training + MLflow → Model artefact + registry alias → Inference service → Backend (API, replay, DB) → Dashboard. Annotate: **two data streams**, **synthetic flag**, **degradation module**, **assumption-driven modifiers**, **monitoring (Track B)**. Source as Mermaid in `docs/architecture/architecture.mmd`; export PDF.

## 4. Slide deck (10–12 slides)
1. Title, team, one-line claim
2. Problem: post-meal variability + India context
3. Challenge mapping: two streams, prediction, dashboard
4. Data: CGMacros + synthetic layer + honest limits + attribution
5. Architecture diagram
6. Model: structure + meal layer (with ablation result)
7. Personalisation + similarity (K-curve, worst case)
8. Degradation: error-vs-scenario table + coverage
9. Live demo screenshots / flow
10. MLOps: run ID → model version → dashboard lineage
11. Limitations and ethics; what Aegis is not
12. Roadmap + impact (design statements only unless measured)

## 5. Video script (target 4:30)
Follow `06_FRONTEND.md` §8. Record in one take at the end of 13 Oct; re-record after final bug fixes. Record a **second fallback** of the whole live flow.

## 6. README template headings
Title · One-paragraph summary · Team details · Problem statement and use case · Challenge mapping · Architecture · Data and provenance (with licence and attribution) · Model and results (links to MLflow report) · What-if simulation and origin labels · Degradation and reliability · MLOps · Quick start · Tech stack · Limitations · Disclaimer · Licence · References.

## 7. Claims audit (G3)
`reports/claims.csv`: claim | where used | source (MLflow run or citation) | verified by | date. No claim ships without a source. Banned phrases: "clinically validated", "diagnoses", "reverses diabetes", "replaces CGM", "measures glucose from wearables", "treatment effect", "proven", "accurate" without a metric.

## 8. Judge Q&A prep
| Question | Honest answer outline |
|---|---|
| How do the two data streams feed the model? | Real `bio.csv` profile → patient encoder; CGM/HR/METs/meals → sequence and meal encoders; synthetic EHR extras are context, flagged |
| Why is the EHR part synthetic? | No open dataset links real EHR + CGM + meals; we separated real and synthetic and tested whether synthetic fields help (ablation A4) |
| Is this Indian data? | No. CGMacros is US-based; Indian meals are source-labelled presets; support check flags out-of-range meals |
| Can you share the data? | Licence allows sharing with attribution, non-commercial, share-alike; we ship a download script and a small attributed subset |
| Where do sequencing/walking numbers come from? | Literature-based assumptions in `assumptions.yaml`, labelled as assumptions |
| How was uncertainty calibrated? | Split conformal per scenario on calibration patients; empirical coverage on test patients reported |
| What happens when CGM drops? | Reduced-sensor mode, wider band, Low label, explicit warning; error numbers in the degradation table |
| How is it different from Twin Health? | Research prototype with transparent uncertainty and meal-structure model; no claim of clinical outcomes |
| Cost / deployability in India? | Design statements only: runs on CPU; no cost claims without measurement |
| Biggest weakness? | Small cohort (14 T2D), non-Indian data, assumption-driven scenarios — and we show the numbers |

## 9. Final dry-run (14 Oct)
Fresh machine/container → clone → one command → demo script start to finish → time it → check offline mode → verify links, licence files, attribution, repo name, video privacy setting → submit → save confirmation.
