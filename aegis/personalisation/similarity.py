"""Patient clinical profile similarity network for cold-start adaptation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def compute_patient_similarity_prior(
    target_pid: str,
    target_static: np.ndarray,
    reference_static_profiles: Dict[str, np.ndarray],
    reference_alphas: Dict[str, np.ndarray],
    k_neighbors: int = 3,
    gamma: float = 0.5,
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """Compute cold-start similarity prior alpha_0 for target patient from nearest clinical twins.

    Args:
        target_pid: ID of target patient to be excluded from neighbor selection.
        target_static: 8-dimensional static profile vector of target patient.
        reference_static_profiles: Mapping of pid -> static profile vector.
        reference_alphas: Mapping of pid -> fitted adaptation coefficients [r].
        k_neighbors: Number of nearest neighbors to aggregate.
        gamma: RBF kernel bandwidth parameter.

    Returns:
        Tuple of (prior_alpha [r], list of nearest neighbor info dictionaries).
    """
    candidates = []

    for pid, profile in reference_static_profiles.items():
        if pid == target_pid or pid not in reference_alphas:
            continue

        # Standardized Euclidean distance
        dist = float(np.linalg.norm(target_static - profile))
        # RBF Gaussian kernel weight
        sim_weight = float(np.exp(-gamma * (dist**2)))

        candidates.append(
            {
                "patient_id": pid,
                "distance": round(dist, 3),
                "similarity": round(sim_weight, 4),
                "alpha": reference_alphas[pid],
            }
        )

    if not candidates:
        r_dim = len(next(iter(reference_alphas.values()))) if reference_alphas else 3
        return np.zeros(r_dim, dtype=np.float32), []

    # Sort by highest similarity (smallest distance)
    candidates.sort(key=lambda x: x["distance"])
    top_k = candidates[:k_neighbors]

    # Normalize weights
    total_sim = sum(c["similarity"] for c in top_k) + 1e-6
    for c in top_k:
        c["normalized_weight"] = round(c["similarity"] / total_sim, 4)

    # Weighted average of neighbor alphas
    prior_alpha = np.zeros_like(top_k[0]["alpha"], dtype=np.float32)
    for c in top_k:
        prior_alpha += c["normalized_weight"] * np.array(c["alpha"], dtype=np.float32)

    return prior_alpha, top_k
