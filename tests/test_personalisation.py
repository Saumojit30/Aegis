"""Unit tests for residual PCA basis, ridge adaptation, and clinical similarity."""

import numpy as np

from aegis.personalisation.adapt import adapt_prediction_with_prior
from aegis.personalisation.basis import ResidualBasis
from aegis.personalisation.similarity import compute_patient_similarity_prior


def test_residual_basis_fit_and_reconstruct():
    rng = np.random.default_rng(42)
    residuals = rng.normal(0, 5.0, size=(20, 36)).astype(np.float32)

    basis = ResidualBasis(n_components=3).fit(residuals)
    assert basis.basis_matrix is not None
    assert basis.basis_matrix.shape == (36, 3)

    sample_res = residuals[0]
    alpha = basis.transform(sample_res)
    assert alpha.shape == (3,)

    recon = basis.reconstruct(alpha)
    assert recon.shape == (36,)
    # Reconstruction should be reasonably close to low-rank approximation
    assert np.mean((sample_res - recon) ** 2) < 30.0


def test_chronological_ridge_adaptation():
    rng = np.random.default_rng(42)
    residuals = rng.normal(0, 5.0, size=(10, 36)).astype(np.float32)
    basis = ResidualBasis(n_components=3).fit(residuals)

    global_pred = np.zeros(36, dtype=np.float32)

    # K = 0 (Cold start -> prior only)
    prior_alpha = np.array([2.0, -1.0, 0.5], dtype=np.float32)
    adapted_k0 = adapt_prediction_with_prior(global_pred, basis, [], prior_alpha=prior_alpha)
    expected_k0 = basis.reconstruct(prior_alpha)
    assert np.allclose(adapted_k0, expected_k0, atol=1e-5)

    # K = 3 (Shrunk toward prior)
    past_residuals = [residuals[0], residuals[1], residuals[2]]
    adapted_k3 = adapt_prediction_with_prior(
        global_pred, basis, past_residuals, prior_alpha=prior_alpha, shrinkage_lambda=2.0
    )
    assert adapted_k3.shape == (36,)
    assert not np.isnan(adapted_k3).any()


def test_similarity_prior_excludes_target():
    ref_static = {
        "P1": np.array([0.0] * 8, dtype=np.float32),
        "P2": np.array([1.0] * 8, dtype=np.float32),
        "P3": np.array([2.0] * 8, dtype=np.float32),
    }
    ref_alphas = {
        "P1": np.array([1.0, 0.0, 0.0], dtype=np.float32),
        "P2": np.array([0.0, 1.0, 0.0], dtype=np.float32),
        "P3": np.array([0.0, 0.0, 1.0], dtype=np.float32),
    }

    target_pid = "P1"
    target_static = np.array([0.0] * 8, dtype=np.float32)

    prior_alpha, neighbors = compute_patient_similarity_prior(
        target_pid, target_static, ref_static, ref_alphas, k_neighbors=2
    )

    # Verify target patient P1 is strictly excluded
    neighbor_ids = [n["patient_id"] for n in neighbors]
    assert "P1" not in neighbor_ids
    assert "P2" in neighbor_ids
    assert len(prior_alpha) == 3
