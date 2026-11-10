"""Split-conformal prediction intervals for multi-horizon glucose forecasting."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import numpy as np
import torch

from aegis.degradation.scenarios import ALL_SCENARIOS, DegradationScenario

HORIZON_STEPS = 36
PHYSIOLOGICAL_MIN_GLUCOSE = 40.0
PHYSIOLOGICAL_MAX_GLUCOSE = 400.0


@dataclass
class ConformalCalibrationTable:
    """Stores horizon-wise conformal quantile offsets per scenario and coverage level."""

    alpha_levels: List[float]  # e.g. [0.10, 0.20] for 90% and 80%
    n_calibration_samples: int
    scenarios: Dict[
        str, Dict[str, List[float]]
    ]  # scenario_id -> {"80%": [q1..q36], "90%": [q1..q36]}
    inflation_multipliers: Dict[str, float]  # scenario_id -> inflation factor if test coverage dips

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConformalCalibrationTable:
        return cls(
            alpha_levels=data.get("alpha_levels", [0.10, 0.20]),
            n_calibration_samples=data.get("n_calibration_samples", 0),
            scenarios=data.get("scenarios", {}),
            inflation_multipliers=data.get("inflation_multipliers", {}),
        )

    def save(self, filepath: Union[str, Path]) -> None:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> ConformalCalibrationTable:
        path = Path(filepath)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def get_quantiles(
        self,
        scenario: Union[DegradationScenario, str] = "D0",
        confidence_level: float = 0.90,
    ) -> np.ndarray:
        """Retrieves 36-step quantile half-widths for a given scenario and confidence level."""
        sc_key = scenario.value if isinstance(scenario, DegradationScenario) else str(scenario)
        if sc_key not in self.scenarios:
            sc_key = "D0"

        level_key = "90%" if confidence_level >= 0.85 else "80%"
        raw_q = self.scenarios.get(sc_key, {}).get(level_key)
        if raw_q is None:
            # Fallback to D0
            raw_q = self.scenarios.get("D0", {}).get(level_key, [15.0] * HORIZON_STEPS)

        multiplier = self.inflation_multipliers.get(sc_key, 1.0)
        return np.array(raw_q, dtype=np.float32) * multiplier


def fit_conformal_quantiles(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    alpha: float = 0.10,
) -> np.ndarray:
    """Computes finite-sample calibrated conformal quantile offsets for each horizon step.

    Args:
        y_true: [N, 36] true trajectories in mg/dL.
        y_pred: [N, 36] predicted trajectories in mg/dL.
        alpha: Error rate (e.g. 0.10 for 90% confidence).

    Returns:
        [36] array of quantile half-widths.
    """
    n = len(y_true)
    if n == 0:
        return np.full(HORIZON_STEPS, 20.0, dtype=np.float32)

    abs_residuals = np.abs(y_true - y_pred)  # [N, 36]

    # Finite sample correction: ceil((n + 1) * (1 - alpha)) / n
    target_p = min(1.0, np.ceil((n + 1) * (1.0 - alpha)) / float(n))

    quantiles = np.zeros(HORIZON_STEPS, dtype=np.float32)
    for t in range(HORIZON_STEPS):
        quantiles[t] = float(np.quantile(abs_residuals[:, t], target_p, method="higher"))

    # Ensure monotonic non-decreasing uncertainty envelope over time
    for t in range(1, HORIZON_STEPS):
        quantiles[t] = max(quantiles[t], quantiles[t - 1])

    return quantiles


def compute_conformal_intervals(
    y_pred: Union[np.ndarray, torch.Tensor],
    quantiles: np.ndarray,
    clamp_physiological: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generates lower and upper prediction intervals around point predictions.

    Args:
        y_pred: [..., 36] point predictions.
        quantiles: [36] half-widths.
        clamp_physiological: whether to clamp to [40, 400] mg/dL.

    Returns:
        (lower_bounds, upper_bounds) of identical shape to y_pred.
    """
    if isinstance(y_pred, torch.Tensor):
        pred_np = y_pred.detach().cpu().numpy()
    else:
        pred_np = np.asarray(y_pred)

    lower = pred_np - quantiles
    upper = pred_np + quantiles

    if clamp_physiological:
        lower = np.clip(lower, PHYSIOLOGICAL_MIN_GLUCOSE, PHYSIOLOGICAL_MAX_GLUCOSE)
        upper = np.clip(upper, PHYSIOLOGICAL_MIN_GLUCOSE, PHYSIOLOGICAL_MAX_GLUCOSE)

    return lower, upper


def compute_interval_conformal_bounds(
    y_pred: Union[np.ndarray, torch.Tensor],
    traj_kinetic: Union[np.ndarray, torch.Tensor],
    quantiles: np.ndarray,
    delta_portion: float = 0.0,
    clamp_physiological: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Computes standard and robust split-conformal bounds under carbohydrate portion uncertainty.

    Given portion uncertainty fraction delta in [0.0, 0.50], constructs the kinetic portion envelope:
        DeltaTraj_portion(t) = delta * |Traj_kinetic(t)|
        Y_low(t) = Y_point(t) - DeltaTraj_portion(t)
        Y_high(t) = Y_point(t) + DeltaTraj_portion(t)
        L_robust(t) = Y_low(t) - q_model(t)
        U_robust(t) = Y_high(t) + q_model(t)

    Args:
        y_pred: [..., 36] point predictions in absolute mg/dL.
        traj_kinetic: [..., 36] physiological kinetic component excursion in mg/dL.
        quantiles: [36] conformal quantile half-widths.
        delta_portion: relative portion uncertainty fraction delta in [0.0, 0.50].
        clamp_physiological: whether to clamp output bounds to [40.0, 400.0] mg/dL.

    Returns:
        (lower_standard, upper_standard, lower_robust, upper_robust)
    """
    if isinstance(y_pred, torch.Tensor):
        pred_np = y_pred.detach().cpu().numpy()
    else:
        pred_np = np.asarray(y_pred, dtype=np.float32)

    if isinstance(traj_kinetic, torch.Tensor):
        kinetic_np = traj_kinetic.detach().cpu().numpy()
    else:
        kinetic_np = np.asarray(traj_kinetic, dtype=np.float32)

    # Standard conformal intervals
    lower_std = pred_np - quantiles
    upper_std = pred_np + quantiles

    # Portion uncertainty envelope
    delta = float(np.clip(delta_portion, 0.0, 0.50))
    delta_traj = delta * np.abs(kinetic_np)

    y_low = pred_np - delta_traj
    y_high = pred_np + delta_traj

    lower_robust = y_low - quantiles
    upper_robust = y_high + quantiles

    if clamp_physiological:
        lower_std = np.clip(lower_std, PHYSIOLOGICAL_MIN_GLUCOSE, PHYSIOLOGICAL_MAX_GLUCOSE)
        upper_std = np.clip(upper_std, PHYSIOLOGICAL_MIN_GLUCOSE, PHYSIOLOGICAL_MAX_GLUCOSE)
        lower_robust = np.clip(lower_robust, PHYSIOLOGICAL_MIN_GLUCOSE, PHYSIOLOGICAL_MAX_GLUCOSE)
        upper_robust = np.clip(upper_robust, PHYSIOLOGICAL_MIN_GLUCOSE, PHYSIOLOGICAL_MAX_GLUCOSE)

    return lower_std, upper_std, lower_robust, upper_robust


def evaluate_conformal_coverage(
    y_true: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> Dict[str, float]:
    """Evaluates empirical coverage fraction and average interval width."""
    in_interval = (y_true >= lower) & (y_true <= upper)
    empirical_coverage = float(np.mean(in_interval))
    mean_width = float(np.mean(upper - lower))

    # Horizon-specific coverage
    coverage_120 = float(np.mean(in_interval[:, :24]))
    coverage_180 = (
        float(np.mean(in_interval[:, 24:])) if y_true.shape[1] > 24 else empirical_coverage
    )

    return {
        "empirical_coverage": empirical_coverage,
        "mean_width": mean_width,
        "coverage_0_120m": coverage_120,
        "coverage_120_180m": coverage_180,
    }


def calibrate_table_from_cross_validation(
    cv_residuals: Dict[str, Dict[str, Tuple[np.ndarray, np.ndarray]]],
    target_coverage: float = 0.90,
) -> ConformalCalibrationTable:
    """Builds a ConformalCalibrationTable across all degradation scenarios.

    Args:
        cv_residuals: dictionary mapping scenario -> {"y_true": ..., "y_pred": ...}
    """
    table = ConformalCalibrationTable(
        alpha_levels=[0.10, 0.20],
        n_calibration_samples=0,
        scenarios={},
        inflation_multipliers={},
    )

    base_sc = DegradationScenario.D0_NONE.value
    base_data = cv_residuals.get(base_sc)
    if base_data is not None:
        y_true, y_pred = base_data["y_true"], base_data["y_pred"]
        table.n_calibration_samples = len(y_true)
        q_90 = fit_conformal_quantiles(y_true, y_pred, alpha=0.10)
        q_80 = fit_conformal_quantiles(y_true, y_pred, alpha=0.20)
    else:
        # Default fallback
        q_90 = np.linspace(10.0, 30.0, HORIZON_STEPS, dtype=np.float32)
        q_80 = np.linspace(8.0, 24.0, HORIZON_STEPS, dtype=np.float32)

    table.scenarios[base_sc] = {
        "90%": [round(float(v), 2) for v in q_90],
        "80%": [round(float(v), 2) for v in q_80],
    }

    # Derive scenario-specific quantiles
    multiplier_map = {
        DegradationScenario.D0_NONE.value: 1.0,
        DegradationScenario.D1_15M.value: 1.15,
        DegradationScenario.D1_30M.value: 1.35,
        DegradationScenario.D1_60M.value: 1.70,
        DegradationScenario.D2_20.value: 1.10,
        DegradationScenario.D2_50.value: 1.30,
        DegradationScenario.D3.value: 1.20,
        DegradationScenario.D4.value: 2.10,  # reduced-sensor mode has much wider intervals
        DegradationScenario.D5.value: 1.25,
        DegradationScenario.D6.value: 1.45,
        DegradationScenario.D7.value: 1.80,
    }

    for sc in ALL_SCENARIOS:
        sc_val = sc.value
        if sc_val in cv_residuals:
            y_t = cv_residuals[sc_val]["y_true"]
            y_p = cv_residuals[sc_val]["y_pred"]
            sc_q_90 = fit_conformal_quantiles(y_t, y_p, alpha=0.10)
            sc_q_80 = fit_conformal_quantiles(y_t, y_p, alpha=0.20)
        else:
            m = multiplier_map.get(sc_val, 1.2)
            sc_q_90 = q_90 * m
            sc_q_80 = q_80 * m

        table.scenarios[sc_val] = {
            "90%": [round(float(v), 2) for v in sc_q_90],
            "80%": [round(float(v), 2) for v in sc_q_80],
        }
        table.inflation_multipliers[sc_val] = 1.0

    return table
