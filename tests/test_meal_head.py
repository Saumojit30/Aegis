"""Unit tests for Structured Fast/Slow Meal Head (Candidate S)."""

import torch

from aegis.models.meal_head import StructuredMealForecasterS


def test_structured_meal_head_forward_and_backward():
    model = StructuredMealForecasterS()

    seq = torch.randn(2, 12, 6)
    static = torch.randn(2, 8)
    meal = torch.randn(2, 16)
    anchor = torch.randn(2, 4)

    traj, residual = model(seq, static, meal, anchor)
    assert traj.shape == (2, 36)
    assert residual.shape == (2, 36)
    assert not torch.isnan(traj).any()

    # Verify gradients flow back to all parameters
    loss = torch.mean(traj**2) + torch.mean(residual**2)
    loss.backward()

    assert model.raw_tau_fast.grad is not None
    assert model.raw_tau_slow.grad is not None
    assert model.raw_delay.grad is not None


def test_basis_curve_bounds():
    model = StructuredMealForecasterS()
    b_fast, b_slow = model._compute_basis_curves(batch_size=1, device=torch.device("cpu"))

    assert b_fast.shape == (1, 36)
    assert b_slow.shape == (1, 36)
    # Basis curves should be positive gamma curves
    assert (b_fast >= 0.0).all()
    assert (b_slow >= 0.0).all()
    # Peaks should be finite and normalized around 1.0
    assert torch.max(b_fast).item() <= 1.5
    assert torch.max(b_slow).item() <= 1.5
