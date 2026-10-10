"""Unit tests for frozen API contracts and scenario models."""

import pytest
from pydantic import ValidationError

from services.common.contracts import (
    CLINICAL_DISCLAIMER,
    ForecastMetrics,
    IntervalBand,
    MealInput,
    ModelMetadata,
    PersonalisationStatus,
    PredictRequest,
    PredictResponse,
    ReliabilityAssessment,
    ScenarioDifference,
    ScenarioResult,
    SimulateResponse,
)


def test_predict_request_validation():
    req = PredictRequest(
        patient_id="P001",
        t0="2026-10-09T12:00:00Z",
        meal=MealInput(carbs_g=50.0, protein_g=20.0, fat_g=15.0, meal_type="lunch"),
    )
    assert req.patient_id == "P001"
    assert req.meal.carbs_g == 50.0
    assert req.degradation == "D0"


def test_predict_request_negative_carbs_fails():
    with pytest.raises(ValidationError):
        MealInput(carbs_g=-10.0)


def test_predict_response_structure():
    resp = PredictResponse(
        delta_glucose=[0.0] * 36,
        glucose=[120.0] * 36,
        interval=IntervalBand(level=0.9, lower=[100.0] * 36, upper=[140.0] * 36),
        metrics=ForecastMetrics(peak=140.0, time_to_peak_min=60, delayed_mean_120_180=115.0),
        reliability=ReliabilityAssessment(label="high", reasons=[]),
        personalisation=PersonalisationStatus(n_personal_meals=5),
        model=ModelMetadata(version="v1.0", dataset_version="d1", feature_version="f1"),
    )
    assert len(resp.horizon_min) == 36
    assert resp.disclaimer == CLINICAL_DISCLAIMER


def test_simulate_response_origin_labels():
    baseline = PredictResponse(
        delta_glucose=[0.0] * 36,
        glucose=[120.0] * 36,
        interval=IntervalBand(level=0.9, lower=[100.0] * 36, upper=[140.0] * 36),
        metrics=ForecastMetrics(peak=140.0, time_to_peak_min=60, delayed_mean_120_180=115.0),
        reliability=ReliabilityAssessment(label="high", reasons=[]),
        personalisation=PersonalisationStatus(n_personal_meals=5),
        model=ModelMetadata(version="v1.0", dataset_version="d1", feature_version="f1"),
    )
    scenario = ScenarioResult(
        type="walk",
        origin="assumption_driven",
        trajectory=[110.0] * 36,
        interval=IntervalBand(level=0.9, lower=[95.0] * 36, upper=[130.0] * 36),
        metrics=ForecastMetrics(peak=125.0, time_to_peak_min=60, delayed_mean_120_180=105.0),
        delta_vs_baseline=ScenarioDifference(
            delta_peak=-15.0, delta_time_to_peak=0, delta_delayed_mean=-10.0
        ),
        reliability=ReliabilityAssessment(label="high", reasons=[]),
        assumption={"citation": "Buffey et al., 2022"},
    )
    sim_resp = SimulateResponse(baseline=baseline, scenarios=[scenario])
    assert sim_resp.scenarios[0].origin == "assumption_driven"
