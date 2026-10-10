"""Unit tests for multi-horizon trajectory metrics and bootstrap confidence intervals."""

from aegis.evaluation.metrics import (
    compute_patient_bootstrap_ci,
    compute_trajectory_metrics,
)


def test_compute_trajectory_metrics_perfect():
    # Exactly matching curves
    true_delta = [float(k) for k in range(36)]
    pred_delta = [float(k) for k in range(36)]
    mask = [1.0] * 36

    m = compute_trajectory_metrics(pred_delta, true_delta, mask)
    assert m["mae_0_120"] == 0.0
    assert m["rmse_0_120"] == 0.0
    assert m["mae_120_180"] == 0.0
    assert m["rmse_120_180"] == 0.0
    assert m["mae_0_180"] == 0.0
    assert m["peak_error"] == 0.0
    assert m["time_to_peak_error"] == 0.0
    assert m["iauc_error"] == 0.0


def test_compute_trajectory_metrics_constant_offset():
    true_delta = [20.0] * 36
    pred_delta = [30.0] * 36  # offset by +10.0 mg/dL everywhere

    m = compute_trajectory_metrics(pred_delta, true_delta)
    assert m["mae_0_120"] == 10.0
    assert m["rmse_0_120"] == 10.0
    assert m["mae_120_180"] == 10.0
    assert m["mae_0_180"] == 10.0
    assert m["peak_error"] == 10.0


def test_compute_patient_bootstrap_ci():
    # 5 patients with known error distributions
    patient_errors = {
        "P1": [10.0, 12.0],
        "P2": [15.0, 14.0],
        "P3": [8.0, 9.0],
        "P4": [20.0, 22.0],
        "P5": [11.0, 13.0],
    }

    mean_val, ci_low, ci_high = compute_patient_bootstrap_ci(
        patient_errors, n_bootstraps=500, seed=42
    )
    assert ci_low <= mean_val <= ci_high
    assert 8.0 < mean_val < 20.0
