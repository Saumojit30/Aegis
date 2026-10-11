# Specification: Backend REST API

## Requirements

### REQ-API-01: Health & Metadata
- `GET /health` SHALL return `{"status": "ok", "inference_mode": "...", "database": "..."}`.
- `GET /model/info` SHALL return architecture details, dataset lineage, and clinical disclaimer.

### REQ-API-02: Patient Twin Queries
- `GET /patients` SHALL list all clinical twins with profile and group metadata.
- `GET /patients/{id}` SHALL return twin profile and synthetic EHR comorbidity / blood pressure records.
- `GET /patients/{id}/state` SHALL return current stream values, data quality, and personalisation status.
- `GET /patients/{id}/similar` SHALL return nearest clinical twins and distance scores.
- `GET /meal-presets` SHALL return Indian and standard meal presets with carbohydrate and fat contents.

### REQ-API-03: Forecasting & Counterfactual Simulation
- `POST /predict` SHALL return 180-min point forecast, conformal interval bands, peak metrics, and reliability assessment.
- `POST /simulate` SHALL return comparison of baseline vs modified scenarios with explicit `origin` attribution (`model_driven` or `assumption_driven`).
