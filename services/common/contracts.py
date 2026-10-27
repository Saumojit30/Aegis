"""Frozen request and response schemas for Aegis API and inference services."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

CLINICAL_DISCLAIMER = (
    "Research prototype using open and synthetic data. "
    "Model-based estimates only — not medical advice and not suitable for treatment decisions."
)


class InsulinInput(BaseModel):
    """Pharmacological insulin dose and timing parameters."""

    bolus_units: float = Field(default=0.0, ge=0.0, description="Bolus insulin dose in units")
    bolus_time_min: float = Field(
        default=0.0,
        description="Bolus timing relative to meal onset in minutes (negative for pre-bolus, e.g. -15)",
    )
    insulin_type: str = Field(
        default="rapid_acting",
        description="Type of insulin: rapid_acting, ultra_rapid, regular",
    )
    basal_rate_diff_u_hr: float = Field(
        default=0.0,
        description="Differential basal rate relative to equilibrium in U/hr (e.g. +0.5 or -0.2)",
    )
    isf_override: Optional[float] = Field(
        default=None,
        ge=1.0,
        le=500.0,
        description="Optional override for Insulin Sensitivity Factor in mg/dL per Unit",
    )


class MealInput(BaseModel):
    """Meal macronutrient and composition parameters."""

    preset_id: Optional[str] = None
    name: Optional[str] = None
    carbs_g: float = Field(default=0.0, ge=0.0, description="Carbohydrates in grams")
    protein_g: float = Field(default=0.0, ge=0.0, description="Protein in grams")
    fat_g: float = Field(default=0.0, ge=0.0, description="Fat in grams")
    fiber_g: float = Field(default=0.0, ge=0.0, description="Fiber in grams")
    amount_pct: float = Field(
        default=100.0, ge=1.0, le=300.0, description="Percentage of meal eaten"
    )
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] = "lunch"
    insulin: Optional[InsulinInput] = Field(
        default=None, description="Optional meal bolus / basal insulin input"
    )


class PredictRequest(BaseModel):
    """Request payload for POST /predict."""

    patient_id: str
    session_id: Optional[str] = "default"
    t0: str = Field(description="ISO 8601 prediction timestamp")
    meal: MealInput
    degradation: str = Field(default="D0", description="Degradation scenario D0-D7")
    g_t0: Optional[float] = Field(
        default=None, description="Current glucose at meal onset in mg/dL"
    )
    retrospective_sequence: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Preceding 60-min telemetry points (up to 12 steps)"
    )
    insulin: Optional[InsulinInput] = Field(
        default=None, description="Optional insulin dosing parameters"
    )


class IntervalBand(BaseModel):
    """Conformal uncertainty interval band."""

    level: float = Field(default=0.90, description="Coverage confidence level (e.g. 90%)")
    lower: List[float] = Field(description="Lower bound trajectory in mg/dL")
    upper: List[float] = Field(description="Upper bound trajectory in mg/dL")
    scenario: str = "D0"


class ForecastMetrics(BaseModel):
    """Summary metrics derived from forecast trajectory."""

    peak: float = Field(description="Predicted peak absolute glucose in mg/dL")
    time_to_peak_min: int = Field(description="Time to peak from t0 in minutes")
    delayed_mean_120_180: float = Field(description="Mean glucose in delayed window (120-180 min)")
    minutes_above_threshold: float = Field(default=0.0, description="Estimated minutes > 180 mg/dL")
    risk_flag: bool = Field(default=False, description="True if peak exceeds risk threshold")


class ReliabilityAssessment(BaseModel):
    """Qualitative reliability status and explanation."""

    label: Literal["high", "moderate", "low"] = "high"
    reasons: List[str] = Field(default_factory=list)


class PersonalisationStatus(BaseModel):
    """Patient few-shot adaptation status."""

    n_personal_meals: int = 0
    method: str = "residual_pca_ridge"
    prior: str = "similarity"


class ModelMetadata(BaseModel):
    """Lineage tracking metadata."""

    version: str = "v1.0"
    dataset_version: str = "v1.0.0"
    feature_version: str = "v1.0"


class PredictResponse(BaseModel):
    """Response payload for POST /predict."""

    horizon_min: List[int] = Field(default_factory=lambda: [5 * k for k in range(1, 37)])
    delta_glucose: List[float] = Field(description="Predicted delta excursions relative to G(t0)")
    glucose: List[float] = Field(description="Predicted absolute glucose trajectory in mg/dL")
    interval: IntervalBand
    metrics: ForecastMetrics
    reliability: ReliabilityAssessment
    personalisation: PersonalisationStatus
    model: ModelMetadata
    iob_trajectory: Optional[List[float]] = Field(
        default=None, description="Active Insulin On Board (IOB) trajectory in units"
    )
    net_insulin_deflection: Optional[List[float]] = Field(
        default=None, description="Superimposed glycemic deflection from insulin in mg/dL"
    )
    disclaimer: str = CLINICAL_DISCLAIMER


class ScenarioModifier(BaseModel):
    """What-if scenario modification parameters."""

    type: Literal["portion", "sequencing", "walk", "fat", "preset", "meal_time", "insulin"]
    amount_pct: Optional[float] = None
    delta_g: Optional[float] = None
    minutes: Optional[int] = None
    preset_id: Optional[str] = None
    shift_min: Optional[int] = None
    bolus_units: Optional[float] = None
    bolus_time_min: Optional[float] = None
    insulin_type: Optional[str] = None
    basal_rate_diff_u_hr: Optional[float] = None
    isf_override: Optional[float] = None


class SimulateRequest(BaseModel):
    """Request payload for POST /simulate."""

    patient_id: str
    session_id: Optional[str] = "default"
    t0: str
    meal: MealInput
    degradation: str = "D0"
    scenarios: List[ScenarioModifier] = Field(default_factory=list)


class ScenarioDifference(BaseModel):
    """Quantitative comparison against baseline meal forecast."""

    delta_peak: float
    delta_time_to_peak: int
    delta_delayed_mean: float


class ScenarioResult(BaseModel):
    """Result for one what-if scenario comparison."""

    type: str
    origin: Literal["model_driven", "assumption_driven"]
    trajectory: List[float]
    interval: IntervalBand
    metrics: ForecastMetrics
    delta_vs_baseline: ScenarioDifference
    reliability: ReliabilityAssessment
    notes: Optional[str] = None
    assumption: Optional[Dict[str, Any]] = None


class SimulateResponse(BaseModel):
    """Response payload for POST /simulate."""

    baseline: PredictResponse
    scenarios: List[ScenarioResult]
    disclaimer: str = CLINICAL_DISCLAIMER


# --- Ingestion Request Schemas ---


class PatientCreateInput(BaseModel):
    """Payload for POST /patients to register a digital twin."""

    patient_id: str
    group: Optional[str] = "T2D"
    age: Optional[float] = 55.0
    sex: Optional[str] = "female"
    bmi: Optional[float] = 28.5
    hba1c: Optional[float] = 6.5
    fasting_glucose: Optional[float] = 115.0
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    fasting_insulin: Optional[float] = None
    triglycerides: Optional[float] = None
    hdl: Optional[float] = None
    ldl: Optional[float] = None
    isf: Optional[float] = None
    cir: Optional[float] = None
    summary: Optional[str] = None
    ehr_extras: Optional[Dict[str, Any]] = None


class BiomarkerUpdateInput(BaseModel):
    """Payload for PUT /patients/{patient_id}/biomarkers."""

    fasting_glucose: Optional[float] = None
    fasting_insulin: Optional[float] = None
    hba1c: Optional[float] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    triglycerides: Optional[float] = None
    hdl: Optional[float] = None
    ldl: Optional[float] = None
    isf: Optional[float] = None
    cir: Optional[float] = None


class TelemetryPoint(BaseModel):
    """Single 5-minute wearable biometric data point."""

    ts: Optional[str] = None
    glucose: Optional[float] = None
    hr: Optional[float] = None
    mets: Optional[float] = None
    glucose_mask: Optional[float] = 1.0
    hr_mask: Optional[float] = 1.0
    mets_mask: Optional[float] = 1.0


class TelemetryIngestInput(BaseModel):
    """Payload for POST /patients/{patient_id}/telemetry (single point or window)."""

    points: Optional[List[TelemetryPoint]] = None
    ts: Optional[str] = None
    glucose: Optional[float] = None
    hr: Optional[float] = None
    mets: Optional[float] = None
    glucose_mask: Optional[float] = 1.0
    hr_mask: Optional[float] = 1.0
    mets_mask: Optional[float] = 1.0


class MealCreateInput(BaseModel):
    """Payload for POST /patients/{patient_id}/meals."""

    meal_id: Optional[str] = None
    ts_start: Optional[str] = None
    name: Optional[str] = "Meal"
    meal_type: Optional[Literal["breakfast", "lunch", "dinner", "snack"]] = "lunch"
    carbs_g: float = Field(default=50.0, ge=0.0)
    protein_g: float = Field(default=20.0, ge=0.0)
    fat_g: float = Field(default=15.0, ge=0.0)
    fiber_g: float = Field(default=5.0, ge=0.0)
    calories: Optional[float] = None
    amount_pct: float = Field(default=100.0, ge=1.0, le=300.0)
