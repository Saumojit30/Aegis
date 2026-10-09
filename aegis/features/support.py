"""Meal support score and out-of-distribution (OOD) guardrails (Decision D16)."""

from __future__ import annotations

import logging
from typing import Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Physiological sensor and excursion boundaries
GLUCOSE_LOWER_BOUND_MG_DL = 40.0
GLUCOSE_UPPER_BOUND_MG_DL = 400.0
DELTA_GLUCOSE_MIN = -40.0
DELTA_GLUCOSE_MAX = 180.0

# Reference CGMacros training meal distribution statistics (mean, std)
# derived from the clinical trial cohort
REFERENCE_MEAL_MEANS = {
    "carbs_g": 52.0,
    "protein_g": 24.0,
    "fat_g": 18.0,
    "fiber_g": 5.5,
    "fat_ratio": 0.22,
}

REFERENCE_MEAL_STDS = {
    "carbs_g": 25.0,
    "protein_g": 12.0,
    "fat_g": 10.0,
    "fiber_g": 3.5,
    "fat_ratio": 0.12,
}


def calculate_meal_support_score(
    carbs_g: float,
    protein_g: float,
    fat_g: float,
    fiber_g: float,
    support_threshold: float = 0.3,
) -> Tuple[float, bool]:
    """Calculate the support score of a meal relative to the training distribution.

    Returns:
        Tuple of (support_score [0.0 - 1.0], is_out_of_support [bool])
    """
    total = max(1.0, carbs_g + protein_g + fat_g)
    fat_ratio = fat_g / total

    # Compute normalized z-distance
    z_carbs = (carbs_g - REFERENCE_MEAL_MEANS["carbs_g"]) / REFERENCE_MEAL_STDS["carbs_g"]
    z_protein = (protein_g - REFERENCE_MEAL_MEANS["protein_g"]) / REFERENCE_MEAL_STDS["protein_g"]
    z_fat = (fat_g - REFERENCE_MEAL_MEANS["fat_g"]) / REFERENCE_MEAL_STDS["fat_g"]
    z_fat_ratio = (fat_ratio - REFERENCE_MEAL_MEANS["fat_ratio"]) / REFERENCE_MEAL_STDS["fat_ratio"]

    # Euclidean distance in standardized macro space
    dist = float(np.sqrt(z_carbs**2 + z_protein**2 + z_fat**2 + (2.0 * z_fat_ratio**2)))

    # Convert distance to a bounded support score [0.0, 1.0]
    # score = 1.0 at distance 0; drops off smoothly via exponential decay
    score = float(np.exp(-0.35 * max(0.0, dist - 1.0)))
    score = min(1.0, max(0.0, score))

    is_ood = score < support_threshold
    return score, is_ood


def clamp_trajectory_to_physiological_bounds(
    baseline_glucose: float,
    delta_trajectory: np.ndarray | list[float],
) -> np.ndarray:
    """Strictly clamp predicted ΔG and absolute glucose to physiological boundaries (Decision D16)."""
    deltas = np.array(delta_trajectory, dtype=np.float32)

    # 1. Clamp excursions
    deltas = np.clip(deltas, DELTA_GLUCOSE_MIN, DELTA_GLUCOSE_MAX)

    # 2. Clamp absolute glucose
    absolute_g = baseline_glucose + deltas
    clamped_absolute = np.clip(absolute_g, GLUCOSE_LOWER_BOUND_MG_DL, GLUCOSE_UPPER_BOUND_MG_DL)

    return clamped_absolute - baseline_glucose
