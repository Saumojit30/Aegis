"""Unit tests for degradation scenarios D0-D7."""

import numpy as np
import pytest
import torch

from aegis.degradation.scenarios import (
    ALL_SCENARIOS,
    DegradationScenario,
    apply_degradation,
)


@pytest.fixture
def mock_sample_tensors():
    seq = torch.randn(1, 12, 6)
    seq[..., 1] = 1.0  # observed
    seq[..., 3] = 1.0
    seq[..., 5] = 1.0

    anchor = torch.tensor([[0.5, 0.0, 0.1, 0.05]])
    meal = torch.randn(1, 16)
    static = torch.tensor([[0.2, 1.0, 0.4, 0.1, 0.8, 0.2, -0.1, 0.3]])
    return seq, anchor, meal, static


def test_d0_identity(mock_sample_tensors):
    seq, anchor, meal, static = mock_sample_tensors
    deg_seq, deg_anchor, deg_meal, deg_static, meta = apply_degradation(
        seq, anchor, meal, static, DegradationScenario.D0_NONE
    )
    assert torch.allclose(seq, deg_seq)
    assert torch.allclose(anchor, deg_anchor)
    assert meta["is_degraded"] is False
    assert meta["warning"] is None


def test_d1_cgm_dropout(mock_sample_tensors):
    seq, anchor, meal, static = mock_sample_tensors
    # 30 min dropout = 6 steps
    deg_seq, deg_anchor, deg_meal, deg_static, meta = apply_degradation(
        seq, anchor, meal, static, DegradationScenario.D1_30M
    )
    assert meta["is_degraded"] is True
    assert meta["anchor_age_min"] == 30.0
    # Last 6 steps of glucose delta and mask must be 0
    assert torch.all(deg_seq[0, -6:, 0] == 0.0)
    assert torch.all(deg_seq[0, -6:, 1] == 0.0)
    # First 6 steps of mask should remain 1.0
    assert torch.all(deg_seq[0, :6, 1] == 1.0)
    # Anchor age feature: min(2.0, 30/30) = 1.0
    assert deg_anchor[0, 1].item() == pytest.approx(1.0)


def test_d2_cgm_gaps(mock_sample_tensors):
    seq, anchor, meal, static = mock_sample_tensors
    deg_seq, _, _, _, meta = apply_degradation(
        seq, anchor, meal, static, DegradationScenario.D2_50, seed=42
    )
    assert meta["is_degraded"] is True
    # At 50% drop, some masks must be zero
    zero_count = (deg_seq[0, :, 1] == 0.0).sum().item()
    assert 0 < zero_count < 12


def test_d3_missing_wearables(mock_sample_tensors):
    seq, anchor, meal, static = mock_sample_tensors
    deg_seq, _, _, _, meta = apply_degradation(seq, anchor, meal, static, DegradationScenario.D3)
    assert meta["is_degraded"] is True
    # HR and METs values and masks zeroed out
    assert torch.all(deg_seq[..., 2] == 0.0)
    assert torch.all(deg_seq[..., 3] == 0.0)
    assert torch.all(deg_seq[..., 4] == 0.0)
    assert torch.all(deg_seq[..., 5] == 0.0)
    # Glucose mask intact
    assert torch.all(deg_seq[..., 1] == 1.0)


def test_d4_reduced_sensor(mock_sample_tensors):
    seq, anchor, meal, static = mock_sample_tensors
    deg_seq, deg_anchor, _, _, meta = apply_degradation(
        seq, anchor, meal, static, DegradationScenario.D4
    )
    assert meta["reduced_sensor"] is True
    assert "not suitable for treatment decisions" in meta["warning"]
    # All glucose masks are zero
    assert torch.all(deg_seq[..., 1] == 0.0)
    # Anchor age is capped at 2.0
    assert deg_anchor[0, 1].item() == pytest.approx(2.0)
    # Anchor glucose equals static fasting glucose (static[..., 4])
    assert deg_anchor[0, 0].item() == pytest.approx(static[0, 4].item())


def test_d5_incomplete_meal(mock_sample_tensors):
    seq, anchor, meal, static = mock_sample_tensors
    _, _, deg_meal, _, meta = apply_degradation(seq, anchor, meal, static, DegradationScenario.D5)
    assert meta["is_degraded"] is True
    assert deg_meal.shape == meal.shape


def test_all_scenarios_shape_invariance_numpy():
    seq = np.ones((12, 6), dtype=np.float32)
    anchor = np.zeros(4, dtype=np.float32)
    meal = np.zeros(16, dtype=np.float32)
    static = np.zeros(8, dtype=np.float32)

    for sc in ALL_SCENARIOS:
        d_seq, d_anchor, d_meal, d_static, meta = apply_degradation(
            seq, anchor, meal, static, sc, seed=123
        )
        assert d_seq.shape == (12, 6)
        assert d_anchor.shape == (4,)
        assert d_meal.shape == (16,)
        assert d_static.shape == (8,)
        assert meta["scenario"] == sc.value
