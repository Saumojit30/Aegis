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


def test_structured_meal_head_properties_and_overrides():
    model = StructuredMealForecasterS()

    # Check nominal property getters
    assert 20.0 <= model.base_tau_fast <= 60.0
    assert 60.0 <= model.base_tau_slow <= 140.0
    assert 5.0 <= model.base_delay <= 40.0

    seq = torch.randn(1, 12, 6)
    static = torch.randn(1, 8)
    meal = torch.randn(1, 16)
    anchor = torch.randn(1, 4)

    phi_nominal = model.compute_phi(meal)
    assert 0.0 <= phi_nominal <= 1.0

    # Test forward with return_components
    traj_nom, res_nom, kinetic_nom = model(seq, static, meal, anchor, return_components=True)
    assert traj_nom.shape == (1, 36)
    assert res_nom.shape == (1, 36)
    assert kinetic_nom.shape == (1, 36)
    assert torch.allclose(traj_nom, kinetic_nom + res_nom, atol=1e-5)

    # Test forward with overrides (e.g. food sequencing parameters)
    traj_seq, res_seq, kinetic_seq = model(
        seq,
        static,
        meal,
        anchor,
        tau_fast_override=model.base_tau_fast * 1.25,
        delay_override=model.base_delay * 1.35 + 10.0,
        phi_override=min(1.0, phi_nominal + 0.25),
        return_components=True,
    )
    # Excursion curve should differ under delayed emptying
    assert not torch.allclose(traj_nom, traj_seq, atol=1e-3)
    # Peak of kinetic absorption curve should be shifted later in time
    nom_peak_step = int(torch.argmax(kinetic_nom[0]).item())
    seq_peak_step = int(torch.argmax(kinetic_seq[0]).item())
    assert seq_peak_step >= nom_peak_step


def test_kinetic_overrides_boundary_clamping_and_numpy():
    import numpy as np

    model = StructuredMealForecasterS()
    seq = torch.randn(1, 12, 6)
    static = torch.randn(1, 8)
    meal = torch.randn(1, 16)
    anchor = torch.randn(1, 4)

    # Test numpy array input to compute_phi
    meal_np = np.random.randn(16).astype(np.float32)
    phi_np = model.compute_phi(meal_np)
    assert 0.0 <= phi_np <= 1.0

    # Negative delay, negative tau_fast, out-of-range phi
    traj, _, kinetic = model(
        seq,
        static,
        meal,
        anchor,
        tau_fast_override=-10.0,  # should be clamped >= 5.0
        delay_override=-5.0,  # should be clamped >= 0.0
        phi_override=1.5,  # should be clamped <= 1.0
        return_components=True,
    )
    assert not torch.isnan(traj).any()
    assert not torch.isinf(traj).any()
    assert not torch.isnan(kinetic).any()
