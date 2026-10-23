"""Frozen request and response schemas for Aegis API and inference services."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

CLINICAL_DISCLAIMER = (
    "Research prototype using open and synthetic data. "
    "Model-based estimates only — not medical advice and not suitable for treatment decisions."
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


class PredictRequest(BaseModel):
    """Request payload for POST /predict."""

    patient_id: str
    session_id: Optional[str] = "default"
    t0: str = Field(description="ISO 8601 prediction timestamp")
    meal: MealInput
    degradation: str = Field(default="D0", description="Degradation scenario D0-D7")
    g_t0: Optional[float] = Field(default=None, description="Current glucose at meal onset in mg/dL")
    retrospective_sequence: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Preceding 60-min telemetry points (up to 12 steps)"
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
    disclaimer: str = CLINICAL_DISCLAIMER


class ScenarioModifier(BaseModel):
    """What-if scenario modification parameters."""

    type: Literal["portion", "sequencing", "walk", "fat", "preset", "meal_time"]
    amount_pct: Optional[float] = None
    delta_g: Optional[float] = None
    minutes: Optional[int] = None
    preset_id: Optional[str] = None
    shift_min: Optional[int] = None


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
