"""Pluggable inference providers for in-process, HTTP, and mock execution (Decision D12)."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    """Executes trained Candidate S bundle in-process with real dynamic tensors (Decision D12)."""

    def __init__(self, bundle_dir: Path | str = "artifacts/bundle") -> None:
        self.bundle_dir = Path(bundle_dir)
        self.bundle: Optional[AegisBundle] = None
        self._samples_cache: Optional[List[Dict[str, Any]]] = None

        if self.bundle_dir.exists():
            try:
                self.bundle = load_aegis_bundle(self.bundle_dir)
                logger.info(f"Loaded AegisBundle from {self.bundle_dir}")
            except Exception as e:
                logger.warning(f"Could not load AegisBundle from {self.bundle_dir}: {e}")

        # Pre-load samples to compute chronological residuals for few-shot adaptation
        samples_path = Path("data/processed/samples.json")
        if not samples_path.exists():
            samples_path = Path("data/demo/samples.json")
        if samples_path.exists():
            try:
                with open(samples_path, "r", encoding="utf-8") as f:
                    self._samples_cache = json.load(f)
                logger.info(f"Loaded {len(self._samples_cache)} samples for chronological adaptation.")
            except Exception as e:
                logger.warning(f"Failed to load samples for adaptation: {e}")

    def _get_chronological_residuals(self, patient_id: str, current_t0: str) -> List[np.ndarray]:
        """Collects empirical model residuals for all completed meals prior to current_t0."""
        if not self._samples_cache or not self.bundle:
            return []

        residuals = []
        for s in self._samples_cache:
            if s.get("patient_id") == patient_id:
                # Meal occurred before current prediction timestamp
                s_t0 = s.get("t0", "")
                if s_t0 and s_t0 < current_t0:
                    y_true = np.array(s.get("target_deltas", []), dtype=np.float32)
                    if len(y_true) == 36:
                        # Forward pass to get unadapted backbone prediction
                        try:
                            seq = np.array(s["seq"], dtype=np.float32)
                            anchor = np.array(s["anchor"], dtype=np.float32)
                            meal = np.array(s["meal"], dtype=np.float32)
                            static = np.array(s["static"], dtype=np.float32)
                            pred_raw = self.bundle.predict(
                                seq=seq,
                                anchor=anchor,
                                meal=meal,
                                static=static,
                                g_t0=float(s.get("g_t0", 120.0)),
                                patient_id=patient_id,
                                earlier_residuals=[],  # unadapted
                            )
                            fc = np.array(pred_raw["forecast"], dtype=np.float32)
                            pred_deltas = fc - float(s.get("g_t0", 120.0))
                            res = y_true - pred_deltas
                            residuals.append(res)
                        except Exception:
                            pass
        return residuals

    async def predict(self, req: PredictRequest) -> PredictResponse:
        if self.bundle is None:
            # Fallback to mock if bundle unavailable
            return await MockInferenceProvider().predict(req)

        # 1. Prepare meal features from request
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
        meal_vec = extract_meal_features(raw_meal)

        # 2. Retrieve patient profile
        profile_vec = self.bundle.reference_static_profiles.get(req.patient_id)
        if profile_vec is None:
            profile_vec = extract_static_features({"age": 55, "bmi": 28.0, "hba1c": 6.8})

        # 3. Baseline glucose g(t0)
        g_t0 = req.g_t0 if req.g_t0 is not None else 120.0

        # 4. Construct dynamic 60-min sequence tensor & anchor vector from real telemetry
        seq = np.zeros((12, 6), dtype=np.float32)
        anchor = np.zeros(4, dtype=np.float32)

        pts = req.retrospective_sequence or []
        if pts:
            # Ensure window is 12 steps (pad front if needed)
            while len(pts) < 12 and len(pts) > 0:
                pts = [pts[0]] + pts

            for k in range(min(12, len(pts))):
                p = pts[k]
                p_g = float(p.get("glucose", g_t0))
                p_hr = float(p.get("hr", 75.0))
                p_mets = float(p.get("mets", 1.0))
                seq[k, 0] = (p_g - g_t0) / 50.0
                seq[k, 1] = 0.0 if p.get("glucose_missing", False) else 1.0
                seq[k, 2] = (p_hr - 75.0) / 30.0
                seq[k, 3] = 0.0 if p.get("hr_missing", False) else 1.0
                seq[k, 4] = (p_mets - 1.0) / 3.0
                seq[k, 5] = 0.0 if p.get("mets_missing", False) else 1.0

            anchor[0] = g_t0 / 200.0
            g_minus15 = float(pts[-3].get("glucose", g_t0)) if len(pts) >= 3 else g_t0
            anchor[1] = (g_t0 - g_minus15) / 15.0
            g_minus30 = float(pts[-6].get("glucose", g_t0)) if len(pts) >= 6 else g_t0
            anchor[2] = (g_t0 - g_minus30) / 30.0
            g_window = [float(x.get("glucose", g_t0)) for x in pts]
            anchor[3] = float(np.std(g_window)) / 50.0
        else:
            # Fallback nominal sequence if no telemetry buffer passed
            seq[:, 1] = 1.0
            seq[:, 3] = 1.0
            seq[:, 5] = 1.0
            anchor[0] = g_t0 / 200.0

        # 5. Extract chronological residuals for few-shot Ridge personalisation
        earlier_residuals = self._get_chronological_residuals(req.patient_id, req.t0)
        n_meals = len(earlier_residuals)

        # 6. Run Candidate S bundle prediction
        raw_out = self.bundle.predict(
            seq=seq,
            anchor=anchor,
            meal=meal_vec,
            static=profile_vec,
            g_t0=g_t0,
            patient_id=req.patient_id,
            earlier_residuals=earlier_residuals,
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

        prior_desc = "similarity" if n_meals == 0 else f"residual_pca_ridge (K={n_meals})"

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
                n_personal_meals=n_meals,
                method="residual_pca_ridge",
                prior=prior_desc,
            ),
            model=ModelMetadata(
                version=self.bundle.metadata.get("model_architecture", "Candidate_S"),
                dataset_version=self.bundle.metadata.get("dataset_version", "v1.0.0"),
                feature_version="v1.0-deep",
            ),
            disclaimer=CLINICAL_DISCLAIMER,
        )

    async def simulate(self, req: SimulateRequest) -> SimulateResponse:
        """Executes real neural what-if recomputation and literature-grounded modifiers."""
        baseline_pred_req = PredictRequest(
            patient_id=req.patient_id,
            session_id=req.session_id,
            t0=req.t0,
            meal=req.meal,
            degradation=req.degradation,
        )
        baseline = await self.predict(baseline_pred_req)

        results: List[ScenarioResult] = []
        for mod in req.scenarios:
            res = await self._run_single_scenario(req, baseline, mod)
            results.append(res)

        return SimulateResponse(
            baseline=baseline,
            scenarios=results,
            disclaimer=CLINICAL_DISCLAIMER,
        )

    async def _run_single_scenario(
        self, req: SimulateRequest, baseline: PredictResponse, mod: ScenarioModifier
    ) -> ScenarioResult:
        base_traj = np.array(baseline.glucose)
        base_g0 = base_traj[0] - baseline.delta_glucose[0] if baseline.delta_glucose else base_traj[0]

        if mod.type == "portion":
            # Model-driven: re-run neural forward pass with modified portion
            amt = mod.amount_pct if mod.amount_pct is not None else 100.0
            mod_meal = req.meal.model_copy(update={"amount_pct": amt})
            mod_req = PredictRequest(
                patient_id=req.patient_id,
                session_id=req.session_id,
                t0=req.t0,
                meal=mod_meal,
                degradation=req.degradation,
            )
            sim_pred = await self.predict(mod_req)
            return ScenarioResult(
                type=mod.type,
                origin="model_driven",
                trajectory=sim_pred.glucose,
                interval=sim_pred.interval,
                metrics=sim_pred.metrics,
                delta_vs_baseline=ScenarioDifference(
                    delta_peak=round(sim_pred.metrics.peak - baseline.metrics.peak, 1),
                    delta_time_to_peak=sim_pred.metrics.time_to_peak_min - baseline.metrics.time_to_peak_min,
                    delta_delayed_mean=round(sim_pred.metrics.delayed_mean_120_180 - baseline.metrics.delayed_mean_120_180, 1),
                ),
                reliability=sim_pred.reliability,
                notes=f"Model-driven simulation: portion adjusted to {amt}% via Candidate S dual-gamma head.",
                assumption=None,
            )

        elif mod.type == "fat":
            # Model-driven: re-run neural forward pass with modified fat
            delta_fat = mod.delta_g if mod.delta_g is not None else 15.0
            new_fat = max(0.0, req.meal.fat_g + delta_fat)
            mod_meal = req.meal.model_copy(update={"fat_g": new_fat})
            mod_req = PredictRequest(
                patient_id=req.patient_id,
                session_id=req.session_id,
                t0=req.t0,
                meal=mod_meal,
                degradation=req.degradation,
            )
            sim_pred = await self.predict(mod_req)
            return ScenarioResult(
                type=mod.type,
                origin="model_driven",
                trajectory=sim_pred.glucose,
                interval=sim_pred.interval,
                metrics=sim_pred.metrics,
                delta_vs_baseline=ScenarioDifference(
                    delta_peak=round(sim_pred.metrics.peak - baseline.metrics.peak, 1),
                    delta_time_to_peak=sim_pred.metrics.time_to_peak_min - baseline.metrics.time_to_peak_min,
                    delta_delayed_mean=round(sim_pred.metrics.delayed_mean_120_180 - baseline.metrics.delayed_mean_120_180, 1),
                ),
                reliability=sim_pred.reliability,
                notes=f"Model-driven simulation: dietary fat altered by {delta_fat:+.1f}g, slowing gastric emptying.",
                assumption=None,
            )

        elif mod.type == "walk":
            # Assumption-driven (Reynolds et al. 2016): 15-30m walk reduces peak excursion by ~20%
            mins = mod.minutes or 15
            suppression = 0.20 if mins >= 15 else 0.10
            new_deltas = np.array(baseline.delta_glucose) * (1.0 - suppression)
            new_traj = np.clip(base_g0 + new_deltas, 40.0, 400.0)

            peak_val = float(np.max(new_traj))
            ttp = int((np.argmax(new_traj) + 1) * 5)
            del_mean = float(np.mean(new_traj[24:]))

            return ScenarioResult(
                type=mod.type,
                origin="assumption_driven",
                trajectory=[round(float(v), 2) for v in new_traj],
                interval=IntervalBand(
                    level=0.90,
                    lower=[round(float(v - 15.0), 2) for v in new_traj],
                    upper=[round(float(v + 15.0), 2) for v in new_traj],
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
                    delta_peak=round(peak_val - baseline.metrics.peak, 1),
                    delta_time_to_peak=ttp - baseline.metrics.time_to_peak_min,
                    delta_delayed_mean=round(del_mean - baseline.metrics.delayed_mean_120_180, 1),
                ),
                reliability=baseline.reliability,
                notes=f"Simulated {mins}-minute brisk walk post-meal attenuating glycemic peak.",
                assumption={
                    "source": "Reynolds et al., Diabetologia 2016",
                    "reduction_factor": round(suppression, 2),
                    "verify": True,
                },
            )

        elif mod.type == "sequencing":
            # Assumption-driven (Shukla et al. 2017): Veggies/protein first delays & blunts carb peak
            new_deltas = np.array(baseline.delta_glucose) * 0.85
            shifted = np.zeros_like(new_deltas)
            shifted[3:] = new_deltas[:-3]
            shifted[:3] = new_deltas[:3] * 0.5
            new_traj = np.clip(base_g0 + shifted, 40.0, 400.0)

            peak_val = float(np.max(new_traj))
            ttp = int((np.argmax(new_traj) + 1) * 5)
            del_mean = float(np.mean(new_traj[24:]))

            return ScenarioResult(
                type=mod.type,
                origin="assumption_driven",
                trajectory=[round(float(v), 2) for v in new_traj],
                interval=IntervalBand(
                    level=0.90,
                    lower=[round(float(v - 15.0), 2) for v in new_traj],
                    upper=[round(float(v + 15.0), 2) for v in new_traj],
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
                    delta_peak=round(peak_val - baseline.metrics.peak, 1),
                    delta_time_to_peak=ttp - baseline.metrics.time_to_peak_min,
                    delta_delayed_mean=round(del_mean - baseline.metrics.delayed_mean_120_180, 1),
                ),
                reliability=baseline.reliability,
                notes="Food sequencing: Vegetables & protein ingested 10 min prior to carbohydrates.",
                assumption={
                    "source": "Shukla et al., BMJ Open Diabetes Res Care 2017",
                    "peak_attenuation": 0.15,
                    "delay_minutes": 15,
                    "verify": True,
                },
            )

        else:
            return ScenarioResult(
                type=mod.type,
                origin="model_driven",
                trajectory=baseline.glucose,
                interval=baseline.interval,
                metrics=baseline.metrics,
                delta_vs_baseline=ScenarioDifference(delta_peak=0.0, delta_time_to_peak=0, delta_delayed_mean=0.0),
                reliability=baseline.reliability,
                notes=f"Scenario {mod.type} maintained baseline.",
                assumption=None,
            )


class HttpInferenceProvider(InferenceProvider):
    """Delegates inference over HTTP to standalone container microservice."""

    def __init__(self, service_url: str = "http://127.0.0.1:8001") -> None:
        self.service_url = service_url.rstrip("/")

    async def predict(self, req: PredictRequest) -> PredictResponse:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{self.service_url}/predict", json=req.model_dump())
            resp.raise_for_status()
            return PredictResponse.model_validate(resp.json())

    async def simulate(self, req: SimulateRequest) -> SimulateResponse:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{self.service_url}/simulate", json=req.model_dump())
            resp.raise_for_status()
            return SimulateResponse.model_validate(resp.json())


class MockInferenceProvider(InferenceProvider):
    """Deterministic synthetic curves for testing and client development."""

    async def predict(self, req: PredictRequest) -> PredictResponse:
        t_grid = np.arange(1, 37) * 5
        carbs = max(20.0, req.meal.carbs_g * (req.meal.amount_pct / 100.0))
        amplitude = carbs * 0.9
        tau = 45.0
        excursion = amplitude * (t_grid / tau) * np.exp(1.0 - t_grid / tau)

        g0 = req.g_t0 if req.g_t0 is not None else 120.0
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
                label="moderate" if req.degradation != "D0" else "high",
                reasons=[f"Scenario: {req.degradation}"],
            ),
            personalisation=PersonalisationStatus(
                n_personal_meals=0,
                method="residual_pca_ridge",
                prior="similarity",
            ),
            model=ModelMetadata(
                version="MockProvider",
                dataset_version="mock-v1",
                feature_version="mock-v1",
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
            g_t0=req.meal.carbs_g,
        )
        baseline = await self.predict(base_req)
        return SimulateResponse(
            baseline=baseline,
            scenarios=[],
            disclaimer=CLINICAL_DISCLAIMER,
        )
