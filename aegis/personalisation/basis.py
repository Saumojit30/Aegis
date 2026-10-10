"""Low-rank PCA basis decomposition of trajectory prediction residuals."""

from __future__ import annotations

import logging

import numpy as np
from sklearn.decomposition import PCA

logger = logging.getLogger(__name__)


class ResidualBasis:
    """Computes and stores a low-rank PCA basis matrix V of shape [36, r] for few-shot adaptation."""

    def __init__(self, n_components: int = 3) -> None:
        self.n_components = n_components
        self.pca = PCA(n_components=n_components)
        self.basis_matrix: np.ndarray | None = None
        self.mean_residual: np.ndarray | None = None

    def fit(self, residuals: np.ndarray) -> "ResidualBasis":
        """Fit PCA on training residual curves of shape [N, 36]."""
        # Center residuals
        self.pca.fit(residuals)
        # Components are of shape [r, 36], transpose to [36, r]
        self.basis_matrix = self.pca.components_.T.astype(np.float32)
        self.mean_residual = self.pca.mean_.astype(np.float32)
        logger.info(
            "Fitted residual PCA basis (r=%d), explained variance ratio: %s",
            self.n_components,
            self.pca.explained_variance_ratio_.round(3),
        )
        return self

    def transform(self, residual_curve: np.ndarray) -> np.ndarray:
        """Project a residual curve of shape [36] onto the basis to get coefficients α of shape [r]."""
        if self.basis_matrix is None or self.mean_residual is None:
            raise ValueError("ResidualBasis must be fitted before transforming.")
        centered = residual_curve - self.mean_residual
        # α = V^T * centered
        alpha = np.dot(self.basis_matrix.T, centered)
        return alpha.astype(np.float32)

    def reconstruct(self, alpha: np.ndarray) -> np.ndarray:
        """Reconstruct 36-step residual curve from coefficients α: V * α + mean."""
        if self.basis_matrix is None or self.mean_residual is None:
            raise ValueError("ResidualBasis must be fitted before reconstructing.")
        curve = np.dot(self.basis_matrix, alpha) + self.mean_residual
        return curve.astype(np.float32)
