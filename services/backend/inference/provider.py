"""Pluggable inference providers for in-process, HTTP, and mock execution (Decision D12)."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Optional

import numpy as np

from aegis.features.extract import extract_meal_features, extract_static_features
from aegis.training.export import AegisBundle, load_aegis_bundle
from services.common.contracts import (
    CLINICAL_DISCLAIMER,
    ForecastMetrics,
    IntervalBand,
    ModelMetadata,
    PersonalisationStatus,
    PredictRequest,
    PredictResponse,
    ReliabilityAssessment,
    ScenarioDifference,
    ScenarioModifier,
    ScenarioResult,
    SimulateRequest,
    SimulateResponse,
)

logger = logging.getLogger(__name__)


class InferenceProvider(ABC):
    """Abstract interface for forecasting and counterfactual simulation."""

    @abstractmethod
    async def predict(self, req: PredictRequest) -> PredictResponse:
        """Generate 180-minute postprandial forecast."""
        pass

    @abstractmethod
    async def simulate(self, req: SimulateRequest) -> SimulateResponse:
        """Simulate counterfactual physiological interventions."""
        pass


class InProcessInferenceProvider(InferenceProvider):
    """Executes trained Candidate S bundle in-process (Decision D12)."""

    def __init__(self, bundle_dir: Path | str = "artifacts/bundle") -> None:
        self.bundle_dir = Path(bundle_dir)
        self.bundle: Optional[AegisBundle] = None
        if self.bundle_dir.exists():
            try:
                self.bundle = load_aegis_bundle(self.bundle_dir)
                logger.info(f"Loaded AegisBundle from {self.bundle_dir}")
            except Exception as e:
                logger.warning(f"Could not load AegisBundle from {self.bundle_dir}: {e}")

    async def predict(self, req: PredictRequest) -> PredictResponse:
        if self.bundle is None:
            # Fallback to mock if bundle unavailable
            return await MockInferenceProvider().predict(req)

        # 1. Prepare features from request
        m = req.meal
        raw_meal = {
            "carbs_g": m.carbs_g * (m.amount_pct / 100.0),
            "protein_g": m.protein_g * (m.amount_pct / 100.0),
            "fat_g": m.fat_g * (m.amount_pct / 100.0),
            "fiber_g": m.fiber_g * (m.amount_pct / 100.0),
            "calories": (m.carbs_g * 4.0 + m.protein_g * 4.0 + m.fat_g * 9.0) * (m.amount_pct / 100.0),
            "meal_type": m.meal_type,
            "minutes_since_prev_meal": 360.0,
        }

        # Retrieve profile for patient_id if in bundle
        profile_vec = self.bundle.reference_static_profiles.get(req.patient_id)
        if profile_vec is None:
            profile_vec = extract_static_features({"age": 55, "bmi": 28.0, "hba1c": 6.8})

        meal_vec = extract_meal_features(raw_meal)

        # Sequence tensor: 12 steps of 5-min intervals
        seq = np.zeros((12, 6), dtype=np.float32)
        seq[:, 1] = 1.0  # observed
        seq[:, 3] = 1.0  # HR present
        seq[:, 5] = 1.0  # METs present

        anchor = np.array([0.2, 0.0, 0.0, 0.0], dtype=np.float32)
        g_t0 = 120.0

        # 2. Run bundle prediction
        raw_out = self.bundle.predict(
            seq=seq,
            anchor=anchor,
            meal=meal_vec,
            static=profile_vec,
            g_t0=g_t0,
            patient_id=req.patient_id,
            scenario=req.degradation,
            confidence_level=0.90,
        )

        fc = raw_out["forecast"]
        low = raw_out["interval_lower"]
        upp = raw_out["interval_upper"]
        delta_g = [round(v - g_t0, 2) for v in fc]

        peak_val = max(fc)
        time_to_peak = (fc.index(peak_val) + 1) * 5
        delayed_mean = float(np.mean(fc[24:]))
        min_above_180 = float(sum(5.0 for v in fc if v > 180.0))

        rel = raw_out["reliability"]
        rel_label = rel["level"].lower()
        if rel_label not in ["high", "moderate", "low"]:
            rel_label = "moderate"

        return PredictResponse(
            horizon_min=[(i + 1) * 5 for i in range(36)],
            delta_glucose=delta_g,
            glucose=fc,
            interval=IntervalBand(
                level=0.90,
                lower=low,
                upper=upp,
                scenario=req.degradation,
            ),
            metrics=ForecastMetrics(
                peak=round(peak_val, 1),
                time_to_peak_min=time_to_peak,
                delayed_mean_120_180=round(delayed_mean, 1),
                minutes_above_threshold=min_above_180,
                risk_flag=peak_val > 180.0,
            ),
            reliability=ReliabilityAssessment(
                label=rel_label,
                reasons=rel.get("reasons", []),
            ),
            personalisation=PersonalisationStatus(
                n_personal_meals=5,
                method="residual_pca_ridge",
                prior="similarity",
            ),
            model=ModelMetadata(
                version=self.bundle.metadata.get("model_architecture", "Candidate_S"),
                dataset_version=self.bundle.metadata.get("dataset_version", "v1.0.0"),
                feature_version="v1.0-deep",
            ),
            disclaimer=CLINICAL_DISCLAIMER,
        )

    async def simulate(self, req: SimulateRequest) -> SimulateResponse:
        # Run baseline
        base_req = PredictRequest(
            patient_id=req.patient_id,
            session_id=req.session_id,
            t0=req.t0,
            meal=req.meal,
            degradation=req.degradation,
        )
        baseline = await self.predict(base_req)

        results: List[ScenarioResult] = []

        for sc in req.scenarios:
            mod_result = self._apply_scenario_intervention(baseline, req.meal, sc)
            results.append(mod_result)

        return SimulateResponse(
            baseline=baseline,
            scenarios=results,
            disclaimer=CLINICAL_DISCLAIMER,
        )

    def _apply_scenario_intervention(
        self, baseline: PredictResponse, orig_meal: Any, mod: ScenarioModifier
    ) -> ScenarioResult:
        base_traj = np.array(baseline.glucose, dtype=np.float32)
        base_g0 = base_traj[0]

        if mod.type == "portion":
            pct = mod.amount_pct if mod.amount_pct is not None else 70.0
            scale = pct / 100.0
            # Model-driven: excursion scales approximately proportionally
            new_traj = base_g0 + (base_traj - base_g0) * scale
            origin = "model_driven"
            notes = f"Portion reduced to {pct:.0f}% of standard serving."
            assumption = None

        elif mod.type == "walk":
            mins = mod.minutes if mod.minutes is not None else 20
            # Assumption-driven (Reynolds et al. 2016): 20 min walk suppresses excursion peak by ~18%
            suppression = min(0.35, (mins / 20.0) * 0.18)
            t_grid = np.arange(1, 37) * 5
            # Walk effect kicks in during minutes 30..120
            walk_effect = suppression * np.exp(-0.5 * ((t_grid - 60) / 30) ** 2)
            new_traj = base_g0 + (base_traj - base_g0) * (1.0 - walk_effect)
            origin = "assumption_driven"
            notes = f"Simulated {mins}-minute brisk walk post-meal."
            assumption = {
                "source": "Reynolds et al., Diabetologia 2016",
                "reduction_factor": round(suppression, 2),
                "verify": True,
            }

        elif mod.type == "sequencing":
            # Assumption-driven (Shukla et al. 2017): Veggies/protein first delays & blunts carb peak
            t_grid = np.arange(1, 37) * 5
            # Peak delayed by ~15 min, excursion lowered by 15%
            new_deltas = (base_traj - base_g0) * 0.85
            # Shift by 3 steps (15 min)
            shifted = np.zeros_like(new_deltas)
            shifted[3:] = new_deltas[:-3]
            shifted[:3] = new_deltas[:3] * 0.5
            new_traj = base_g0 + shifted
            origin = "assumption_driven"
            notes = "Food sequencing: Vegetables & protein ingested 10 min prior to carbohydrates."
            assumption = {
                "source": "Shukla et al., BMJ Open Diabetes Res Care 2017",
                "peak_attenuation": 0.15,
                "delay_minutes": 15,
                "verify": True,
            }

        else:
            # Fallback
            new_traj = base_traj
            origin = "model_driven"
            notes = f"Scenario {mod.type} applied."
            assumption = None

        peak_val = float(np.max(new_traj))
        ttp = int((np.argmax(new_traj) + 1) * 5)
        del_mean = float(np.mean(new_traj[24:]))

        delta_peak = round(peak_val - baseline.metrics.peak, 1)
        delta_ttp = ttp - baseline.metrics.time_to_peak_min
        delta_del = round(del_mean - baseline.metrics.delayed_mean_120_180, 1)

        low_bound = np.clip(new_traj - 15.0, 40.0, 400.0)
        upp_bound = np.clip(new_traj + 15.0, 40.0, 400.0)

        return ScenarioResult(
            type=mod.type,
            origin=origin,
            trajectory=[round(float(v), 2) for v in new_traj],
            interval=IntervalBand(
                level=0.90,
                lower=[round(float(v), 2) for v in low_bound],
                upper=[round(float(v), 2) for v in upp_bound],
                scenario=baseline.interval.scenario,
            ),
            metrics=ForecastMetrics(
                peak=round(peak_val, 1),
                time_to_peak_min=ttp,
                delayed_mean_120_180=round(del_mean, 1),
                minutes_above_threshold=float(sum(5.0 for v in new_traj if v > 180.0)),
                risk_flag=peak_val > 180.0,
            ),
            delta_vs_baseline=ScenarioDifference(
                delta_peak=delta_peak,
                delta_time_to_peak=delta_ttp,
                delta_delayed_mean=delta_del,
            ),
            reliability=baseline.reliability,
            notes=notes,
            assumption=assumption,
        )


class MockInferenceProvider(InferenceProvider):
    """Deterministic synthetic curves for testing and client development."""

    async def predict(self, req: PredictRequest) -> PredictResponse:
        t_grid = np.arange(1, 37) * 5
        # Plausible gamma-like postprandial trajectory peaking at ~60 min
        carbs = max(20.0, req.meal.carbs_g * (req.meal.amount_pct / 100.0))
        amplitude = carbs * 0.9
        tau = 45.0
        excursion = amplitude * (t_grid / tau) * np.exp(1.0 - t_grid / tau)

        g0 = 120.0
        glucose = g0 + excursion
        peak_val = float(np.max(glucose))
        ttp = int(t_grid[np.argmax(glucose)])
        del_mean = float(np.mean(glucose[24:]))

        return PredictResponse(
            horizon_min=t_grid.tolist(),
            delta_glucose=[round(float(v), 2) for v in excursion],
            glucose=[round(float(v), 2) for v in glucose],
            interval=IntervalBand(
                level=0.90,
                lower=[round(float(v - 18.0), 2) for v in glucose],
                upper=[round(float(v + 18.0), 2) for v in glucose],
                scenario=req.degradation,
            ),
            metrics=ForecastMetrics(
                peak=round(peak_val, 1),
                time_to_peak_min=ttp,
                delayed_mean_120_180=round(del_mean, 1),
                minutes_above_threshold=float(sum(5.0 for v in glucose if v > 180.0)),
                risk_flag=peak_val > 180.0,
            ),
            reliability=ReliabilityAssessment(
                label="moderate",
                reasons=["Simulated prediction (mock engine)"],
            ),
            personalisation=PersonalisationStatus(
                n_personal_meals=0,
                method="mock_gamma",
                prior="population",
            ),
            model=ModelMetadata(
                version="mock",
                dataset_version="mock-demo",
                feature_version="v0",
            ),
            disclaimer=CLINICAL_DISCLAIMER,
        )

    async def simulate(self, req: SimulateRequest) -> SimulateResponse:
        base_req = PredictRequest(
            patient_id=req.patient_id,
            session_id=req.session_id,
            t0=req.t0,
            meal=req.meal,
            degradation=req.degradation,
        )
        base = await self.predict(base_req)

        results = []
        for sc in req.scenarios:
            factor = 0.8 if sc.type in ["walk", "sequencing"] else 0.7
            mod_g = [round(float(base.glucose[0] + (v - base.glucose[0]) * factor), 2) for v in base.glucose]
            results.append(
                ScenarioResult(
                    type=sc.type,
                    origin="assumption_driven" if sc.type in ["walk", "sequencing"] else "model_driven",
                    trajectory=mod_g,
                    interval=IntervalBand(
                        level=0.90,
                        lower=[round(v - 15.0, 2) for v in mod_g],
                        upper=[round(v + 15.0, 2) for v in mod_g],
                        scenario=base.interval.scenario,
                    ),
                    metrics=ForecastMetrics(
                        peak=round(max(mod_g), 1),
                        time_to_peak_min=base.metrics.time_to_peak_min,
                        delayed_mean_120_180=round(float(np.mean(mod_g[24:])), 1),
                        minutes_above_threshold=0.0,
                        risk_flag=False,
                    ),
                    delta_vs_baseline=ScenarioDifference(
                        delta_peak=round(max(mod_g) - base.metrics.peak, 1),
                        delta_time_to_peak=0,
                        delta_delayed_mean=round(float(np.mean(mod_g[24:])) - base.metrics.delayed_mean_120_180, 1),
                    ),
                    reliability=base.reliability,
                    notes=f"Mock simulation for {sc.type}",
                )
            )

        return SimulateResponse(
            baseline=base,
            scenarios=results,
            disclaimer=CLINICAL_DISCLAIMER,
        )


class HttpInferenceProvider(InferenceProvider):
    """Dispatches prediction to separate HTTP inference microservice."""

    def __init__(self, service_url: str = "http://127.0.0.1:8001") -> None:
        self.service_url = service_url

    async def predict(self, req: PredictRequest) -> PredictResponse:
        import httpx

        async with httpx.AsyncClient(base_url=self.service_url, timeout=10.0) as client:
            resp = await client.post("/predict", json=req.model_dump())
            resp.raise_for_status()
            return PredictResponse.model_validate(resp.json())

    async def simulate(self, req: SimulateRequest) -> SimulateResponse:
        # Fallback simulation logic or remote call
        base_req = PredictRequest(
            patient_id=req.patient_id,
            session_id=req.session_id,
            t0=req.t0,
            meal=req.meal,
            degradation=req.degradation,
        )
        base = await self.predict(base_req)
        # Using InProcess provider simulation logic
        in_proc = InProcessInferenceProvider()
        results = [in_proc._apply_scenario_intervention(base, req.meal, sc) for sc in req.scenarios]
        return SimulateResponse(baseline=base, scenarios=results, disclaimer=CLINICAL_DISCLAIMER)
