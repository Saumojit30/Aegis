"""Single source of truth degradation scenarios (D0-D7).

Used across training, evaluation, inference services, and clinician replay.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import torch

from aegis.features.extract import extract_meal_features


class DegradationScenario(str, Enum):
    """Enumeration of standard degradation scenarios D0-D7."""

    D0_NONE = "D0"
    D1_15M = "D1_15m"
    D1_30M = "D1_30m"
    D1_60M = "D1_60m"
    D2_20 = "D2_20"
    D2_50 = "D2_50"
    D3 = "D3"
    D4 = "D4"
    D5 = "D5"
    D6 = "D6"
    D7 = "D7"


ALL_SCENARIOS = [
    DegradationScenario.D0_NONE,
    DegradationScenario.D1_15M,
    DegradationScenario.D1_30M,
    DegradationScenario.D1_60M,
    DegradationScenario.D2_20,
    DegradationScenario.D2_50,
    DegradationScenario.D3,
    DegradationScenario.D4,
    DegradationScenario.D5,
    DegradationScenario.D6,
    DegradationScenario.D7,
]


def apply_degradation(
    seq: Union[torch.Tensor, np.ndarray],
    anchor: Union[torch.Tensor, np.ndarray],
    meal: Union[torch.Tensor, np.ndarray],
    static: Union[torch.Tensor, np.ndarray],
    scenario: Union[DegradationScenario, str] = DegradationScenario.D0_NONE,
    raw_meal: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
) -> Tuple[
    Union[torch.Tensor, np.ndarray],
    Union[torch.Tensor, np.ndarray],
    Union[torch.Tensor, np.ndarray],
    Union[torch.Tensor, np.ndarray],
    Dict[str, Any],
]:
    """Applies a degradation scenario to sequence, anchor, meal, and static features.

    Preserves exact tensor shapes and devices.
    """
    if isinstance(scenario, str):
        try:
            scenario = DegradationScenario(scenario)
        except ValueError:
            # Fallback matching by prefix/string
            s_upper = scenario.upper()
            if "D1_15" in s_upper or "15M" in s_upper:
                scenario = DegradationScenario.D1_15M
            elif "D1_30" in s_upper or "30M" in s_upper:
                scenario = DegradationScenario.D1_30M
            elif "D1_60" in s_upper or "60M" in s_upper:
                scenario = DegradationScenario.D1_60M
            elif "D2_50" in s_upper or "50" in s_upper:
                scenario = DegradationScenario.D2_50
            elif "D2" in s_upper or "20" in s_upper:
                scenario = DegradationScenario.D2_20
            elif "D3" in s_upper:
                scenario = DegradationScenario.D3
            elif "D4" in s_upper:
                scenario = DegradationScenario.D4
            elif "D5" in s_upper:
                scenario = DegradationScenario.D5
            elif "D6" in s_upper:
                scenario = DegradationScenario.D6
            elif "D7" in s_upper:
                scenario = DegradationScenario.D7
            else:
                scenario = DegradationScenario.D0_NONE

    is_torch = isinstance(seq, torch.Tensor)
    if is_torch:
        out_seq = seq.clone()
        out_anchor = anchor.clone()
        out_meal = meal.clone()
        out_static = static.clone()
    else:
        out_seq = np.copy(seq)
        out_anchor = np.copy(anchor)
        out_meal = np.copy(meal)
        out_static = np.copy(static)

    metadata: Dict[str, Any] = {
        "scenario": scenario.value,
        "is_degraded": scenario != DegradationScenario.D0_NONE,
        "anchor_age_min": 0.0,
        "warning": None,
        "reduced_sensor": False,
        "cold_start": False,
        "out_of_support": False,
    }

    steps = out_seq.shape[-2]
    rng = np.random.RandomState(seed)

    if scenario == DegradationScenario.D0_NONE:
        return out_seq, out_anchor, out_meal, out_static, metadata

    elif scenario in [
        DegradationScenario.D1_15M,
        DegradationScenario.D1_30M,
        DegradationScenario.D1_60M,
    ]:
        # CGM dropout for last N minutes
        dropout_min = (
            15
            if scenario == DegradationScenario.D1_15M
            else (30 if scenario == DegradationScenario.D1_30M else 60)
        )
        dropout_steps = min(steps, dropout_min // 5)
        metadata["anchor_age_min"] = float(dropout_min)
        metadata["warning"] = (
            f"CGM missing for the last {dropout_min} minutes. Prediction anchored to earlier observation."
        )

        # Mask out glucose for the last dropout_steps
        if dropout_steps > 0:
            out_seq[..., -dropout_steps:, 0] = 0.0  # delta
            out_seq[..., -dropout_steps:, 1] = 0.0  # mask

        # Update anchor age in anchor vector: index 1 is min(2.0, anchor_age / 30.0)
        age_feature = min(2.0, dropout_min / 30.0)
        out_anchor[..., 1] = age_feature

        # If all steps were dropped, anchor falls back to fasting glucose from static profile
        if dropout_steps >= steps:
            # Fasting glucose is static index 4
            out_anchor[..., 0] = out_static[..., 4]
            out_anchor[..., 2] = 0.0  # pre_meal_mean_30
            out_anchor[..., 3] = 0.0  # pre_meal_slope_15

    elif scenario in [DegradationScenario.D2_20, DegradationScenario.D2_50]:
        # Random gaps in CGM
        drop_rate = 0.20 if scenario == DegradationScenario.D2_20 else 0.50
        metadata["warning"] = (
            f"Intermittent CGM communication gaps ({int(drop_rate * 100)}% dropout rate)."
        )

        if is_torch:
            mask = torch.from_numpy(rng.rand(*out_seq.shape[:-1]) < drop_rate).to(out_seq.device)
            out_seq[..., 0] = torch.where(mask, torch.zeros_like(out_seq[..., 0]), out_seq[..., 0])
            out_seq[..., 1] = torch.where(mask, torch.zeros_like(out_seq[..., 1]), out_seq[..., 1])
        else:
            mask = rng.rand(*out_seq.shape[:-1]) < drop_rate
            out_seq[mask, 0] = 0.0
            out_seq[mask, 1] = 0.0

    elif scenario == DegradationScenario.D3:
        # Wearables missing: HR and METs zeroed out
        metadata["warning"] = "Wearable activity & heart rate telemetry missing."
        out_seq[..., 2] = 0.0  # HR z-score
        out_seq[..., 3] = 0.0  # HR mask
        out_seq[..., 4] = 0.0  # METs z-score
        out_seq[..., 5] = 0.0  # METs mask

    elif scenario == DegradationScenario.D4:
        # Reduced sensor mode (No CGM in entire history window)
        metadata["reduced_sensor"] = True
        metadata["anchor_age_min"] = 720.0
        metadata["warning"] = (
            "Estimate based on wearables and profile only - not suitable for treatment decisions."
        )
        # All glucose sequence masked
        out_seq[..., 0] = 0.0
        out_seq[..., 1] = 0.0

        # Anchor falls back to static fasting glucose (index 4 of static)
        out_anchor[..., 0] = out_static[..., 4]
        out_anchor[..., 1] = 2.0  # min(2.0, 720 / 30) = 2.0
        out_anchor[..., 2] = 0.0  # pre_meal_mean_30
        out_anchor[..., 3] = 0.0  # pre_meal_slope_15

    elif scenario == DegradationScenario.D5:
        # Incomplete meal: substitute population defaults
        metadata["warning"] = (
            "Incomplete meal composition; replaced with population nutritional medians."
        )
        # If raw_meal provided, use extract_meal_features with population medians
        default_meal = {
            "calories": 500.0,
            "carbs_g": 55.0,
            "protein_g": 25.0,
            "fat_g": 20.0,
            "fiber_g": 5.0,
            "meal_type": "lunch",
            "minutes_since_prev_meal": 360.0,
        }
        std_meal = extract_meal_features(default_meal)
        if is_torch:
            std_meal_t = torch.tensor(std_meal, dtype=out_meal.dtype, device=out_meal.device)
            if out_meal.ndim == 2:
                out_meal[:] = std_meal_t.unsqueeze(0)
            else:
                out_meal[:] = std_meal_t
        else:
            if out_meal.ndim == 2:
                out_meal[:] = std_meal[np.newaxis, :]
            else:
                out_meal[:] = std_meal

    elif scenario == DegradationScenario.D6:
        # Cold start: K=0 personal meals
        metadata["cold_start"] = True
        metadata["warning"] = (
            "New patient cold-start (K=0 meals). Prior computed via clinical similarity."
        )

    elif scenario == DegradationScenario.D7:
        # Out of support meal
        metadata["out_of_support"] = True
        metadata["warning"] = (
            "Meal nutritional profile is outside historical support envelope; conservative bounds applied."
        )

    return out_seq, out_anchor, out_meal, out_static, metadata
