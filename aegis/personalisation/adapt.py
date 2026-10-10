"""Few-shot chronological ridge adaptation over residual PCA basis curves."""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np

from aegis.personalisation.basis import ResidualBasis

logger = logging.getLogger(__name__)


def adapt_prediction_with_prior(
    global_prediction: np.ndarray,
    basis: ResidualBasis,
    past_residuals: List[np.ndarray],
    prior_alpha: Optional[np.ndarray] = None,
    shrinkage_lambda: float = 2.0,
) -> np.ndarray:
    """Adapt a global forecast using a patient's earlier K meals shrunk toward a prior.

    Args:
        global_prediction: Global model forecast curve of shape [36].
        basis: Fitted ResidualBasis object.
        past_residuals: List of residual curves (true - global_pred) for earlier meals.
        prior_alpha: Prior coefficient vector of shape [r] (from similarity or 0).
        shrinkage_lambda: Ridge shrinkage parameter (higher = more shrinkage to prior).

    Returns:
        Adapted trajectory of shape [36].
    """
    r_dim = basis.n_components
    prior = prior_alpha if prior_alpha is not None else np.zeros(r_dim, dtype=np.float32)

    k = len(past_residuals)
    if k == 0:
        # Cold start: use prior only
        alpha_adapted = prior
    else:
        # Project past residuals onto basis
        alphas = [basis.transform(res) for res in past_residuals]
        mean_alpha = np.mean(alphas, axis=0)

        # Empirical Bayes / Ridge shrinkage toward prior:
        # alpha = (K / (K + lambda)) * mean_alpha + (lambda / (K + lambda)) * prior
        weight_data = float(k) / (float(k) + shrinkage_lambda)
        weight_prior = shrinkage_lambda / (float(k) + shrinkage_lambda)

        alpha_adapted = (weight_data * mean_alpha) + (weight_prior * prior)

    # Reconstruct residual adjustment curve
    adjustment = basis.reconstruct(alpha_adapted)
    adapted_forecast = global_prediction + adjustment
    return adapted_forecast.astype(np.float32)
