# AGENTS.md — Operating Rules for Antigravity

You are implementing Aegis from the blueprint in `docs/`. The blueprint is the single source of truth.

## 1. Before you write any code (every session)
1. Read `README.md` and this file.
2. Read the docs relevant to the current phase (see `docs/08_ROADMAP.md`).
3. Open `tasks/IMPLEMENTATION_TASKS.md`, find the current task, read its acceptance criteria.
4. Inspect the repository and `STATUS.md` to learn what already exists.
5. State in one paragraph what you are about to do and which task ID it serves.

## 2. Non-negotiable rules
- **No fabricated data, metrics, citations, nutrition values, or dataset statistics.** If you cannot verify a fact, write `UNKNOWN—VERIFY` and stop for a human decision.
- **Every number shown in the UI, README, slides or video must come from a logged experiment** (MLflow run ID) or a cited source. Keep `reports/claims.csv` listing claim → source run/URL.
- **Patient-level splits only.** Never split rows of the same patient across train/validation/test/calibration. A leakage test must exist and pass.
- **No future information in features.** Anything after the prediction time `t0` is off-limits as input, except explicitly named scenario inputs.
- **One feature-definition module** (`aegis/features`) is used by training, inference and the replay engine. Do not re-implement features elsewhere.
- **One degradation module** (`aegis/degradation`) is used by evaluation and by the replay engine. Do not re-implement it.
- **Simulation is not causation.** Scenario outputs are labelled `model_driven` or `assumption_driven`. Never write "treatment effect", "reverses", "cures", or "clinically validated".
- **Data policy:** never commit the full raw CGMacros dataset (`data/raw`) or full processed per-participant tables. Only the download script, checksums, synthetic fixtures and the approved attributed demo subset (`data/demo`, with `LICENSE-DATA` and `ATTRIBUTION.md`) may be committed. Do not commit trained weights until gate G-licence approves.
- No secrets in code. Use `.env` and `.env.example`.
- Do not add features, services or libraries outside the current phase without a logged decision.

## 3. Stub-first, contract-first
Backend and frontend develop against the **mock inference service** (fixed JSON contract in `docs/05_SYSTEM.md`) until a trained model exists. Contracts change only through a logged decision.

## 4. Conflict procedure
identify conflict → explain → propose change → update the relevant doc → add entry to the decision log in `docs/08_ROADMAP.md` → implement. Never change architecture silently.

## 5. After each task / phase
- Run the full test suite and linters.
- Update `STATUS.md` (task done / blocked / deviations).
- Record MLflow run IDs for any result.
- Commit with message `[<task id>] <summary>`.

## 6. Human gates — STOP and ask
- G-licence: dataset licence interpretation and repository data policy.
- G1: EHR pairing strategy.
- G2: final model selection.
- G3: any claim that goes into the README, slides or video.
- G4: Indian meal preset nutrient values and sources.
- G5: demo script and fallback video.
- G6: submission upload.
