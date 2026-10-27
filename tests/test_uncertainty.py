"""Unit tests for conformal prediction and clinical reliability."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from aegis.degradation.scenarios import DegradationScenario
from aegis.uncertainty.conformal import (
    ConformalCalibrationTable,
    compute_conformal_intervals,
    compute_interval_conformal_bounds,
    evaluate_conformal_coverage,
    fit_conformal_quantiles,
)
from aegis.uncertainty.reliability import (
    ReliabilityLevel,
    assess_reliability,
)


def test_fit_conformal_quantiles_monotonic():
    np.random.seed(42)
    n = 50
    y_true = np.random.normal(130, 20, size=(n, 36))
    y_pred = y_true + np.random.normal(0, 5, size=(n, 36))

    q_90 = fit_conformal_quantiles(y_true, y_pred, alpha=0.10)
    assert len(q_90) == 36
    # Must be non-decreasing
    assert np.all(np.diff(q_90) >= 0)
    # Check positive values
    assert np.all(q_90 > 0)


def test_compute_conformal_intervals_and_clamping():
    y_pred = np.array([[50.0, 120.0, 390.0]])
    quantiles = np.array([20.0, 15.0, 25.0])

    lower, upper = compute_conformal_intervals(y_pred, quantiles, clamp_physiological=True)
    # 50 - 20 = 30 -> clamped to 40.0
    assert lower[0, 0] == 40.0
    assert upper[0, 0] == 70.0

    # 120 - 15 = 105, 120 + 15 = 135
    assert lower[0, 1] == 105.0
    assert upper[0, 1] == 135.0

    # 390 + 25 = 415 -> clamped to 400.0
    assert lower[0, 2] == 365.0
    assert upper[0, 2] == 400.0


def test_evaluate_conformal_coverage():
    y_true = np.ones((10, 36)) * 100.0
    lower = np.ones((10, 36)) * 90.0
    upper = np.ones((10, 36)) * 110.0

    res = evaluate_conformal_coverage(y_true, lower, upper)
    assert res["empirical_coverage"] == 1.0
    assert res["mean_width"] == 20.0


def test_conformal_table_save_load_roundtrip():
    table = ConformalCalibrationTable(
        alpha_levels=[0.10, 0.20],
        n_calibration_samples=40,
        scenarios={
            "D0": {"90%": [12.5] * 36, "80%": [9.5] * 36},
            "D4": {"90%": [28.0] * 36, "80%": [22.0] * 36},
        },
        inflation_multipliers={"D0": 1.0, "D4": 1.1},
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "uncertainty_table.json"
        table.save(tmp_path)
        loaded = ConformalCalibrationTable.load(tmp_path)

        assert loaded.n_calibration_samples == 40
        assert "D0" in loaded.scenarios
        assert "D4" in loaded.scenarios

        q_d0 = loaded.get_quantiles("D0", confidence_level=0.90)
        assert len(q_d0) == 36
        assert q_d0[0] == 12.5

        q_d4 = loaded.get_quantiles("D4", confidence_level=0.90)
        assert q_d4[0] == pytest.approx(28.0 * 1.1)


def test_reliability_assessment_levels():
    # 1. High confidence
    high_res = assess_reliability(
        scenario=DegradationScenario.D0_NONE,
        mean_interval_width=22.0,
        k_personal_meals=5,
        support_score=0.9,
    )
    assert high_res.level == ReliabilityLevel.HIGH
    assert high_res.is_safe_for_decision is True

    # 2. Moderate confidence (short dropout or missing wearables)
    mod_res = assess_reliability(
        scenario=DegradationScenario.D1_15M,
        mean_interval_width=35.0,
        anchor_age_min=15.0,
        k_personal_meals=4,
    )
    assert mod_res.level == ReliabilityLevel.MODERATE
    assert mod_res.is_safe_for_decision is True

    # 3. Low confidence (D4 reduced sensor)
    low_res_d4 = assess_reliability(
        scenario=DegradationScenario.D4,
        mean_interval_width=52.0,
        k_personal_meals=0,
    )
    assert low_res_d4.level == ReliabilityLevel.LOW
    assert low_res_d4.is_safe_for_decision is False
    assert "not suitable for treatment decisions" in low_res_d4.clinician_message

    # 4. Low confidence (D7 out of support)
    low_res_d7 = assess_reliability(
        scenario=DegradationScenario.D7,
        mean_interval_width=40.0,
        support_score=0.1,
    )
    assert low_res_d7.level == ReliabilityLevel.LOW
    assert low_res_d7.is_safe_for_decision is False


def test_interval_conformal_bounds_properties():
    # 36-step trajectory, kinetic excursion peaking at 40 mg/dL
    t = np.arange(1, 37) * 5.0
    y_pred = 110.0 + 40.0 * (t / 45.0) * np.exp(1.0 - t / 45.0)
    traj_kinetic = 35.0 * (t / 45.0) * np.exp(1.0 - t / 45.0)
    quantiles = np.linspace(10.0, 25.0, 36)

    # 1. Delta = 0.0 should exactly reproduce standard conformal bounds
    l_std, u_std, l_rob0, u_rob0 = compute_interval_conformal_bounds(
        y_pred, traj_kinetic, quantiles, delta_portion=0.0
    )
    np.testing.assert_allclose(l_rob0, l_std)
    np.testing.assert_allclose(u_rob0, u_std)

    # 2. Delta > 0 should widen bounds strictly around kinetic excursion
    _, _, l_rob20, u_rob20 = compute_interval_conformal_bounds(
        y_pred, traj_kinetic, quantiles, delta_portion=0.20
    )
    assert np.all(l_rob20 <= l_std)
    assert np.all(u_rob20 >= u_std)
    # At peak kinetic excursion, robust envelope should be wider by 2 * delta * kinetic
    peak_idx = int(np.argmax(traj_kinetic))
    expected_diff = 0.20 * traj_kinetic[peak_idx]
    assert np.isclose(u_rob20[peak_idx] - u_std[peak_idx], expected_diff, atol=1e-4)
    assert np.isclose(l_std[peak_idx] - l_rob20[peak_idx], expected_diff, atol=1e-4)

    # 3. Monotonic expansion with delta
    _, _, l_rob40, u_rob40 = compute_interval_conformal_bounds(
        y_pred, traj_kinetic, quantiles, delta_portion=0.40
    )
    assert np.all(l_rob40 <= l_rob20)
    assert np.all(u_rob40 >= u_rob20)

    # 4. Physiological clamping [40, 400]
    extreme_pred = np.array([45.0, 395.0])
    extreme_kinetic = np.array([30.0, 30.0])
    extreme_q = np.array([20.0, 20.0])
    _, _, l_ext, u_ext = compute_interval_conformal_bounds(
        extreme_pred, extreme_kinetic, extreme_q, delta_portion=0.30, clamp_physiological=True
    )
    assert l_ext[0] >= 40.0
    assert u_ext[1] <= 400.0


def test_interval_conformal_coverage_under_portion_shift():
    np.random.seed(42)
    n = 200
    t = np.arange(1, 37) * 5.0
    kinetic_shape = (t / 45.0) * np.exp(1.0 - t / 45.0)

    # Unperturbed baseline predictions and residuals
    y_pred = 110.0 + np.outer(np.ones(n), kinetic_shape * 40.0)
    residuals = np.random.normal(0, 4.0, size=(n, 36))
    quantiles = fit_conformal_quantiles(y_pred + residuals, y_pred, alpha=0.10)

    # True portion size varies by up to +/- 20%
    delta_portion = 0.20
    portion_errors = np.random.uniform(-delta_portion, delta_portion, size=(n, 1))
    y_true_perturbed = y_pred + (portion_errors * kinetic_shape * 40.0) + residuals

    # Standard bounds without portion uncertainty
    l_std, u_std = compute_conformal_intervals(y_pred, quantiles)
    cov_std = evaluate_conformal_coverage(y_true_perturbed, l_std, u_std)

    # Robust interval conformal bounds
    traj_kinetic = np.outer(np.ones(n), kinetic_shape * 40.0)
    _, _, l_rob, u_rob = compute_interval_conformal_bounds(
        y_pred, traj_kinetic, quantiles, delta_portion=delta_portion
    )
    cov_rob = evaluate_conformal_coverage(y_true_perturbed, l_rob, u_rob)

    # Robust bounds must achieve higher empirical coverage under portion shifts (>= 90%)
    assert cov_rob["empirical_coverage"] >= 0.90
    assert cov_rob["empirical_coverage"] >= cov_std["empirical_coverage"]
