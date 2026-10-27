"""Pharmacological insulin kinetics and pharmacodynamics module (Decision Phase 2).

Implements analytical closed-form rapid-acting analog kinetics (Lispro/Aspart/Glulisine),
basal differential drift, active Insulin on Board (IOB) tracking, and 1800-Rule
clinical sensitivity estimators.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Union

import numpy as np

# Default pharmacological constants
DEFAULT_TAU_PEAK_MIN = 55.0  # Time to peak action in minutes (rapid-acting analog)
DEFAULT_DIA_MIN = 300.0  # Duration of Insulin Action in minutes (5 hours)

INSULIN_PROFILES: Dict[str, Dict[str, float]] = {
    "rapid_acting": {"tau_peak": 55.0, "dia": 300.0},  # Lispro, Aspart, Glulisine
    "ultra_rapid": {"tau_peak": 40.0, "dia": 270.0},  # Fiasp, Lyumjev
    "regular": {"tau_peak": 90.0, "dia": 360.0},  # Regular human insulin
}


def estimate_tdd(weight_kg: float) -> float:
    """Estimate Total Daily Dose (TDD) of insulin using clinical standard ~0.55 U/kg."""
    if weight_kg is None or math.isnan(weight_kg) or weight_kg <= 0:
        raise ValueError(f"weight_kg must be positive, got {weight_kg}")
    return 0.55 * weight_kg


def estimate_isf(weight_kg: float, rule: float = 1800.0) -> float:
    """Estimate Insulin Sensitivity Factor (ISF) via 1800-Rule (mg/dL per unit).

    Formula: ISF = 1800 / TDD = 1800 / (0.55 * weight_kg).
    """
    tdd = estimate_tdd(weight_kg)
    return rule / tdd


def estimate_cir(weight_kg: float, rule: float = 500.0) -> float:
    """Estimate Carbohydrate-to-Insulin Ratio (CIR) via 500-Rule (grams carb per unit).

    Formula: CIR = 500 / TDD = 500 / (0.55 * weight_kg).
    """
    tdd = estimate_tdd(weight_kg)
    return rule / tdd


def estimate_homa_ir(
    fasting_glucose_mg_dl: Optional[float],
    fasting_insulin_u_u_ml: Optional[float],
) -> Optional[float]:
    """Calculate Homeostatic Model Assessment of Insulin Resistance (HOMA-IR).

    Formula: HOMA-IR = (Fasting Glucose [mg/dL] * Fasting Insulin [uU/mL]) / 405.
    Normal range: < 1.0 (insulin sensitive), > 1.9 (early resistance), > 2.9 (significant resistance).
    """
    if fasting_glucose_mg_dl is None or fasting_insulin_u_u_ml is None:
        return None
    try:
        fg = float(fasting_glucose_mg_dl)
        fi = float(fasting_insulin_u_u_ml)
    except (ValueError, TypeError):
        return None
    if math.isnan(fg) or math.isnan(fi) or fg <= 0 or fi <= 0:
        return None
    return (fg * fi) / 405.0


class RapidActingInsulinKinetics:
    """Analytical closed-form rapid-acting analog kinetics.

    Uses the cumulative gamma distribution CDF (k=2 shape):
        F_abs(t) = 1 - (1 + (t - t_bolus)/tau_peak) * exp(-(t - t_bolus)/tau_peak)
    for t >= t_bolus, and 0 for t < t_bolus.
    """

    def __init__(
        self,
        tau_peak: float = DEFAULT_TAU_PEAK_MIN,
        dia: float = DEFAULT_DIA_MIN,
        insulin_type: str = "rapid_acting",
    ) -> None:
        params = INSULIN_PROFILES.get(insulin_type, {})
        self.tau_peak = params.get("tau_peak", tau_peak)
        self.dia = params.get("dia", dia)
        self.insulin_type = insulin_type

    def cumulative_absorption_fraction(self, t_min: float, t_bolus_min: float = 0.0) -> float:
        """Computes fraction F_abs(t) in [0.0, 1.0] of insulin absorbed up to time t_min."""
        delta_t = t_min - t_bolus_min
        if delta_t <= 0.0:
            return 0.0
        if delta_t >= self.dia:
            return 1.0

        # Cumulative gamma CDF (shape=2)
        x = delta_t / self.tau_peak
        f_abs = 1.0 - (1.0 + x) * math.exp(-x)
        return float(np.clip(f_abs, 0.0, 1.0))

    def iob(self, t_min: float, bolus_units: float, t_bolus_min: float = 0.0) -> float:
        """Active Insulin On Board (IOB) remaining at time t_min in units."""
        if bolus_units <= 0:
            return 0.0
        if t_min < t_bolus_min:
            # Bolus scheduled in the future, not yet injected
            return 0.0
        f_abs = self.cumulative_absorption_fraction(t_min, t_bolus_min)
        return float(max(0.0, bolus_units * (1.0 - f_abs)))

    def calculate_bolus_deflection(
        self,
        t_array_min: Union[List[float], np.ndarray],
        bolus_units: float,
        isf: float,
        t_bolus_min: float = 0.0,
    ) -> np.ndarray:
        """Computes glycemic deflection trajectory Delta G_bolus(t) in mg/dL relative to t=0.

        Formula:
            Delta G_bolus(t) = -ISF * U_bolus * [F_abs(t) - F_abs(0)]

        This correctly handles:
            1. Pre-bolus (t_bolus < 0): F_abs(0) > 0, so Delta G(0) = 0 and ongoing absorption
               from residual IOB drops glucose further from t=0.
            2. At meal (t_bolus = 0): F_abs(0) = 0, Delta G(t) = -ISF * U * F_abs(t).
            3. Delayed bolus (t_bolus > 0): F_abs(t) = 0 for t < t_bolus, active thereafter.
        """
        if bolus_units <= 0 or isf <= 0:
            return np.zeros(len(t_array_min), dtype=np.float32)

        f_abs_0 = self.cumulative_absorption_fraction(0.0, t_bolus_min)
        deflections = []
        for t in t_array_min:
            f_abs_t = self.cumulative_absorption_fraction(float(t), t_bolus_min)
            delta_absorbed = f_abs_t - f_abs_0
            deflection = -isf * bolus_units * delta_absorbed
            deflections.append(deflection)

        return np.array(deflections, dtype=np.float32)

    def calculate_basal_deflection(
        self,
        t_array_min: Union[List[float], np.ndarray],
        basal_rate_diff_u_hr: float,
        isf: float,
    ) -> np.ndarray:
        """Computes basal differential drift Delta G_basal(t) in mg/dL relative to t=0.

        Formula:
            Delta G_basal(t) = -ISF * Delta R_b * (t / 60)
        """
        if abs(basal_rate_diff_u_hr) < 1e-6 or isf <= 0:
            return np.zeros(len(t_array_min), dtype=np.float32)

        t_arr = np.array(t_array_min, dtype=np.float32)
        return -isf * basal_rate_diff_u_hr * (t_arr / 60.0)

    def calculate_iob_trajectory(
        self,
        t_array_min: Union[List[float], np.ndarray],
        bolus_units: float,
        t_bolus_min: float = 0.0,
    ) -> np.ndarray:
        """Computes active IOB curve across the horizon."""
        return np.array(
            [self.iob(float(t), bolus_units, t_bolus_min) for t in t_array_min], dtype=np.float32
        )


def compute_insulin_effect(
    horizon_min: List[int],
    bolus_units: float = 0.0,
    bolus_time_min: float = 0.0,
    basal_rate_diff_u_hr: float = 0.0,
    isf: float = 45.0,
    insulin_type: str = "rapid_acting",
) -> Dict[str, Any]:
    """Convenience function returning bolus deflection, basal drift, net deflection, and IOB trajectory.

    Returns dict with keys:
        - "net_deflection": np.ndarray of shape (len(horizon_min),)
        - "bolus_deflection": np.ndarray
        - "basal_deflection": np.ndarray
        - "iob_trajectory": np.ndarray
        - "residual_iob_at_t0": float
    """
    kinetics = RapidActingInsulinKinetics(insulin_type=insulin_type)
    t_arr = np.array(horizon_min, dtype=np.float32)

    bolus_delta = kinetics.calculate_bolus_deflection(
        t_array_min=t_arr,
        bolus_units=bolus_units,
        isf=isf,
        t_bolus_min=bolus_time_min,
    )
    basal_delta = kinetics.calculate_basal_deflection(
        t_array_min=t_arr,
        basal_rate_diff_u_hr=basal_rate_diff_u_hr,
        isf=isf,
    )
    iob_traj = kinetics.calculate_iob_trajectory(
        t_array_min=t_arr,
        bolus_units=bolus_units,
        t_bolus_min=bolus_time_min,
    )
    residual_iob_0 = kinetics.iob(0.0, bolus_units, bolus_time_min)

    return {
        "net_deflection": bolus_delta + basal_delta,
        "bolus_deflection": bolus_delta,
        "basal_deflection": basal_delta,
        "iob_trajectory": iob_traj,
        "residual_iob_at_t0": residual_iob_0,
    }
