"""Unit tests for pharmacological insulin kinetics and sensitivity estimators."""

import numpy as np
import pytest

from aegis.models.pharmacology import (
    RapidActingInsulinKinetics,
    compute_insulin_effect,
    estimate_cir,
    estimate_homa_ir,
    estimate_isf,
    estimate_tdd,
)


def test_clinical_estimators_1800_rule():
    # 70 kg reference adult
    w = 70.0
    tdd = estimate_tdd(w)
    assert pytest.approx(tdd, rel=1e-3) == 38.5

    isf = estimate_isf(w)
    assert pytest.approx(isf, rel=1e-3) == 1800.0 / 38.5  # ~46.75 mg/dL/U

    cir = estimate_cir(w)
    assert pytest.approx(cir, rel=1e-3) == 500.0 / 38.5  # ~12.98 g/U

    # Custom rule constant
    isf_1500 = estimate_isf(w, rule=1500.0)
    assert pytest.approx(isf_1500, rel=1e-3) == 1500.0 / 38.5

    # Boundary & error cases
    with pytest.raises(ValueError):
        estimate_tdd(0.0)

    with pytest.raises(ValueError):
        estimate_tdd(-10.0)

    with pytest.raises(ValueError):
        estimate_tdd(float("nan"))


def test_homa_ir_estimator():
    # Normal reference
    homa = estimate_homa_ir(90.0, 5.0)
    assert pytest.approx(homa, rel=1e-2) == 1.11

    # Elevated insulin resistance
    homa_res = estimate_homa_ir(140.0, 25.0)
    assert pytest.approx(homa_res, rel=1e-2) == 8.64

    # None / negative / nan cases
    assert estimate_homa_ir(None, 10.0) is None
    assert estimate_homa_ir(100.0, None) is None
    assert estimate_homa_ir(0.0, 10.0) is None
    assert estimate_homa_ir(-50.0, 10.0) is None
    assert estimate_homa_ir(float("nan"), 10.0) is None
    assert estimate_homa_ir(100.0, float("nan")) is None


def test_rapid_acting_kinetics_cdf():
    kinetics = RapidActingInsulinKinetics(tau_peak=55.0, dia=300.0)

    # At meal onset (t = t_bolus = 0)
    f_0 = kinetics.cumulative_absorption_fraction(0.0, t_bolus_min=0.0)
    assert f_0 == 0.0

    # Before bolus time
    f_pre = kinetics.cumulative_absorption_fraction(-10.0, t_bolus_min=0.0)
    assert f_pre == 0.0

    # At peak time tau_peak = 55.0
    # Formula: 1 - (1 + 1)*exp(-1) = 1 - 2/e ~ 0.2642
    f_peak = kinetics.cumulative_absorption_fraction(55.0, t_bolus_min=0.0)
    assert pytest.approx(f_peak, rel=1e-3) == 1.0 - 2.0 / np.e

    # Beyond DIA (300 min)
    f_dia = kinetics.cumulative_absorption_fraction(300.0, t_bolus_min=0.0)
    assert f_dia == 1.0
    f_post = kinetics.cumulative_absorption_fraction(400.0, t_bolus_min=0.0)
    assert f_post == 1.0

    # Monotonicity test
    t_steps = np.linspace(0.0, 300.0, 61)
    fractions = [kinetics.cumulative_absorption_fraction(t, 0.0) for t in t_steps]
    for i in range(len(fractions) - 1):
        assert fractions[i + 1] >= fractions[i]


def test_iob_calculation():
    kinetics = RapidActingInsulinKinetics(tau_peak=55.0, dia=300.0)
    bolus = 5.0

    # At injection time
    iob_0 = kinetics.iob(0.0, bolus_units=bolus, t_bolus_min=0.0)
    assert pytest.approx(iob_0, rel=1e-4) == 5.0

    # As absorption progresses, IOB decreases
    iob_60 = kinetics.iob(60.0, bolus_units=bolus, t_bolus_min=0.0)
    assert 0.0 < iob_60 < 5.0

    # At or past DIA, IOB reaches 0.0
    iob_dia = kinetics.iob(300.0, bolus_units=bolus, t_bolus_min=0.0)
    assert iob_dia == 0.0

    # Zero or negative bolus
    assert kinetics.iob(30.0, bolus_units=0.0) == 0.0


def test_bolus_deflection_pre_and_post_timing():
    kinetics = RapidActingInsulinKinetics(tau_peak=55.0, dia=300.0)
    horizon = [5 * k for k in range(1, 37)]  # 5 to 180 min
    bolus = 6.0
    isf = 40.0

    # Case 1: Bolus at meal (t = 0)
    deflection_0 = kinetics.calculate_bolus_deflection(
        horizon, bolus_units=bolus, isf=isf, t_bolus_min=0.0
    )
    assert len(deflection_0) == 36
    # Glucose deflection must be monotonically non-positive
    assert np.all(deflection_0 <= 0.0)
    assert deflection_0[-1] < deflection_0[0]

    # Case 2: Pre-bolus 15 minutes before meal (t_bolus = -15)
    deflection_pre = kinetics.calculate_bolus_deflection(
        horizon, bolus_units=bolus, isf=isf, t_bolus_min=-15.0
    )
    # At earlier points, pre-bolus has higher cumulative drop than at-meal bolus
    assert abs(deflection_pre[0]) > abs(deflection_0[0])

    # Case 3: Delayed bolus 30 minutes after meal (t_bolus = +30)
    deflection_post = kinetics.calculate_bolus_deflection(
        horizon, bolus_units=bolus, isf=isf, t_bolus_min=30.0
    )
    # At t <= 30 min (steps 1 to 6), deflection should be 0.0
    for i in range(6):
        assert deflection_post[i] == 0.0
    # After t = 30 min, deflection becomes negative
    assert deflection_post[7] < 0.0


def test_basal_differential_drift():
    kinetics = RapidActingInsulinKinetics()
    horizon = [60.0, 120.0, 180.0]
    isf = 50.0

    # Case 1: Temporary basal increase (+0.5 U/hr)
    drift_inc = kinetics.calculate_basal_deflection(horizon, basal_rate_diff_u_hr=0.5, isf=isf)
    # -50 * 0.5 * (60/60) = -25 mg/dL
    assert pytest.approx(drift_inc[0], rel=1e-3) == -25.0
    assert pytest.approx(drift_inc[1], rel=1e-3) == -50.0
    assert pytest.approx(drift_inc[2], rel=1e-3) == -75.0

    # Case 2: Temporary basal decrease / suspension (-0.5 U/hr)
    drift_dec = kinetics.calculate_basal_deflection(horizon, basal_rate_diff_u_hr=-0.5, isf=isf)
    # Glucose rises relative to baseline
    assert pytest.approx(drift_dec[0], rel=1e-3) == 25.0
    assert pytest.approx(drift_dec[1], rel=1e-3) == 50.0

    # Case 3: Zero diff
    drift_zero = kinetics.calculate_basal_deflection(horizon, basal_rate_diff_u_hr=0.0, isf=isf)
    assert np.all(drift_zero == 0.0)


def test_compute_insulin_effect_convenience():
    horizon = [(i + 1) * 5 for i in range(36)]
    res = compute_insulin_effect(
        horizon_min=horizon,
        bolus_units=4.0,
        bolus_time_min=-15.0,
        basal_rate_diff_u_hr=0.2,
        isf=45.0,
        insulin_type="rapid_acting",
    )

    assert "net_deflection" in res
    assert "bolus_deflection" in res
    assert "basal_deflection" in res
    assert "iob_trajectory" in res
    assert "residual_iob_at_t0" in res

    assert len(res["net_deflection"]) == 36
    assert len(res["iob_trajectory"]) == 36
    assert res["residual_iob_at_t0"] > 0.0  # Injected 15m ago, so residual IOB > 0
    assert np.all(res["net_deflection"] < 0.0)  # Both bolus and +basal lower glucose


def test_different_insulin_types():
    horizon = [(i + 1) * 5 for i in range(36)]

    # Ultra-rapid (Fiasp) vs Rapid-acting vs Regular
    res_ultra = compute_insulin_effect(
        horizon, bolus_units=5.0, insulin_type="ultra_rapid", isf=40.0
    )
    res_rapid = compute_insulin_effect(
        horizon, bolus_units=5.0, insulin_type="rapid_acting", isf=40.0
    )
    res_reg = compute_insulin_effect(horizon, bolus_units=5.0, insulin_type="regular", isf=40.0)

    # At early horizon (e.g. 30 min), ultra-rapid drops glucose faster than regular
    assert abs(res_ultra["net_deflection"][5]) > abs(res_rapid["net_deflection"][5])
    assert abs(res_rapid["net_deflection"][5]) > abs(res_reg["net_deflection"][5])
