"""Evaluation harness for post-meal glucose trajectory forecasting."""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def compute_trajectory_metrics(
    pred_delta: np.ndarray | List[float],
    true_delta: np.ndarray | List[float],
    mask: np.ndarray | List[float] | None = None,
) -> Dict[str, float]:
    """Compute MAE and RMSE across primary (0-120), delayed (120-180), and full (0-180) windows.

    Indices:
    - 0..23 corresponds to 5..120 min (primary window, 24 steps)
    - 24..35 corresponds to 125..180 min (delayed window, 12 steps)
    - 0..35 corresponds to 5..180 min (full window, 36 steps)
    """
    pred = np.array(pred_delta, dtype=np.float32)
    true = np.array(true_delta, dtype=np.float32)

    if mask is None:
        m = np.ones_like(true, dtype=np.float32)
    else:
        m = np.array(mask, dtype=np.float32)

    err = np.abs(pred - true)
    sq_err = (pred - true) ** 2

    # Helper for masked mean
    def _masked_mean(values: np.ndarray, weights: np.ndarray) -> float:
        w_sum = np.sum(weights)
        if w_sum == 0:
            return 0.0
        return float(np.sum(values * weights) / w_sum)

    # 1. Primary window (0-120 min, steps 0..23)
    mae_120 = _masked_mean(err[:24], m[:24])
    rmse_120 = float(np.sqrt(_masked_mean(sq_err[:24], m[:24])))

    # 2. Delayed window (120-180 min, steps 24..35)
    mae_delayed = _masked_mean(err[24:36], m[24:36])
    rmse_delayed = float(np.sqrt(_masked_mean(sq_err[24:36], m[24:36])))

    # 3. Full window (0-180 min, steps 0..35)
    mae_180 = _masked_mean(err[:36], m[:36])
    rmse_180 = float(np.sqrt(_masked_mean(sq_err[:36], m[:36])))

    # Peak and Time-to-Peak (TTP)
    valid_true = true[m > 0]
    valid_pred = pred[m > 0]

    if len(valid_true) > 0 and len(valid_pred) > 0:
        true_peak_idx = int(np.argmax(valid_true))
        pred_peak_idx = int(np.argmax(valid_pred))

        true_peak = float(valid_true[true_peak_idx])
        pred_peak = float(valid_pred[pred_peak_idx])
        peak_err = abs(pred_peak - true_peak)

        # Each step is 5 minutes
        true_ttp = (true_peak_idx + 1) * 5
        pred_ttp = (pred_peak_idx + 1) * 5
        ttp_err = abs(pred_ttp - true_ttp)
    else:
        true_peak, pred_peak, peak_err = 0.0, 0.0, 0.0
        true_ttp, pred_ttp, ttp_err = 0, 0, 0

    # Incremental AUC (positive area under curve above baseline G(t0))
    # Using trapezoidal rule at 5-minute grid
    pos_true = np.clip(true, 0.0, None) * m
    pos_pred = np.clip(pred, 0.0, None) * m
    trapz_fn = getattr(np, "trapezoid", getattr(np, "trapz", None))
    iauc_true = float(trapz_fn(pos_true, dx=5.0))
    iauc_pred = float(trapz_fn(pos_pred, dx=5.0))
    iauc_err = abs(iauc_pred - iauc_true)

    return {
        "mae_0_120": round(mae_120, 3),
        "rmse_0_120": round(rmse_120, 3),
        "mae_120_180": round(mae_delayed, 3),
        "rmse_120_180": round(rmse_delayed, 3),
        "mae_0_180": round(mae_180, 3),
        "rmse_0_180": round(rmse_180, 3),
        "peak_error": round(peak_err, 3),
        "time_to_peak_error": float(ttp_err),
        "iauc_error": round(iauc_err, 2),
        "true_peak": round(true_peak, 2),
        "pred_peak": round(pred_peak, 2),
    }


def compute_patient_bootstrap_ci(
    patient_metric_map: Dict[str, List[float]],
    n_bootstraps: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Compute 95% paired bootstrap confidence interval resampled at patient level.

    Args:
        patient_metric_map: Dictionary mapping patient_id -> list of sample metric errors.
        n_bootstraps: Number of bootstrap replications.
        alpha: Significance level (default 0.05 for 95% CI).
        seed: Random seed.

    Returns:
        Tuple of (mean_metric, lower_bound_2.5%, upper_bound_97.5%)
    """
    patient_ids = list(patient_metric_map.keys())
    if not patient_ids:
        return 0.0, 0.0, 0.0

    # Compute patient-level mean for each patient
    patient_means = np.array(
        [np.mean(patient_metric_map[pid]) for pid in patient_ids], dtype=np.float32
    )
    overall_mean = float(np.mean(patient_means))

    rng = np.random.default_rng(seed)
    n_patients = len(patient_ids)
    boot_means = np.zeros(n_bootstraps, dtype=np.float32)

    for b in range(n_bootstraps):
        # Resample patient IDs with replacement
        sample_indices = rng.choice(n_patients, size=n_patients, replace=True)
        boot_means[b] = np.mean(patient_means[sample_indices])

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - (alpha / 2.0))

    ci_lower = float(np.percentile(boot_means, lower_pct))
    ci_upper = float(np.percentile(boot_means, upper_pct))

    return round(overall_mean, 3), round(ci_lower, 3), round(ci_upper, 3)
