"""Pluggable inference providers for in-process, HTTP, and mock execution (Decision D12)."""

from __future__ import annotations

import datetime
import json
import logging
import math
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch

from aegis.features.extract import extract_meal_features, extract_static_features
from aegis.models.pharmacology import compute_insulin_effect, estimate_isf
from aegis.training.export import AegisBundle, load_aegis_bundle
from aegis.uncertainty.conformal import compute_conformal_intervals
from services.common.contracts import (
    CLINICAL_DISCLAIMER,
    ForecastMetrics,
    InsulinInput,
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

    def __init__(
        self,
        bundle_dir: Path | str = "artifacts/bundle",
        db_session_factory: Optional[Any] = None,
    ) -> None:
        self.bundle_dir = Path(bundle_dir)
        self.bundle: Optional[AegisBundle] = None
        self._samples_cache: Optional[List[Dict[str, Any]]] = None
        self.db_session_factory = db_session_factory

        if self.db_session_factory is None:
            try:
                from services.backend.db import SessionLocal

                self.db_session_factory = SessionLocal
            except Exception:
                self.db_session_factory = None

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
                logger.info(
                    f"Loaded {len(self._samples_cache)} samples for chronological adaptation."
                )
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

    async def predict(
        self,
        req: PredictRequest,
        tau_fast_override: Optional[float] = None,
        delay_override: Optional[float] = None,
        phi_override: Optional[float] = None,
    ) -> PredictResponse:
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
            "calories": (m.carbs_g * 4.0 + m.protein_g * 4.0 + m.fat_g * 9.0)
            * (m.amount_pct / 100.0),
            "meal_type": m.meal_type,
            "minutes_since_prev_meal": 360.0,
        }
        meal_vec = extract_meal_features(raw_meal)

        # 2. Retrieve patient profile and clinical priors from reference or DB
        profile_vec = self.bundle.reference_static_profiles.get(req.patient_id)
        patient_record: Optional[Dict[str, Any]] = None

        if self.db_session_factory:
            try:
                with self.db_session_factory() as db:
                    from services.backend.models import PatientModel

                    p = (
                        db.query(PatientModel)
                        .filter(PatientModel.patient_id == req.patient_id)
                        .first()
                    )
                    if p:
                        patient_record = p.to_dict()
            except Exception as e:
                logger.warning(f"Failed to query patient {req.patient_id} from DB: {e}")

        if profile_vec is None:
            if patient_record and "profile" in patient_record:
                profile_vec = extract_static_features(patient_record["profile"])
            else:
                profile_vec = extract_static_features({"age": 55, "bmi": 28.0, "hba1c": 6.8})

        pts = req.retrospective_sequence or []
        if not pts and self.db_session_factory:
            try:
                with self.db_session_factory() as db:
                    from services.backend.models import ObservationModel

                    t0_clean = str(req.t0).replace("Z", "+00:00")
                    try:
                        t0_dt = datetime.datetime.fromisoformat(t0_clean)
                        db_obs = (
                            db.query(ObservationModel)
                            .filter(
                                ObservationModel.patient_id == req.patient_id,
                                ObservationModel.ts <= t0_dt,
                            )
                            .order_by(ObservationModel.ts.desc())
                            .limit(12)
                            .all()
                        )
                    except Exception:
                        db_obs = (
                            db.query(ObservationModel)
                            .filter(ObservationModel.patient_id == req.patient_id)
                            .order_by(ObservationModel.ts.desc())
                            .limit(12)
                            .all()
                        )
                    if db_obs:
                        pts = [o.to_dict() for o in reversed(db_obs)]
            except Exception as e:
                logger.debug(f"Could not load telemetry from DB for {req.patient_id}: {e}")

        # 3. Baseline glucose g(t0)
        g_t0 = req.g_t0
        if g_t0 is None:
            if pts and pts[-1].get("glucose") is not None:
                g_t0 = float(pts[-1]["glucose"])
            elif patient_record and patient_record.get("profile", {}).get("fasting_glucose"):
                g_t0 = float(patient_record["profile"]["fasting_glucose"])
            else:
                g_t0 = 120.0

        # 4. Construct dynamic 60-min sequence tensor & anchor vector from real telemetry
        seq = np.zeros((12, 6), dtype=np.float32)
        anchor = np.zeros(4, dtype=np.float32)

        if pts:
            # Ensure window is 12 steps (pad front if needed)
            while len(pts) < 12 and len(pts) > 0:
                pts = [pts[0]] + pts

            for k in range(min(12, len(pts))):
                p = pts[k]
                raw_g = p.get("glucose")
                raw_hr = p.get("hr")
                raw_mets = p.get("mets")

                g_missing = p.get("glucose_missing", False) or raw_g is None
                hr_missing = p.get("hr_missing", False) or raw_hr is None
                mets_missing = p.get("mets_missing", False) or raw_mets is None

                try:
                    p_g = float(raw_g) if (raw_g is not None and not math.isnan(float(raw_g))) else g_t0
                except (ValueError, TypeError):
                    p_g = g_t0
                    g_missing = True

                try:
                    p_hr = float(raw_hr) if (raw_hr is not None and not math.isnan(float(raw_hr))) else 75.0
                except (ValueError, TypeError):
                    p_hr = 75.0
                    hr_missing = True

                try:
                    p_mets = float(raw_mets) if (raw_mets is not None and not math.isnan(float(raw_mets))) else 1.0
                except (ValueError, TypeError):
                    p_mets = 1.0
                    mets_missing = True

                seq[k, 0] = (p_g - g_t0) / 50.0
                seq[k, 1] = 0.0 if g_missing else 1.0
                seq[k, 2] = (p_hr - 75.0) / 30.0
                seq[k, 3] = 0.0 if hr_missing else 1.0
                seq[k, 4] = (p_mets - 1.0) / 3.0
                seq[k, 5] = 0.0 if mets_missing else 1.0

            anchor[0] = g_t0 / 200.0
            g_minus15_raw = pts[-3].get("glucose") if len(pts) >= 3 else None
            try:
                g_minus15 = float(g_minus15_raw) if (g_minus15_raw is not None and not math.isnan(float(g_minus15_raw))) else g_t0
            except (ValueError, TypeError):
                g_minus15 = g_t0
            anchor[1] = (g_t0 - g_minus15) / 15.0

            g_minus30_raw = pts[-6].get("glucose") if len(pts) >= 6 else None
            try:
                g_minus30 = float(g_minus30_raw) if (g_minus30_raw is not None and not math.isnan(float(g_minus30_raw))) else g_t0
            except (ValueError, TypeError):
                g_minus30 = g_t0
            anchor[2] = (g_t0 - g_minus30) / 30.0

            g_window = []
            for x in pts:
                xg = x.get("glucose")
                if xg is not None:
                    try:
                        xf = float(xg)
                        if not math.isnan(xf):
                            g_window.append(xf)
                    except (ValueError, TypeError):
                        pass
            anchor[3] = (float(np.std(g_window)) / 50.0) if g_window else 0.0
        else:
            # Fallback nominal sequence if no telemetry buffer passed
            seq[:, 1] = 1.0
            seq[:, 3] = 1.0
            seq[:, 5] = 1.0
            anchor[0] = g_t0 / 200.0

        # 5. Extract chronological residuals for few-shot Ridge personalisation
        earlier_residuals = self._get_chronological_residuals(req.patient_id, req.t0)
        n_meals = len(earlier_residuals)

        portion_unc = req.portion_uncertainty_pct
        if portion_unc <= 0.0 and req.meal.portion_uncertainty_pct > 0.0:
            portion_unc = req.meal.portion_uncertainty_pct

        tf_override = tau_fast_override if tau_fast_override is not None else req.tau_fast_override
        d_override = delay_override if delay_override is not None else req.delay_override
        p_override = phi_override if phi_override is not None else req.phi_override

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
            tau_fast_override=tf_override,
            delay_override=d_override,
            phi_override=p_override,
            portion_uncertainty_pct=portion_unc,
        )

        fc = raw_out["forecast"]
        low = raw_out["interval_lower"]
        upp = raw_out["interval_upper"]
        low_robust = raw_out.get("interval_lower_robust")
        upp_robust = raw_out.get("interval_upper_robust")

        # 7. Pharmacological Insulin (Bolus & Basal Drift) superposition
        insulin_input = req.insulin or req.meal.insulin
        iob_traj: Optional[List[float]] = None
        net_deflection: Optional[List[float]] = None

        if insulin_input and (
            insulin_input.bolus_units > 0 or abs(insulin_input.basal_rate_diff_u_hr) > 1e-4
        ):
            # Resolve ISF: override -> clinical priors / DB -> weight estimation -> default 45.0
            isf = insulin_input.isf_override
            if isf is None and patient_record:
                isf = patient_record.get("clinical_priors", {}).get("isf")
                if isf is None and "profile" in patient_record:
                    isf = patient_record["profile"].get("isf")
                if isf is None:
                    w = patient_record.get("profile", {}).get("weight_kg")
                    if w and w > 0:
                        isf = estimate_isf(w)
            if isf is None:
                isf = 45.0

            horizon_steps = [(i + 1) * 5 for i in range(36)]
            eff = compute_insulin_effect(
                horizon_min=horizon_steps,
                bolus_units=insulin_input.bolus_units,
                bolus_time_min=insulin_input.bolus_time_min,
                basal_rate_diff_u_hr=insulin_input.basal_rate_diff_u_hr,
                isf=isf,
                insulin_type=insulin_input.insulin_type,
            )
            net_deflection = [round(float(v), 2) for v in eff["net_deflection"]]
            iob_traj = [round(float(v), 3) for v in eff["iob_trajectory"]]

            # Superimpose on forecast trajectory and conformal interval bounds
            fc = [round(float(np.clip(v + d, 40.0, 400.0)), 1) for v, d in zip(fc, net_deflection)]
            low = [
                round(float(np.clip(v + d, 40.0, 400.0)), 1) for v, d in zip(low, net_deflection)
            ]
            upp = [
                round(float(np.clip(v + d, 40.0, 400.0)), 1) for v, d in zip(upp, net_deflection)
            ]
            if low_robust is not None and upp_robust is not None:
                low_robust = [
                    round(float(np.clip(v + d, 40.0, 400.0)), 1)
                    for v, d in zip(low_robust, net_deflection)
                ]
                upp_robust = [
                    round(float(np.clip(v + d, 40.0, 400.0)), 1)
                    for v, d in zip(upp_robust, net_deflection)
                ]

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
                lower_bound_robust=low_robust,
                upper_bound_robust=upp_robust,
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
            iob_trajectory=iob_traj,
            net_insulin_deflection=net_deflection,
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
        base_g0 = (
            base_traj[0] - baseline.delta_glucose[0] if baseline.delta_glucose else base_traj[0]
        )

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
                    delta_time_to_peak=sim_pred.metrics.time_to_peak_min
                    - baseline.metrics.time_to_peak_min,
                    delta_delayed_mean=round(
                        sim_pred.metrics.delayed_mean_120_180
                        - baseline.metrics.delayed_mean_120_180,
                        1,
                    ),
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
                    delta_time_to_peak=sim_pred.metrics.time_to_peak_min
                    - baseline.metrics.time_to_peak_min,
                    delta_delayed_mean=round(
                        sim_pred.metrics.delayed_mean_120_180
                        - baseline.metrics.delayed_mean_120_180,
                        1,
                    ),
                ),
                reliability=sim_pred.reliability,
                notes=f"Model-driven simulation: dietary fat altered by {delta_fat:+.1f}g, slowing gastric emptying.",
                assumption=None,
            )

        elif mod.type == "walk":
            # Dynamic physical activity / exercise non-insulin-mediated GLUT4 clearance
            mins = mod.minutes or 15
            t_start = float(mod.shift_min) if mod.shift_min is not None else 15.0
            t_end = t_start + float(mins)

            # Retrieve patient weight
            weight_kg = 70.0
            if self.db_session_factory:
                try:
                    with self.db_session_factory() as db:
                        from services.backend.models import PatientModel

                        p_rec = (
                            db.query(PatientModel)
                            .filter(PatientModel.patient_id == req.patient_id)
                            .first()
                        )
                        if p_rec and p_rec.weight_kg and p_rec.weight_kg > 0:
                            weight_kg = float(p_rec.weight_kg)
                except Exception:
                    pass

            mets = 3.5  # Moderate-to-brisk walking (Compendium of Physical Activities)
            kappa_exercise = 0.38  # mg * dL^-1 * min^-1 * DeltaMET^-1
            tau_post = 25.0  # min exponential decay tail
            r_active = kappa_exercise * (mets - 1.0) * (weight_kg / 70.0)

            # Integrate non-insulin GLUT4 clearance: CumClear(t) across 36-step horizon
            t_grid = np.arange(1, 37) * 5.0
            cum_clear = np.zeros_like(t_grid)
            for i, t in enumerate(t_grid):
                if t <= t_start:
                    cum_clear[i] = 0.0
                elif t_start < t <= t_end:
                    cum_clear[i] = r_active * (t - t_start)
                else:  # t > t_end
                    cum_clear[i] = (
                        r_active * (t_end - t_start)
                        + r_active * tau_post * (1.0 - math.exp(-(t - t_end) / tau_post))
                    )

            new_traj = np.clip(base_traj - cum_clear, 40.0, 400.0)

            peak_val = float(np.max(new_traj))
            ttp = int((np.argmax(new_traj) + 1) * 5)
            del_mean = float(np.mean(new_traj[24:]))

            # Calibrated Split-Conformal Uncertainty Intervals
            quantiles = (
                self.bundle.calibration_table.get_quantiles(
                    scenario=req.degradation, confidence_level=0.90
                )
                if self.bundle
                else np.full(36, 15.0, dtype=np.float32)
            )
            low_sc, upp_sc = compute_conformal_intervals(
                new_traj, quantiles, clamp_physiological=True
            )

            return ScenarioResult(
                type=mod.type,
                origin="assumption_driven",
                trajectory=[round(float(v), 2) for v in new_traj],
                interval=IntervalBand(
                    level=0.90,
                    lower=[round(float(v), 2) for v in low_sc],
                    upper=[round(float(v), 2) for v in upp_sc],
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
                notes=f"Physical activity clearance: {mins}-min walk (METs={mets}, W={weight_kg:.0f}kg) starting at t={t_start:.0f}m with {tau_post}m post-exercise tail.",
                assumption={
                    "source": "Reynolds et al., Diabetologia 2016; muscle GLUT4 non-insulin clearance",
                    "kappa_exercise": kappa_exercise,
                    "mets": mets,
                    "weight_kg": weight_kg,
                    "tau_post_min": tau_post,
                    "t_start_min": t_start,
                    "t_end_min": t_end,
                    "verify": True,
                },
            )

        elif mod.type == "sequencing":
            # Dynamic food sequencing: GLP-1/PYY delayed gastric emptying via Candidate S overrides
            if self.bundle:
                base_delay = self.bundle.model.base_delay
                base_tau_fast = self.bundle.model.base_tau_fast
                m_curr = req.meal
                raw_m = {
                    "carbs_g": m_curr.carbs_g * (m_curr.amount_pct / 100.0),
                    "protein_g": m_curr.protein_g * (m_curr.amount_pct / 100.0),
                    "fat_g": m_curr.fat_g * (m_curr.amount_pct / 100.0),
                    "fiber_g": m_curr.fiber_g * (m_curr.amount_pct / 100.0),
                    "calories": (
                        m_curr.carbs_g * 4.0 + m_curr.protein_g * 4.0 + m_curr.fat_g * 9.0
                    )
                    * (m_curr.amount_pct / 100.0),
                    "meal_type": m_curr.meal_type,
                    "minutes_since_prev_meal": 360.0,
                }
                m_vec = extract_meal_features(raw_m)
                base_phi = self.bundle.model.compute_phi(
                    torch.tensor(m_vec, dtype=torch.float32).unsqueeze(0)
                )

                delay_override = base_delay * 1.35 + 10.0
                tau_fast_override = base_tau_fast * 1.25
                phi_override = min(1.0, base_phi + 0.25)

                mod_req = PredictRequest(
                    patient_id=req.patient_id,
                    session_id=req.session_id,
                    t0=req.t0,
                    meal=req.meal,
                    degradation=req.degradation,
                    tau_fast_override=tau_fast_override,
                    delay_override=delay_override,
                    phi_override=phi_override,
                )
                sim_pred = await self.predict(
                    mod_req,
                    tau_fast_override=tau_fast_override,
                    delay_override=delay_override,
                    phi_override=phi_override,
                )
                return ScenarioResult(
                    type=mod.type,
                    origin="model_driven",
                    trajectory=sim_pred.glucose,
                    interval=sim_pred.interval,
                    metrics=sim_pred.metrics,
                    delta_vs_baseline=ScenarioDifference(
                        delta_peak=round(sim_pred.metrics.peak - baseline.metrics.peak, 1),
                        delta_time_to_peak=sim_pred.metrics.time_to_peak_min
                        - baseline.metrics.time_to_peak_min,
                        delta_delayed_mean=round(
                            sim_pred.metrics.delayed_mean_120_180
                            - baseline.metrics.delayed_mean_120_180,
                            1,
                        ),
                    ),
                    reliability=sim_pred.reliability,
                    notes=(
                        f"Food sequencing: Candidate S kinetic overrides (delay={delay_override:.1f}m, "
                        f"tau_fast={tau_fast_override:.1f}m, phi={phi_override:.2f}) modeling GLP-1/PYY delayed gastric emptying."
                    ),
                    assumption={
                        "source": "Shukla et al., BMJ Open Diabetes Res Care 2017; GLP-1/PYY delay model",
                        "delay_override": round(delay_override, 1),
                        "tau_fast_override": round(tau_fast_override, 1),
                        "phi_override": round(phi_override, 2),
                        "verify": True,
                    },
                )
            else:
                quantiles = np.full(36, 15.0, dtype=np.float32)
                shifted = np.zeros_like(baseline.delta_glucose)
                shifted[3:] = np.array(baseline.delta_glucose)[:-3] * 0.85
                shifted[:3] = np.array(baseline.delta_glucose)[:3] * 0.5
                new_traj = np.clip(base_g0 + shifted, 40.0, 400.0)
                low_sc, upp_sc = compute_conformal_intervals(
                    new_traj, quantiles, clamp_physiological=True
                )
                peak_val = float(np.max(new_traj))
                ttp = int((np.argmax(new_traj) + 1) * 5)
                del_mean = float(np.mean(new_traj[24:]))
                return ScenarioResult(
                    type=mod.type,
                    origin="model_driven",
                    trajectory=[round(float(v), 2) for v in new_traj],
                    interval=IntervalBand(
                        level=0.90,
                        lower=[round(float(v), 2) for v in low_sc],
                        upper=[round(float(v), 2) for v in upp_sc],
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
                    notes="Food sequencing: Mock simulation with delayed absorption.",
                    assumption={"source": "Shukla et al., 2017"},
                )

        elif mod.type == "insulin":
            # Model-driven pharmacological insulin simulation
            bolus = mod.bolus_units if mod.bolus_units is not None else 4.0
            b_time = mod.bolus_time_min if mod.bolus_time_min is not None else 0.0
            basal_diff = mod.basal_rate_diff_u_hr if mod.basal_rate_diff_u_hr is not None else 0.0
            i_type = mod.insulin_type or "rapid_acting"
            isf_over = mod.isf_override

            insulin_in = InsulinInput(
                bolus_units=bolus,
                bolus_time_min=b_time,
                insulin_type=i_type,
                basal_rate_diff_u_hr=basal_diff,
                isf_override=isf_over,
            )
            mod_req = PredictRequest(
                patient_id=req.patient_id,
                session_id=req.session_id,
                t0=req.t0,
                meal=req.meal,
                degradation=req.degradation,
                insulin=insulin_in,
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
                    delta_time_to_peak=sim_pred.metrics.time_to_peak_min
                    - baseline.metrics.time_to_peak_min,
                    delta_delayed_mean=round(
                        sim_pred.metrics.delayed_mean_120_180
                        - baseline.metrics.delayed_mean_120_180,
                        1,
                    ),
                ),
                reliability=sim_pred.reliability,
                notes=f"Pharmacological insulin simulation: {bolus}U {i_type} at t={b_time:+.0f}m, basal diff {basal_diff:+.2f} U/hr.",
                assumption=None,
            )

        else:
            return ScenarioResult(
                type=mod.type,
                origin="model_driven",
                trajectory=baseline.glucose,
                interval=baseline.interval,
                metrics=baseline.metrics,
                delta_vs_baseline=ScenarioDifference(
                    delta_peak=0.0, delta_time_to_peak=0, delta_delayed_mean=0.0
                ),
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

        insulin_input = req.insulin or req.meal.insulin
        net_deflection: Optional[List[float]] = None
        iob_traj: Optional[List[float]] = None

        if insulin_input and (
            insulin_input.bolus_units > 0 or abs(insulin_input.basal_rate_diff_u_hr) > 1e-4
        ):
            isf = insulin_input.isf_override or 45.0
            eff = compute_insulin_effect(
                horizon_min=t_grid.tolist(),
                bolus_units=insulin_input.bolus_units,
                bolus_time_min=insulin_input.bolus_time_min,
                basal_rate_diff_u_hr=insulin_input.basal_rate_diff_u_hr,
                isf=isf,
                insulin_type=insulin_input.insulin_type,
            )
            net_deflection = [round(float(v), 2) for v in eff["net_deflection"]]
            iob_traj = [round(float(v), 3) for v in eff["iob_trajectory"]]

            glucose = np.clip(glucose + np.array(net_deflection), 40.0, 400.0)
            excursion = glucose - g0

        peak_val = float(np.max(glucose))
        ttp = int(t_grid[np.argmax(glucose)])
        del_mean = float(np.mean(glucose[24:]))

        portion_unc = req.portion_uncertainty_pct
        if portion_unc <= 0.0 and req.meal.portion_uncertainty_pct > 0.0:
            portion_unc = req.meal.portion_uncertainty_pct

        low_robust: Optional[List[float]] = None
        upp_robust: Optional[List[float]] = None
        if portion_unc > 0.0:
            delta = min(0.50, portion_unc / 100.0)
            delta_traj = delta * np.abs(excursion)
            low_robust = [
                round(float(np.clip(v - d - 18.0, 40.0, 400.0)), 2)
                for v, d in zip(glucose, delta_traj)
            ]
            upp_robust = [
                round(float(np.clip(v + d + 18.0, 40.0, 400.0)), 2)
                for v, d in zip(glucose, delta_traj)
            ]

        return PredictResponse(
            horizon_min=t_grid.tolist(),
            delta_glucose=[round(float(v), 2) for v in excursion],
            glucose=[round(float(v), 2) for v in glucose],
            interval=IntervalBand(
                level=0.90,
                lower=[round(float(v - 18.0), 2) for v in glucose],
                upper=[round(float(v + 18.0), 2) for v in glucose],
                scenario=req.degradation,
                lower_bound_robust=low_robust,
                upper_bound_robust=upp_robust,
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
            iob_trajectory=iob_traj,
            net_insulin_deflection=net_deflection,
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

        results: List[ScenarioResult] = []
        for mod in req.scenarios:
            if mod.type == "portion":
                amt = mod.amount_pct if mod.amount_pct is not None else 100.0
                mod_meal = req.meal.model_copy(update={"amount_pct": amt})
                p = await self.predict(base_req.model_copy(update={"meal": mod_meal}))
                results.append(
                    ScenarioResult(
                        type=mod.type,
                        origin="model_driven",
                        trajectory=p.glucose,
                        interval=p.interval,
                        metrics=p.metrics,
                        delta_vs_baseline=ScenarioDifference(
                            delta_peak=round(p.metrics.peak - baseline.metrics.peak, 1),
                            delta_time_to_peak=p.metrics.time_to_peak_min
                            - baseline.metrics.time_to_peak_min,
                            delta_delayed_mean=round(
                                p.metrics.delayed_mean_120_180
                                - baseline.metrics.delayed_mean_120_180,
                                1,
                            ),
                        ),
                        reliability=p.reliability,
                    )
                )
            elif mod.type == "walk":
                mins = mod.minutes or 15
                t_grid = np.arange(1, 37) * 5.0
                t_start = 15.0
                t_end = t_start + float(mins)
                r_active = 0.38 * 2.5  # 0.95 mg/dL/min
                cum_clear = np.zeros_like(t_grid)
                for i, t in enumerate(t_grid):
                    if t_start < t <= t_end:
                        cum_clear[i] = r_active * (t - t_start)
                    elif t > t_end:
                        cum_clear[i] = r_active * (t_end - t_start) + r_active * 25.0 * (
                            1.0 - math.exp(-(t - t_end) / 25.0)
                        )
                new_traj = np.clip(np.array(baseline.glucose) - cum_clear, 40.0, 400.0)
                peak_val = float(np.max(new_traj))
                ttp = int((np.argmax(new_traj) + 1) * 5)
                del_mean = float(np.mean(new_traj[24:]))
                results.append(
                    ScenarioResult(
                        type=mod.type,
                        origin="assumption_driven",
                        trajectory=[round(float(v), 2) for v in new_traj],
                        interval=IntervalBand(
                            level=0.90,
                            lower=[round(float(v - 18.0), 2) for v in new_traj],
                            upper=[round(float(v + 18.0), 2) for v in new_traj],
                            scenario=baseline.interval.scenario,
                        ),
                        metrics=ForecastMetrics(
                            peak=round(peak_val, 1),
                            time_to_peak_min=ttp,
                            delayed_mean_120_180=round(del_mean, 1),
                        ),
                        delta_vs_baseline=ScenarioDifference(
                            delta_peak=round(peak_val - baseline.metrics.peak, 1),
                            delta_time_to_peak=ttp - baseline.metrics.time_to_peak_min,
                            delta_delayed_mean=round(
                                del_mean - baseline.metrics.delayed_mean_120_180, 1
                            ),
                        ),
                        reliability=baseline.reliability,
                        assumption={"source": "Reynolds et al., Diabetologia 2016"},
                    )
                )
            else:
                results.append(
                    ScenarioResult(
                        type=mod.type,
                        origin="model_driven",
                        trajectory=baseline.glucose,
                        interval=baseline.interval,
                        metrics=baseline.metrics,
                        delta_vs_baseline=ScenarioDifference(
                            delta_peak=0.0, delta_time_to_peak=0, delta_delayed_mean=0.0
                        ),
                        reliability=baseline.reliability,
                    )
                )

        return SimulateResponse(
            baseline=baseline,
            scenarios=results,
            disclaimer=CLINICAL_DISCLAIMER,
        )
