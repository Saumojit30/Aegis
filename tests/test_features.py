"""Unit tests for shared feature extraction, missingness resilience, and support scoring."""

import numpy as np
import pandas as pd

from aegis.features.extract import (
    extract_meal_features,
    extract_sequence_and_anchor_features,
    extract_static_features,
)
from aegis.features.support import (
    calculate_meal_support_score,
    clamp_trajectory_to_physiological_bounds,
)


def test_extract_static_features():
    profile = {
        "age": 52.0,
        "sex": "male",
        "bmi": 28.5,
        "hba1c": 6.3,
        "fasting_glucose": 115.0,
        "fasting_insulin": 14.0,
        "triglycerides": 160.0,
        "hdl": 46.0,
    }
    vec = extract_static_features(profile)
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (8,)
    # Male = 1.0 at index 1
    assert vec[1] == 1.0

    # Test resilience against np.float32 NaN, string NaN, pd.NA, and inf
    series_with_nans = pd.Series({
        "age": np.float32(np.nan),
        "sex": "female",
        "bmi": float("inf"),
        "hba1c": "nan",
        "fasting_glucose": pd.NA,
        "fasting_insulin": None,
        "triglycerides": np.nan,
        "hdl": 50.0,
    })
    vec_nans = extract_static_features(series_with_nans)
    assert isinstance(vec_nans, np.ndarray)
    assert vec_nans.shape == (8,)
    assert not np.isnan(vec_nans).any()
    assert not np.isinf(vec_nans).any()


def test_extract_meal_features():
    meal = {
        "calories_eff": 500.0,
        "carbs_eff": 55.0,
        "protein_eff": 25.0,
        "fat_eff": 20.0,
        "fiber_eff": 5.0,
        "meal_type": "lunch",
    }
    vec = extract_meal_features(meal, ts_start=pd.Timestamp("2026-10-01 12:30"))
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (16,)


def test_sequence_missingness_masks_d15():
    # 12 steps history where HR is completely missing
    ts_list = [pd.Timestamp("2026-10-01 12:00") + pd.Timedelta(minutes=5 * i) for i in range(12)]
    df = pd.DataFrame(
        {
            "ts": ts_list,
            "glucose": [100.0 + i for i in range(12)],
            "hr": [np.nan] * 12,  # HR missing
            "mets": [1.2] * 12,
            "hr_missing": [True] * 12,
            "mets_missing": [False] * 12,
        }
    )

    t0 = pd.Timestamp("2026-10-01 12:55")
    seq, anchor, g_t0 = extract_sequence_and_anchor_features(df, t0, steps=12)

    assert seq.shape == (12, 6)
    assert anchor.shape == (4,)
    # Glucose mask channel (index 1) should be 1.0
    assert (seq[:, 1] == 1.0).all()
    # HR mask channel (index 3) should be 0.0 (missing)
    assert (seq[:, 3] == 0.0).all()
    # METs mask channel (index 5) should be 1.0 (present)
    assert (seq[:, 5] == 1.0).all()


def test_meal_support_score_and_clamping_d16():
    # Typical in-distribution meal
    score_normal, is_ood_normal = calculate_meal_support_score(50.0, 25.0, 15.0, 5.0)
    assert score_normal > 0.5
    assert not is_ood_normal

    # Extreme meal (250g carbs, 120g fat)
    score_extreme, is_ood_extreme = calculate_meal_support_score(250.0, 10.0, 120.0, 1.0)
    assert score_extreme < 0.3
    assert is_ood_extreme

    # Test clamping
    baseline_g = 130.0
    deltas = [-80.0, 50.0, 220.0, 350.0]  # extreme deltas
    clamped = clamp_trajectory_to_physiological_bounds(baseline_g, deltas)
    final_glucose = baseline_g + clamped
    assert (final_glucose >= 40.0).all()
    assert (final_glucose <= 400.0).all()
