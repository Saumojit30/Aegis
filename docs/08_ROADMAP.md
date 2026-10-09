# 08 — ROADMAP

## 1. Tracks
| Track | Goal | Window |
|---|---|---|
| A — Challenge | Working prototype + submission pack | 7 Oct → submit **14 Oct 2026**; 15 Oct buffer only |
| B — Portfolio | Registry rules, monitoring, retraining, cloud deployment, model card, write-up | after submission |
Verify on the Unstop page: official submission deadline and that your team's registration is valid (a listing mirror showed registration closed on 26 Sep 2026). `UNKNOWN—VERIFY`.

## 2. Phase summary
| Phase | Name | Date | Gate/Checkpoint |
|---|---|---|---|
| A0 | Foundation | 7 Oct AM | |
| A1 | Data acquisition + audit + licence/data policy | 7 Oct | G-licence, resolve UNKNOWNs |
| A2 | Pipeline, EHR layer, features, splits | 8 Oct | **C1** (EOD): samples + leakage tests pass; G1 |
| A3 | Baselines | 9 Oct AM | |
| A4 | Temporal model + meal layer + ablations | 9–10 Oct | |
| A5 | Personalisation + similarity | 10 Oct | **C2** (EOD): model vs baselines decision; G2 |
| A6 | Uncertainty + degradation | 11 Oct | |
| A7 | Inference service + backend + replay (starts against mock on 9 Oct) | 9–12 Oct | |
| A8 | Frontend (starts against mock on 10 Oct) | 10–13 Oct | **C3** (12 Oct EOD): replay → forecast → dashboard works end-to-end |
| A9 | Testing, containers, CI | 12–13 Oct | |
| A10 | Submission pack | 13–14 Oct | G3, G5, G6 |
| — | Buffer | 15 Oct | no new features |

## 3. Phase details
For each: Objective · Prerequisites · Inputs · Tasks (see task file) · Outputs · Validation · Definition of done.

**A0 Foundation** — repo, structure, tooling, CI skeleton, MLflow + DVC, env. *Done when:* `make setup && make test` passes on a clean checkout; CI runs.
**A1 Data acquisition + audit** — licence/data-policy decision, download CGMacros, verify checksums, audit. *Outputs:* `reports/licence_decision.md`, `reports/data_audit.md`, resolved UNKNOWNs, decision-log entries. *Done when:* every UNKNOWN in `02_DATA.md` §2 is closed and the data policy is approved.
**A2 Pipeline** — clean, resample, meal events, static profile, synthetic EHR pairing, features, samples, splits, leakage tests, demo subset. *Done when:* sample counts reported; all leakage tests pass.
**A3 Baselines** — B0–B4, evaluation harness, MLflow logging. *Done when:* baseline table (overall, T2D, delayed window) exists with patient-level CIs.
**A4 Model** — GRU+fusion, structured and unstructured heads, ablations A1–A3. *Done when:* final-candidate comparison logged; decision proposed.
**A5 Personalisation** — residual-PCA ridge adaptation, similarity prior, chronological evaluation. *Done when:* K-curve and worst-case table logged.
**A6 Uncertainty + degradation** — degradation module, augmentation, conformal tables, coverage report, reliability rules. *Done when:* error-vs-scenario table and coverage report exist.
**A7 Services** — mock inference first; backend (DB, API, replay, WS, simulate); real inference swap. *Done when:* `03/05` acceptance criteria met.
**A8 Frontend** — components in `06_FRONTEND.md` against mock, then real. *Done when:* demo script runs end-to-end.
**A9 Testing/containers/CI** — full test pyramid, compose, offline script. *Done when:* clean-machine run succeeds.
**A10 Submission** — README, diagram, slides, video, fallback video, repo rename, licence files, claims audit. *Done when:* `09_SUBMISSION.md` checklist is complete.

### Track B phases
| Phase | Name | Output |
|---|---|---|
| B1 | Registry rules | `promote_model.py` enforcing promotion criteria |
| B2 | Monitoring | prediction log, drift/performance job, report, UI banner |
| B3 | Retraining | documented/automated retrain + comparison report |
| B4 | Cloud deployment | VM/containers, HTTPS, CD workflow, rollback doc, public URL |
| B5 | Model card + write-up | `reports/model_card.md`, blog/paper draft with ablations |
| B6 | Extended validation | more datasets/meal evidence, optional walking-signal analysis |

## 4. Critical path
Data policy + audit → pipeline/splits → forecasting dataset → baselines → model decision → inference artefact → real backend integration → demo → submission. Feature-module and contract definitions precede model and backend work.

## 5. Parallel work
After A2: A3/A4 (ML) ∥ A7 backend against mock ∥ A8 frontend against mock ∥ README/diagram drafts. A6 degradation module can start with A3 because it only needs feature definitions.

## 6. Blockers and dependencies
| Blocker | Resolves at |
|---|---|
| Registration/deadline confirmation on Unstop | before A0 (human) |
| CGMacros download/schema | A1 |
| Dexcom sampling representation, meal markers | A1 |
| Java/Synthea availability | A2 (fallback D6) |
| Indian preset nutrition values + sources | G4 (human) — before A8 demo build |
| Licence/data policy approval | G-licence in A1 |
| Model not beating baselines | C2 decision |

## 7. Milestones
M1 Data ready (C1) · M2 Model decision (C2) · M3 End-to-end demo (C3) · M4 Submission pack · M5 Submitted · M6 Portfolio deployment.

## 8. Scope-cut order (cut from top first)
1. Track B items
2. BP secondary panel
3. Similar-patients panel
4. Extra scenarios (keep sequencing + walk + portion)
5. Ablation A7 and optional deep-ensemble
6. Separate inference container (merge in-process behind the same interface, D7)
**Never cut:** two-stream fusion, working forecast, what-if comparison, degradation demo, submission pack.

## 9. Fallback rules
- If at C1 data is not ready: drop 120-min history ablation and structured head variants; focus on baseline + GRU.
- If at C2 the GRU does not beat B3: ship B3 as the forecaster; keep degradation/simulator story.
- If at C3 the real model is not integrated: ship with the best baseline artefact; never ship the mock as a real model.
- If the licence gate raises doubt about committing the demo subset: ship a synthetic-only demo seed and document the download step for real data.

## 10. Decision log
| ID | Decision | Context | Options | Chosen | Reason | Trade-offs |
|---|---|---|---|---|---|---|
| D1 | Dataset integration | No real link between CGMacros and Synthea | random pairing; cohort conditioning; flagged matched augmentation | Real static profile from `bio.csv`; flagged synthetic extras | honest, still two-stream | synthetic extras do not improve accuracy |
| D2 | Primary glucose signal | Libre 15-min vs Dexcom 5-min | either | Dexcom | finer sampling | verify coverage per participant |
| D3 | Forecast horizon | meals ≥3 h apart | 120 / 180 / 300 min | 180 min (primary eval 120) | data supports it | 3–5 h delayed effect untestable |
| D4 | Uncertainty | small cohort | ensembles, MC dropout, quantile, conformal | split conformal per scenario | checkable coverage | exchangeability assumption |
| D5 | Personalisation | ~30 meals/patient (verify) | fine-tuning vs residual ridge | residual PCA + ridge with similarity prior | stable with few meals | limited expressiveness |
| D6 | Synthetic EHR | Java/Synthea risk | Synthea vs generator | Synthea, fallback generator | speed risk control | US-based defaults |
| D7 | Inference placement | time pressure | separate service vs in-process | separate service, fallback in-process | MLOps story | extra container |
| D8 | Chart library | | Recharts / ECharts | decide in A8 | | |
| D9 | Model runtime | | PyTorch CPU vs ONNX | PyTorch CPU first; ONNX in Track B | speed | larger image |
| D10 | Sequencing/walking | not in data | learn vs assume | assumption-driven, labelled | honesty | not data-validated |
| D11 | Data in repo | CC BY-NC-SA 4.0; 628 MB; challenge needs accessible files | commit all; commit none; download script + small attributed subset | download script + checksums + synthetic fixtures + small attributed demo subset | permitted by licence, practical, accessible to judges | share-alike applies to the subset; weights held back until G-licence |

## 11. Definition of Done
```text
TRACK A
[ ] Registration/deadline confirmed; licence/data policy approved
[ ] Data audited; counts reported; licences recorded
[ ] Two-stream fusion implemented; EHR extras flagged synthetic
[ ] Leakage tests pass; patient-level splits saved
[ ] Baselines B0–B4 evaluated; final model chosen by evidence
[ ] Ablations A1–A6 logged
[ ] Personalisation + similarity evaluated (with worst cases)
[ ] Degradation table, conformal tables, coverage report
[ ] Backend + replay + simulate + DB + inference service
[ ] Dashboard with all required components and demo controls
[ ] Tests green; Docker one-command run; CI green; offline demo works
[ ] README, architecture diagram, slides, video, fallback video, repo renamed, licence files
[ ] claims.csv reviewed by a human (G3)
TRACK B
[ ] Registry promotion script; monitoring report; retraining doc/script
[ ] Cloud deployment + CD + rollback; model card; write-up
```
