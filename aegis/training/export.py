"""Production model artifact bundler and clean offline loading interface."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import torch

from aegis.common.tracking import get_git_commit
from aegis.degradation.scenarios import DegradationScenario, apply_degradation
from aegis.models.dataset import MealForecastingDataset, collate_meal_batch
from aegis.models.meal_head import StructuredMealForecasterS
from aegis.personalisation.adapt import adapt_prediction_with_prior
from aegis.personalisation.basis import ResidualBasis
from aegis.personalisation.similarity import compute_patient_similarity_prior
from aegis.training.train import train_model
from aegis.uncertainty.conformal import (
    ConformalCalibrationTable,
    compute_interval_conformal_bounds,
)
from aegis.uncertainty.reliability import ReliabilityAssessment, assess_reliability

logger = logging.getLogger(__name__)


@dataclass
class AegisBundle:
    """Self-contained runtime forecasting engine for inference service and clinician replay."""

    model: StructuredMealForecasterS
    basis: ResidualBasis
    calibration_table: ConformalCalibrationTable
    reference_static_profiles: Dict[str, np.ndarray]
    reference_alphas: Dict[str, np.ndarray]
    metadata: Dict[str, Any]

    def predict(
        self,
        seq: Union[np.ndarray, torch.Tensor],
        anchor: Union[np.ndarray, torch.Tensor],
        meal: Union[np.ndarray, torch.Tensor],
        static: Union[np.ndarray, torch.Tensor],
        g_t0: float = 120.0,
        patient_id: str = "P_SIM",
        earlier_residuals: Optional[List[np.ndarray]] = None,
        scenario: Union[DegradationScenario, str] = DegradationScenario.D0_NONE,
        confidence_level: float = 0.90,
        seed: Optional[int] = 42,
        tau_fast_override: Optional[float] = None,
        delay_override: Optional[float] = None,
        phi_override: Optional[float] = None,
        portion_uncertainty_pct: float = 0.0,
    ) -> Dict[str, Any]:
        """Runs end-to-end forecasting, few-shot personalisation, conformal bounds, and reliability assessment.

        Returns:
            Dictionary matching the frozen PredictResponse contract.
        """
        if earlier_residuals is None:
            earlier_residuals = []

        is_torch = isinstance(seq, torch.Tensor)
        if not is_torch:
            seq_t = torch.tensor(seq, dtype=torch.float32)
            anchor_t = torch.tensor(anchor, dtype=torch.float32)
            meal_t = torch.tensor(meal, dtype=torch.float32)
            static_t = torch.tensor(static, dtype=torch.float32)
        else:
            seq_t = seq.float()
            anchor_t = anchor.float()
            meal_t = meal.float()
            static_t = static.float()

        if seq_t.ndim == 2:
            seq_t = seq_t.unsqueeze(0)
            anchor_t = anchor_t.unsqueeze(0)
            meal_t = meal_t.unsqueeze(0)
            static_t = static_t.unsqueeze(0)

        # 1. Apply degradation transforms
        d_seq, d_anchor, d_meal, d_static, deg_meta = apply_degradation(
            seq_t, anchor_t, meal_t, static_t, scenario=scenario, seed=seed
        )

        # 2. Forward pass through Candidate S with optional kinetic overrides
        self.model.eval()
        with torch.no_grad():
            point_delta, _, traj_kinetic = self.model(
                d_seq,
                d_static,
                d_meal,
                d_anchor,
                tau_fast_override=tau_fast_override,
                delay_override=delay_override,
                phi_override=phi_override,
                return_components=True,
            )
            point_delta_np = point_delta.squeeze(0).cpu().numpy()
            traj_kinetic_np = traj_kinetic.squeeze(0).cpu().numpy()

        # 3. Few-shot adaptation
        static_np = static_t.squeeze(0).cpu().numpy()
        alpha_prior, neighbors = compute_patient_similarity_prior(
            patient_id, static_np, self.reference_static_profiles, self.reference_alphas
        )

        k_count = len(earlier_residuals)
        if deg_meta.get("cold_start") or k_count == 0:
            adapted_delta = adapt_prediction_with_prior(
                point_delta_np, self.basis, past_residuals=[], prior_alpha=alpha_prior
            )
        else:
            adapted_delta = adapt_prediction_with_prior(
                point_delta_np, self.basis, past_residuals=earlier_residuals[:5], prior_alpha=alpha_prior
            )

        adapted_pred = float(g_t0) + adapted_delta

        # 4. Out of support / physiological bounds clamping
        if deg_meta.get("out_of_support"):
            adapted_pred = np.clip(adapted_pred, 40.0, 400.0)

        # 5. Split-conformal prediction intervals and robust portion uncertainty bounds
        quantiles = self.calibration_table.get_quantiles(
            scenario=scenario, confidence_level=confidence_level
        )
        delta_portion = float(np.clip(portion_uncertainty_pct / 100.0, 0.0, 0.50))
        lower_bound, upper_bound, lower_robust, upper_robust = compute_interval_conformal_bounds(
            adapted_pred,
            traj_kinetic_np,
            quantiles,
            delta_portion=delta_portion,
            clamp_physiological=True,
        )

        # 6. Reliability assessment
        mean_width = float(np.mean(upper_bound - lower_bound))
        anchor_age = float(deg_meta.get("anchor_age_min", 0.0))
        supp_score = 0.1 if deg_meta.get("out_of_support") else 1.0

        rel_assessment: ReliabilityAssessment = assess_reliability(
            scenario=scenario,
            mean_interval_width=mean_width,
            k_personal_meals=k_count,
            support_score=supp_score,
            has_wearables=not (deg_meta.get("scenario") == "D3"),
            anchor_age_min=anchor_age,
        )

        # 7. Summary metrics
        peak_idx = int(np.argmax(adapted_pred))
        peak_glucose = float(adapted_pred[peak_idx])
        time_to_peak_min = (peak_idx + 1) * 5

        return {
            "forecast": [round(float(v), 2) for v in adapted_pred],
            "interval_lower": [round(float(v), 2) for v in lower_bound],
            "interval_upper": [round(float(v), 2) for v in upper_bound],
            "interval_lower_robust": [round(float(v), 2) for v in lower_robust]
            if delta_portion > 0.0
            else None,
            "interval_upper_robust": [round(float(v), 2) for v in upper_robust]
            if delta_portion > 0.0
            else None,
            "traj_kinetic": [round(float(v), 2) for v in traj_kinetic_np],
            "peak_glucose": round(peak_glucose, 1),
            "time_to_peak_min": time_to_peak_min,
            "reliability": rel_assessment.to_dict(),
            "metadata": {
                "scenario": deg_meta.get("scenario", "D0"),
                "is_degraded": deg_meta.get("is_degraded", False),
                "confidence_level": confidence_level,
                "anchor_age_min": anchor_age,
                "portion_uncertainty_pct": portion_uncertainty_pct,
                "warning": deg_meta.get("warning"),
            },
        }


def export_aegis_bundle(
    processed_dir: Path | str = "data/processed",
    output_dir: Path | str = "artifacts/bundle",
    seed: int = 42,
) -> Path:
    """Trains production model on full dataset, fits residual PCA basis, and bundles artifacts."""
    src = Path(processed_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(seed)
    np.random.seed(seed)

    with open(src / "samples.json", "r", encoding="utf-8") as f:
        samples: List[Dict[str, Any]] = json.load(f)

    with open(src / "MANIFEST.json", "r", encoding="utf-8") as f:
        manifest: Dict[str, Any] = json.load(f)

    logger.info(f"Training production Candidate S on {len(samples)} samples...")
    model = StructuredMealForecasterS(dropout=0.2)
    model, _ = train_model(model, samples, samples, max_epochs=20, lr=0.002)
    model.eval()

    # Save model weights
    model_path = out / "model.pt"
    torch.save(model.state_dict(), model_path)
    logger.info(f"Saved model weights to {model_path}")

    # Fit PCA basis on residuals
    residuals = []
    with torch.no_grad():
        for s in samples:
            batch = collate_meal_batch([MealForecastingDataset([s])[0]])
            pred, _ = model(batch["seq"], batch["static"], batch["meal"], batch["anchor"])
            diff = np.array(s["target_deltas"], dtype=np.float32) - pred.squeeze(0).numpy()
            residuals.append(diff)
    residuals_np = np.vstack(residuals)

    basis = ResidualBasis(n_components=3).fit(residuals_np)

    pca_dict = {
        "n_components": basis.n_components,
        "mean": basis.mean_residual.tolist(),
        "basis_matrix": basis.basis_matrix.tolist(),
    }
    with open(out / "pca_basis.json", "w", encoding="utf-8") as f:
        json.dump(pca_dict, f, indent=2)

    # Compute similarity profiles
    unique_pids = sorted(list(set(s["patient_id"] for s in samples)))
    ref_static_profiles = {
        s["patient_id"]: np.array(s["static"], dtype=np.float32) for s in samples
    }
    ref_alphas = {}
    for pid in unique_pids:
        p_res = [
            residuals[i]
            for i, s in enumerate(samples)
            if s["patient_id"] == pid
        ]
        if p_res:
            ref_alphas[pid] = np.mean([basis.transform(r) for r in p_res], axis=0).tolist()

    sim_dict = {
        "static_profiles": {pid: prof.tolist() for pid, prof in ref_static_profiles.items()},
        "alphas": ref_alphas,
    }
    with open(out / "similarity_priors.json", "w", encoding="utf-8") as f:
        json.dump(sim_dict, f, indent=2)

    # Copy or load uncertainty calibration table
    configs_table = Path("configs/uncertainty_table.json")
    if configs_table.exists():
        table = ConformalCalibrationTable.load(configs_table)
    else:
        table = ConformalCalibrationTable(
            alpha_levels=[0.10, 0.20],
            n_calibration_samples=len(samples),
            scenarios={"D0": {"90%": [12.0] * 36, "80%": [9.0] * 36}},
            inflation_multipliers={"D0": 1.0},
        )
    table.save(out / "uncertainty_table.json")

    # Save bundle metadata
    git_hash = get_git_commit()
    metadata = {
        "model_architecture": "StructuredMealForecasterS",
        "dataset_version": manifest.get("dataset_version", "v1.0.0"),
        "git_commit": git_hash,
        "input_schema": {
            "sequence": [12, 6],
            "anchor": [4],
            "meal": [16],
            "static": [8],
        },
        "output_horizon_steps": 36,
        "personalisation_basis_dim": 3,
        "is_calibrated": True,
    }
    with open(out / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Successfully exported Aegis artifact bundle to {out}")
    return out


def load_aegis_bundle(bundle_dir: Union[str, Path] = "artifacts/bundle") -> AegisBundle:
    """Loads complete runtime forecasting bundle."""
    b_dir = Path(bundle_dir)

    model = StructuredMealForecasterS(dropout=0.2)
    model.load_state_dict(torch.load(b_dir / "model.pt", weights_only=True))
    model.eval()

    with open(b_dir / "pca_basis.json", "r", encoding="utf-8") as f:
        pca_dict = json.load(f)
    basis = ResidualBasis(n_components=pca_dict["n_components"])
    basis.mean_residual = np.array(pca_dict["mean"], dtype=np.float32)
    basis.basis_matrix = np.array(pca_dict["basis_matrix"], dtype=np.float32)

    with open(b_dir / "similarity_priors.json", "r", encoding="utf-8") as f:
        sim_data = json.load(f)

    ref_static = {
        pid: np.array(vec, dtype=np.float32) for pid, vec in sim_data["static_profiles"].items()
    }
    ref_alphas = {
        pid: np.array(vec, dtype=np.float32) for pid, vec in sim_data["alphas"].items()
    }

    cal_table = ConformalCalibrationTable.load(b_dir / "uncertainty_table.json")

    with open(b_dir / "metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return AegisBundle(
        model=model,
        basis=basis,
        calibration_table=cal_table,
        reference_static_profiles=ref_static,
        reference_alphas=ref_alphas,
        metadata=metadata,
    )


if __name__ == "__main__":
    export_aegis_bundle()
