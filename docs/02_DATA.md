# 02 — DATA

Single source of truth for all data decisions. Facts marked **[V]** were read from the official PhysioNet CGMacros page and data dictionaries (v1.0.0, published 28 Jan 2025). Anything marked `UNKNOWN—VERIFY` must be confirmed in task A1 before dependent work starts.

## 0. Repository data policy (summary)
Full raw CGMacros (~628 MB) is **not** committed: it is large and is downloaded from PhysioNet by `make data`. The repo holds the download script, checksums, synthetic test fixtures and a small attributed **demo subset** under `data/demo/` with `LICENSE-DATA` and `ATTRIBUTION.md`. Rationale and details: `09_SUBMISSION.md` §2. The challenge listing requires open, anonymised or synthetic data and that files/links be accessible to evaluators; it does not require the data to be inside the repository.

## 1. Dataset strategy
| Layer | Source | Role |
|---|---|---|
| Dynamic physiology | **CGMacros** (PhysioNet, open access) | CGM, HR, METs, meal macros per participant |
| Static baseline profile | CGMacros `bio.csv` | Age, sex, BMI, HbA1c, fasting glucose/insulin, lipids (real, screening data) |
| Synthetic EHR layer | **Synthea** (or fallback generator) | Medications, BP history, comorbidities, encounters — **flagged synthetic** |
| Meal presets | Published Indian food composition tables (e.g., IFCT 2017) | Source-labelled preset compositions; **values to be sourced by a human (G4)** |

Excluded: OhioT1DM (Type 1, different task), MIMIC-IV (ICU, credentialed access; the challenge permits it but it does not fit free-living meals), PPG-DaLiA (no glucose/BP labels), AI-READI (access not guaranteed — optional only).

## 2. CGMacros — verified facts [V]
| Item | Fact |
|---|---|
| Participants | 45: 15 non-diabetic (HbA1c < 5.7%), 16 pre-diabetic, 14 Type 2 diabetes (HbA1c > 6.4%) |
| Site | Sansum Diabetes Research Institute, Santa Barbara, California (US) |
| Duration | ~10 days free-living per participant |
| Main files | One CSV per participant, rows at **1-minute intervals** |
| Main columns | `Timestamp`, `Libre GL`, `Dexcom GL`, `HR`, `Calories (Activity)`, `Mets`, `Meal Type`, `Calories`, `Carbs`, `Protein`, `Fat`, `Fiber`, `Amount Consumed`, `Image Path` |
| Sensors | Abbott FreeStyle Libre Pro (15-min sampling, upper arm), Dexcom G6 Pro (5-min sampling, abdomen), Fitbit Sense. CGMs were blinded |
| Glucose range | 40–400 mg/dL (clipped by sensors) |
| Meals | Breakfast = protein shakes with varied macros; Lunch = fast-casual restaurant meal; Dinner = participant's choice. Lunch ≥3 h after breakfast, dinner ≥3 h after lunch; only water/unsweetened coffee between |
| Meal marker | `Meal Type` non-empty at the meal-start row; timestamp derived from photos; `Amount Consumed` = % of meal eaten |
| Supplementary | `bio.csv` (demographics, anthropometrics, labs, 3 fingerstick glucose values with times), `microbes.csv`, `gut_health_test.csv` |
| Bio fields | Age, Gender, BMI, Body weight (pounds), Height (inches), Self-identified ethnicity, A1c, Fasting glucose, Insulin, Triglycerides, Cholesterol, HDL, Non-HDL, LDL, VLDL, Cho/HDL ratio, collection time, 3 fingersticks + times |
| Dates | Time-shifted for privacy |
| Size/Access | ~628 MB zip; `wget -r -N -c -np https://physionet.org/files/cgmacros/1.0.0/` or `aws s3 sync --no-sign-request s3://physionet-open/cgmacros/1.0.0/ DEST`; checksums in `SHA256SUMS.txt` |
| Licence | **CC BY-NC-SA 4.0** — attribution, non-commercial, share-alike for adaptations; redistribution is permitted under those terms (see `09_SUBMISSION.md` §2). PhysioNet lists `LICENSE.txt` as empty; rely on the stated CC licence and re-check |
| Citation | Gutierrez-Osuna et al. (2025), PhysioNet, doi:10.13026/3z8q-x658 + the Scientific Data paper listed on the dataset page |

### Discrepancies and open points (resolve in A1)
- Page states BMI 21–46; data dictionary states 20.69–49.09. `UNKNOWN—VERIFY` actual range.
- Dictionary labels A1c unit as "mmol/mol" but range 4.6–8.5 matches percent. Treat as % **after verifying against group definitions**.
- Folder IDs run 1–49 but only 45 participants exist. Record missing IDs.
- How a 5-minute Dexcom stream appears in 1-minute rows (blank vs forward-filled vs repeated). `UNKNOWN—VERIFY`.
- Whether `Meal Type` marks one row per meal or also marks a "meal end". `UNKNOWN—VERIFY`.
- Exact number of meals per participant and per group (estimate ≈ 3/day × ~10 days). **Verify**.
- Whether every participant has HR and METs. Missingness per column per participant: audit.

## 3. What the dataset cannot support (state in README)
- No Indian population, no Indian foods; protein-shake breakfasts and restaurant lunches limit meal diversity.
- No blood pressure, no medication list, no insulin/medication timing, no sleep.
- No food-sequencing information; no controlled post-meal walking.
- Meals are ≥3 h apart by protocol → the **testable forecast window is ≤ 180 min**. A "3–5 hour delayed rise" **cannot be validated here**. Define the *delayed window* as **120–180 min**.
- Small T2D cohort (n=14).

## 4. Dataset integration strategy (Decision D1, human gate G1)
Synthea and CGMacros are independent populations; no real linkage exists.

**What is directly combined:** nothing at real-identity level.

**Chosen strategy — "Real static profile + flagged synthetic augmentation":**
1. The model's static input features come **only from real CGMacros `bio.csv`** (age, sex, BMI, HbA1c, fasting glucose, fasting insulin, triglycerides, HDL). This is the "historical clinical profile" and is genuinely used by the model.
2. A Synthea cohort (or fallback generator) supplies **fields CGMacros lacks**: medication history, BP readings/trend, comorbidities, encounter timeline. Each CGMacros participant is matched to the nearest Synthea patient on age, sex, BMI, HbA1c; matched fields are copied with `synthetic_pairing=true`.
3. Synthetic fields are used for **display context and scenario conditioning only**, not as predictive features, unless ablation A4 shows a benefit (not expected).
4. UI and README must say: "EHR extras are synthetic and paired for demonstration; they do not describe the real participants."

**Cannot be done:** claim that BP or medication influences predicted glucose; claim real patient identity linkage; claim the model learned a glucose–BP relationship.

**Fallback (D6):** if Synthea (requires Java; verify version) is not running by end of 8 Oct, use a rule-based generator with documented distributions and the same schema.

## 5. Raw data organisation
```text
data/
  raw/cgmacros/            # DVC-tracked, never in git (download via make data)
  raw/synthea/             # generated CSV export + seed + version
  demo/                    # small attributed subset, committed (LICENSE-DATA, ATTRIBUTION.md)
  interim/                 # cleaned per-participant parquet
  processed/
    meals.parquet  samples/  splits.json  presets/indian_meals.csv
tests/fixtures/            # synthetic fixtures, committed
reports/
  data_audit.md  claims.csv
```

## 6. Canonical schemas
### 6.1 `patients`
`patient_id` (e.g., `P001`), `source_id`, `group` (healthy/prediabetes/t2d), `age`, `sex`, `bmi`, `height_cm`, `weight_kg`, `hba1c`, `fasting_glucose`, `fasting_insulin`, `triglycerides`, `hdl`, `ldl`, `n_days`, `n_meals`.
Conversions: pounds→kg (×0.45359237), inches→cm (×2.54).

### 6.2 `sensor_5min`
`patient_id`, `ts`, `glucose` (Dexcom, mg/dL), `glucose_libre`, `hr`, `mets`, `cal_activity`, flags: `glucose_missing`, `hr_missing`, `glucose_interpolated`.

### 6.3 `meals`
`meal_id`, `patient_id`, `ts_start`, `meal_type`, `calories`, `carbs_g`, `protein_g`, `fat_g`, `fiber_g`, `amount_consumed_pct`, effective macros (`*_eff = macro × amount/100`), `minutes_since_prev_meal`, `image_path`.

### 6.4 `ehr_profiles` (synthetic extras)
`patient_id`, `synthetic_pairing` (true), `synthea_patient_id`, `diagnoses`, `medications`, `bp_history` (timestamp, systolic, diastolic), `encounters`, `pairing_distance`.

## 7. Data audit (task A1 output: `reports/data_audit.md`)
Report per participant and overall: rows, days, meals, glucose missingness (both sensors), HR/METs missingness, sampling pattern of each glucose column, duplicate timestamps, out-of-range values, clipped values (40/400), date-shift consistency, Libre vs Dexcom agreement, meal macro ranges, `Amount Consumed` distribution, meals with next meal < 180 min, group counts. Every `UNKNOWN—VERIFY` in §2 is resolved here and recorded in the decision log.

## 8. Cleaning rules
- Parse timestamps (`Month/Day/Year HH:MM`); sort; drop exact duplicates; for conflicting duplicates keep the first and log.
- Convert units; flag physiologically impossible values as missing; glucose clipped values flagged, not removed.
- Primary glucose = **Dexcom** (5-min). Libre kept for cross-check only. If Dexcom coverage is poor for a participant, document and decide (D2).
- Resample to a 5-minute grid. Interpolate glucose gaps ≤ 15 min (flag `glucose_interpolated`); longer gaps stay missing.
- No imputation across meals or days.
- Quarantine invalid rows to `data/interim/quarantine/` with reason codes.

## 9. Meal event construction
- Meal start = row with non-empty `Meal Type`. Verify one start per meal.
- Effective macros = macros × `Amount Consumed`/100.
- Derived: `fat_ratio = fat_g / (carbs+protein+fat)`, `fiber_per_carb`, `protein_ratio`, `glycaemic_load_proxy = carbs_g − 0.5·fiber_g` (a transparent proxy, not true GL), `minutes_since_prev_meal`.
- Drop meals with no usable glucose around them (rules in §12).

## 10. Feature engineering
**Patient features (static):** age, sex, BMI, HbA1c, fasting glucose, fasting insulin, triglycerides, HDL. (Microbiome excluded: far too many indicators for 45 patients.)

**Physiological sequence (per 5 min, window before t0):** glucose, glucose-missing mask, HR, METs, activity calories, glucose first difference.

**Anchor features:** `last_glucose`, `anchor_age_min`, `pre_meal_mean_30`, `pre_meal_slope_15`.

**Meal features:** effective carbs/protein/fat/fiber, calories, ratios, meal type one-hot, hour-of-day sin/cos, `minutes_since_prev_meal`, **fast/slow absorption features** (§11).

**Patient-response features (adaptation only, never in the global model):** personal residual coefficients from earlier meals (see `03_ML.md`).

Scalers and encoders are fitted **on training patients only**, stored as artefacts and reused at inference.

## 11. Meal absorption abstraction
Assumption-driven representation (not validated physiology):
- Fast pool: carbohydrate absorbed with an early peak.
- Slow pool: carbohydrate fraction `φ` that appears later; `φ` and delay increase with fat ratio (and possibly protein, fibre).
- Parameters (`τ_fast`, `τ_slow`, `d0`, `d1`, bounds) are **learned within bounds**, initialised from the audit (e.g., median time-to-peak of low-fat vs high-fat meals) — **no hardcoded physiology constants**.
- Output: two basis curves over the 36-step horizon used by the model head (`03_ML.md` §5).

## 12. Forecasting sample construction
DATA-DEPENDENT DECISION — confirm in A1/A2, do not hardcode before verification.
| Item | Default proposal |
|---|---|
| Unit of sample | one meal event |
| Prediction time `t0` | meal start timestamp |
| Observation window | 60 min before `t0` at 5-min (12 steps); test 120 min as ablation |
| Target | `ΔG(k) = G(t0 + 5k) − G(t0)`, k = 1…36 (5–180 min) |
| Primary evaluation window | 0–120 min (k ≤ 24) |
| Delayed window | 120–180 min (k = 25…36) |
| Derived targets | peak ΔG, time-to-peak, iAUC (above G(t0)), minutes above threshold |
| Threshold | default 180 mg/dL peak; configurable; clinical reference `UNKNOWN—VERIFY` before citing |
| Inclusion | ≥ 70% valid glucose in window; valid `G(t0)` within 10 min; ≥ 80% valid target points |
| Truncation | if the next meal begins before 180 min, mask the later target points |
| Risk event | `peak_glucose_120 > threshold` (check class balance per group) |

## 13. Splits
- **Group = patient.** Outer: 5-fold grouped cross-validation stratified by diabetes group. Inside each training portion: validation patients (early stopping) and **separate calibration patients** (conformal intervals). With 45 patients these sets are small (roughly 3–4 patients each) → report variability.
- **Personalisation/similarity:** chronological within patient. Use a patient's first K meals to adapt, evaluate on the remaining meals. K ∈ {0,1,3,5,10}.
- **Final reporting:** (a) all held-out patients, (b) T2D-only subset, with patient-level bootstrap confidence intervals.
- Splits are generated once, saved to `data/processed/splits.json`, versioned.

## 14. Leakage prevention (tests required)
1. No patient appears in more than one of train/val/calibration/test within a fold.
2. All features use data with timestamp ≤ `t0` (perturbation test: shifting future values must not change features).
3. Scalers/encoders fitted on training patients only.
4. Personalisation uses only meals strictly earlier than the evaluated meal.
5. Similarity neighbours exclude the target patient.
6. No target-derived feature (e.g., post-meal METs) in the forecast model.

## 15. Indian meal presets (G4 human gate)
`presets/indian_meals.csv` columns: `preset_id`, `name`, `portion_description`, `carbs_g`, `protein_g`, `fat_g`, `fiber_g`, `calories`, `source`, `value_type` (measured/estimated/illustrative), `verified_by`.
Initial list (values **blank until sourced**): rice + dal + vegetables; roti + dal + vegetables; biryani-style; paratha-based; high-fat thali; balanced plate.
Rules: never invent values; every preset passes a **support check** — distance to the nearest training meals in macro space; out-of-support presets trigger a low-confidence flag.

## 16. Synthetic EHR layer details
- Generate a Synthea cohort with diabetes/hypertension modules; record Synthea version, seed, config. Default Synthea demographics are US-based; do **not** claim an Indian synthetic population.
- Matching: standardise age, sex, BMI, HbA1c; nearest neighbour without replacement; store `pairing_distance`.
- BP: displayed as secondary context only.

## 17. Data validation (automated; CI runs on small fixtures, full data runs locally)
Schema/types, ranges, monotonic timestamps, duplicate checks, missingness ceilings per participant, meal macro non-negativity, unit sanity (BMI from height/weight within tolerance), split-leakage tests, sample-shape tests.

## 18. Dataset versioning
- DVC tracks `data/raw`, `data/interim`, `data/processed`.
- `data/MANIFEST.json`: file hashes, source URL, download date, licence, CGMacros version (1.0.0), Synthea version/seed, feature-code git commit.
- `dataset_version` = hash of manifest, logged to every MLflow run.

## 19. Pipeline architecture
```text
download → verify checksums → audit → clean (quarantine) → resample 5-min
→ meal events → static profile → synthetic EHR pairing → features
→ samples + masks → splits → validation tests → processed artefacts (DVC)
```
Single CLI: `python -m aegis.data.run --config configs/data.yaml`.

## 20. Data acceptance criteria
- [ ] Licence/data policy gate approved; `LICENSE-DATA` and `ATTRIBUTION.md` prepared
- [ ] Raw files downloaded and checksums verified (not committed)
- [ ] `reports/data_audit.md` resolves every UNKNOWN—VERIFY in §2
- [ ] Meals, sensor, patients tables produced with documented counts
- [ ] Samples built; counts per group reported
- [ ] Splits saved; leakage tests pass
- [ ] Synthetic EHR layer generated and flagged
- [ ] Indian preset file exists with sourced values (or marked blank and excluded)
- [ ] Demo subset prepared with attribution and modification notice
- [ ] `MANIFEST.json` and `dataset_version` produced
