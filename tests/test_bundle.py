"""Unit tests for offline artifact bundle loading and end-to-end inference."""

import numpy as np
import pytest

from aegis.degradation.scenarios import DegradationScenario
from aegis.training.export import load_aegis_bundle


@pytest.fixture
def loaded_bundle():
    return load_aegis_bundle("artifacts/bundle")


def test_bundle_structure_and_metadata(loaded_bundle):
    assert loaded_bundle.model is not None
    assert loaded_bundle.basis is not None
    assert loaded_bundle.calibration_table is not None
    assert len(loaded_bundle.reference_static_profiles) > 0
    assert loaded_bundle.metadata["model_architecture"] == "StructuredMealForecasterS"
    assert loaded_bundle.metadata["output_horizon_steps"] == 36


def test_bundle_predict_d0_nominal(loaded_bundle):
    seq = np.zeros((12, 6), dtype=np.float32)
    seq[:, 1] = 1.0  # observed
    anchor = np.array([0.2, 0.0, 0.0, 0.0], dtype=np.float32)
    meal = np.zeros(16, dtype=np.float32)
    static = np.zeros(8, dtype=np.float32)

    res = loaded_bundle.predict(
        seq=seq,
        anchor=anchor,
        meal=meal,
        static=static,
        g_t0=115.0,
        patient_id="P_TEST",
        earlier_residuals=[np.zeros(36, dtype=np.float32) for _ in range(4)],
        scenario=DegradationScenario.D0_NONE,
        confidence_level=0.90,
    )

    assert len(res["forecast"]) == 36
    assert len(res["interval_lower"]) == 36
    assert len(res["interval_upper"]) == 36
    assert res["reliability"]["level"] == "HIGH"
    assert res["reliability"]["is_safe_for_decision"] is True
    assert res["metadata"]["is_degraded"] is False

    # Check bounds order
    for t in range(36):
        assert res["interval_lower"][t] <= res["forecast"][t] + 1e-3
        assert res["interval_upper"][t] >= res["forecast"][t] - 1e-3


def test_bundle_predict_d4_reduced_sensor(loaded_bundle):
    seq = np.zeros((12, 6), dtype=np.float32)
    anchor = np.zeros(4, dtype=np.float32)
    meal = np.zeros(16, dtype=np.float32)
    static = np.zeros(8, dtype=np.float32)

    res = loaded_bundle.predict(
        seq=seq,
        anchor=anchor,
        meal=meal,
        static=static,
        g_t0=115.0,
        patient_id="P_TEST",
        scenario=DegradationScenario.D4,
        confidence_level=0.90,
    )

    assert res["reliability"]["level"] == "LOW"
    assert res["reliability"]["is_safe_for_decision"] is False
    assert "not suitable for treatment decisions" in res["reliability"]["clinician_message"]
    assert res["metadata"]["is_degraded"] is True


def test_bundle_predict_d7_out_of_support(loaded_bundle):
    seq = np.zeros((12, 6), dtype=np.float32)
    seq[:, 1] = 1.0
    anchor = np.zeros(4, dtype=np.float32)
    meal = np.zeros(16, dtype=np.float32)
    static = np.zeros(8, dtype=np.float32)

    res = loaded_bundle.predict(
        seq=seq,
        anchor=anchor,
        meal=meal,
        static=static,
        g_t0=130.0,
        patient_id="P_TEST",
        scenario=DegradationScenario.D7,
    )

    assert res["reliability"]["level"] == "LOW"
    assert res["metadata"]["is_degraded"] is True
    assert all(40.0 <= v <= 400.0 for v in res["forecast"])
