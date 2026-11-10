"""Asynchronous real-data replay engine with WebSocket broadcast (Decision D13)."""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
from fastapi import WebSocket

from services.backend.inference.provider import InferenceProvider

logger = logging.getLogger(__name__)


@dataclass
class ReplayState:
    """In-memory active replay session cursor."""

    session_id: str
    patient_id: str
    status: str  # IDLE, RUNNING, PAUSED, STOPPED
    speed: int  # 1, 5, 10, 50, 100
    degradation: str  # D0-D7
    cursor_idx: int
    total_steps: int
    started_at: datetime.datetime
    current_glucose: float
    current_hr: float
    current_mets: float
    active_forecast: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["started_at"] = self.started_at.isoformat()
        d["active_degradation"] = self.degradation
        return d


class ReplayEngine:
    """Manages playback, time advancement, degradation injection, and WebSocket events from real sensor data."""

    def __init__(self, inference_provider: Optional[InferenceProvider] = None) -> None:
        self.inference_provider = inference_provider
        self.sessions: Dict[str, ReplayState] = {}
        self.listeners: Dict[str, Set[WebSocket]] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self._series_cache: Dict[str, List[Dict[str, Any]]] = {}

    def register_client(self, session_id: str, websocket: WebSocket) -> None:
        self.listeners.setdefault(session_id, set()).add(websocket)

    def unregister_client(self, session_id: str, websocket: WebSocket) -> None:
        if session_id in self.listeners:
            self.listeners[session_id].discard(websocket)
            if not self.listeners[session_id]:
                del self.listeners[session_id]

    async def broadcast(self, session_id: str, event: Dict[str, Any]) -> None:
        if session_id not in self.listeners:
            return
        dead = []
        for ws in self.listeners[session_id]:
            try:
                await ws.send_text(json.dumps(event))
            except Exception:
                dead.append(ws)
        for d in dead:
            self.listeners[session_id].discard(d)

    def _load_patient_series(self, patient_id: str) -> List[Dict[str, Any]]:
        """Loads real 5-minute continuous telemetry and clinical meals from processed parquets."""
        if patient_id in self._series_cache:
            return self._series_cache[patient_id]

        sensor_file = Path("data/processed/sensor_5min.parquet")
        meals_file = Path("data/processed/meals.parquet")

        if not sensor_file.exists():
            sensor_file = Path("data/demo/sensor_5min.parquet")
        if not meals_file.exists():
            meals_file = Path("data/demo/meals.parquet")

        if not sensor_file.exists():
            logger.warning(f"Sensor file {sensor_file} not found. Fallback to basic series.")
            return self._create_fallback_series(patient_id)

        try:
            df = pd.read_parquet(sensor_file)
            p_df = df[df["patient_id"] == patient_id].sort_values("ts").reset_index(drop=True)

            if len(p_df) == 0:
                # If patient_id not in sensor_5min, pick first available patient's data
                avail = df["patient_id"].unique()
                if len(avail) > 0:
                    first_p = avail[0]
                    logger.info(
                        f"Patient {patient_id} not in sensor parquet. Using {first_p} timeseries."
                    )
                    p_df = df[df["patient_id"] == first_p].sort_values("ts").reset_index(drop=True)
                else:
                    return self._create_fallback_series(patient_id)

            # Load real meals
            meals_dict: Dict[int, Dict[str, Any]] = {}
            if meals_file.exists():
                m_df = pd.read_parquet(meals_file)
                p_meals = m_df[m_df["patient_id"] == patient_id]
                if len(p_meals) == 0 and len(m_df) > 0:
                    # Fallback to meals of available patient
                    p_meals = m_df[m_df["patient_id"] == p_df["patient_id"].iloc[0]]

                # Map each meal to closest step index
                for _, m_row in p_meals.iterrows():
                    m_ts = pd.to_datetime(m_row["ts_start"])
                    # Find closest ts index in p_df
                    diffs = (pd.to_datetime(p_df["ts"]) - m_ts).abs()
                    closest_idx = int(diffs.idxmin())
                    meals_dict[closest_idx] = {
                        "meal_id": str(m_row.get("meal_id", f"M_{closest_idx}")),
                        "name": f"{str(m_row.get('meal_type', 'Meal')).title()} ({float(m_row.get('carbs_g', 50))}g C, {float(m_row.get('fat_g', 15))}g F)",
                        "meal_type": str(m_row.get("meal_type", "lunch")),
                        "carbs_g": float(m_row.get("carbs_g", 50.0)),
                        "fat_g": float(m_row.get("fat_g", 15.0)),
                        "protein_g": float(m_row.get("protein_g", 20.0)),
                        "fiber_g": float(m_row.get("fiber_g", 5.0)),
                        "calories": float(m_row.get("calories", 400.0)),
                        "amount_pct": float(m_row.get("amount_consumed_pct", 100.0)),
                    }

            # Build list of points
            points = []
            n_rows = len(p_df)
            for idx in range(n_rows):
                row = p_df.iloc[idx]
                ts_dt = pd.to_datetime(row["ts"])
                is_meal = idx in meals_dict
                meal_info = meals_dict.get(idx)

                # Ground-truth future trajectory for meal overlay (next 36 steps = 180 min)
                actual_curve = None
                if is_meal:
                    future_slice = p_df.iloc[idx : min(n_rows, idx + 36)]["glucose"].tolist()
                    actual_curve = [round(float(v), 2) for v in future_slice]

                points.append(
                    {
                        "step": idx,
                        "ts": ts_dt.isoformat(),
                        "glucose": round(float(row["glucose"]), 1),
                        "hr": round(float(row.get("hr", 72.0)), 1),
                        "mets": round(float(row.get("mets", 1.0)), 2),
                        "glucose_missing": bool(row.get("glucose_missing", False)),
                        "hr_missing": bool(row.get("hr_missing", False)),
                        "mets_missing": bool(row.get("mets_missing", False)),
                        "is_meal": is_meal,
                        "meal": meal_info,
                        "actual_curve": actual_curve,
                    }
                )

            self._series_cache[patient_id] = points
            logger.info(
                f"Loaded {len(points)} real sensor readings and {len(meals_dict)} meals for patient {patient_id}"
            )
            return points

        except Exception as e:
            logger.error(f"Error loading real series for {patient_id}: {e}")
            return self._create_fallback_series(patient_id)

    def _create_fallback_series(self, patient_id: str) -> List[Dict[str, Any]]:
        """Fallback series if parquet files are completely absent."""
        points = []
        base_t = datetime.datetime.now(datetime.timezone.utc).replace(
            hour=8, minute=0, second=0, microsecond=0
        )
        curr_g = 120.0
        for step in range(144):
            ts = base_t + datetime.timedelta(minutes=step * 5)
            is_meal = step in [24, 72]
            meal_info = None
            if step == 24:
                curr_g += 45.0
                meal_info = {
                    "meal_id": f"M_{patient_id}_1",
                    "name": "Breakfast",
                    "carbs_g": 45.0,
                    "fat_g": 12.0,
                    "protein_g": 15.0,
                    "calories": 350.0,
                    "amount_pct": 100.0,
                    "meal_type": "breakfast",
                }
            elif step == 72:
                curr_g += 60.0
                meal_info = {
                    "meal_id": f"M_{patient_id}_2",
                    "name": "Lunch",
                    "carbs_g": 65.0,
                    "fat_g": 20.0,
                    "protein_g": 22.0,
                    "calories": 520.0,
                    "amount_pct": 100.0,
                    "meal_type": "lunch",
                }
            else:
                curr_g = curr_g + (120.0 - curr_g) * 0.05
            points.append(
                {
                    "step": step,
                    "ts": ts.isoformat(),
                    "glucose": round(curr_g, 1),
                    "hr": 72.0,
                    "mets": 1.0,
                    "glucose_missing": False,
                    "hr_missing": False,
                    "mets_missing": False,
                    "is_meal": is_meal,
                    "meal": meal_info,
                    "actual_curve": None,
                }
            )
        self._series_cache[patient_id] = points
        return points

    def get_patient_series(self, patient_id: str) -> List[Dict[str, Any]]:
        return self._load_patient_series(patient_id)

    def get_retrospective_buffer(
        self, patient_id: str, cursor_idx: int, steps: int = 12
    ) -> List[Dict[str, Any]]:
        """Extracts preceding 12 steps (60 minutes) from the active replay buffer."""
        series = self._load_patient_series(patient_id)
        if not series:
            return []
        start_idx = max(0, cursor_idx - steps)
        window = series[start_idx:cursor_idx]
        # Pad with first element if cursor is near beginning
        while len(window) < steps and len(series) > 0:
            window.insert(0, series[0])
        return window

    def start_session(
        self,
        session_id: str,
        patient_id: str = "P020",
        speed: int = 10,
        degradation: str = "D0",
    ) -> ReplayState:
        series = self._load_patient_series(patient_id)

        # Cancel existing task if running
        if session_id in self.tasks and not self.tasks[session_id].done():
            self.tasks[session_id].cancel()

        state = ReplayState(
            session_id=session_id,
            patient_id=patient_id,
            status="RUNNING",
            speed=max(1, min(100, speed)),
            degradation=degradation,
            cursor_idx=0,
            total_steps=len(series),
            started_at=datetime.datetime.now(datetime.timezone.utc),
            current_glucose=series[0]["glucose"] if series else 120.0,
            current_hr=series[0]["hr"] if series else 72.0,
            current_mets=series[0]["mets"] if series else 1.0,
        )
        self.sessions[session_id] = state
        self.tasks[session_id] = asyncio.create_task(self._run_loop(session_id))
        return state

    def pause_session(self, session_id: str) -> Optional[ReplayState]:
        state = self.sessions.get(session_id)
        if state:
            state.status = "PAUSED"
            asyncio.create_task(self.broadcast(session_id, {"type": "STATUS", "status": "PAUSED"}))
        return state

    def resume_session(self, session_id: str) -> Optional[ReplayState]:
        state = self.sessions.get(session_id)
        if state:
            state.status = "RUNNING"
            if session_id not in self.tasks or self.tasks[session_id].done():
                self.tasks[session_id] = asyncio.create_task(self._run_loop(session_id))
            asyncio.create_task(self.broadcast(session_id, {"type": "STATUS", "status": "RUNNING"}))
        return state

    def stop_session(self, session_id: str) -> Optional[ReplayState]:
        state = self.sessions.get(session_id)
        if state:
            state.status = "STOPPED"
            if session_id in self.tasks and not self.tasks[session_id].done():
                self.tasks[session_id].cancel()
            asyncio.create_task(self.broadcast(session_id, {"type": "STATUS", "status": "STOPPED"}))
        return state

    def jump_to_next_meal(self, session_id: str) -> Optional[ReplayState]:
        """Advances replay cursor directly to the next clinical meal event."""
        state = self.sessions.get(session_id)
        if not state:
            return None
        series = self._load_patient_series(state.patient_id)
        next_meal_idx = None
        for i in range(state.cursor_idx + 1, len(series)):
            if series[i].get("is_meal"):
                next_meal_idx = i
                break

        if next_meal_idx is None:
            # Wrap around to first meal if at the end
            for i in range(len(series)):
                if series[i].get("is_meal"):
                    next_meal_idx = i
                    break

        if next_meal_idx is not None:
            state.cursor_idx = next_meal_idx
            pt = series[state.cursor_idx]
            state.current_glucose = pt["glucose"]
            state.current_hr = pt["hr"]
            state.current_mets = pt["mets"]
            # Trigger immediate async event
            asyncio.create_task(self._process_step(session_id, state, pt, series))
        return state

    def set_degradation(self, session_id: str, degradation: str) -> Optional[ReplayState]:
        state = self.sessions.get(session_id)
        if state:
            state.degradation = degradation
            asyncio.create_task(
                self.broadcast(
                    session_id,
                    {"type": "DEGRADATION_CHANGED", "degradation": degradation},
                )
            )
        return state

    async def _process_step(
        self, session_id: str, state: ReplayState, pt: Dict[str, Any], series: List[Dict[str, Any]]
    ) -> None:
        """Processes a single step, broadcasting tick and running forecast on meal arrival."""
        state.current_glucose = pt["glucose"]
        state.current_hr = pt["hr"]
        state.current_mets = pt["mets"]

        # 1. Broadcast TICK
        await self.broadcast(
            session_id,
            {
                "type": "TICK",
                "cursor_idx": state.cursor_idx,
                "timestamp": pt["ts"],
                "glucose": pt["glucose"],
                "hr": pt["hr"],
                "mets": pt["mets"],
                "glucose_missing": pt.get("glucose_missing", False),
                "degradation": state.degradation,
                "progress_pct": round((state.cursor_idx / max(1, state.total_steps)) * 100, 1),
            },
        )

        # 2. Check for MEAL_EVENT
        if pt.get("is_meal") and pt.get("meal"):
            await self.broadcast(
                session_id,
                {
                    "type": "MEAL_EVENT",
                    "meal": pt["meal"],
                    "timestamp": pt["ts"],
                    "actual_curve": pt.get("actual_curve"),
                },
            )

            # Trigger automatic forecast using real 60-min retrospective buffer
            if self.inference_provider is not None:
                try:
                    from services.common.contracts import MealInput, PredictRequest

                    retrospective_window = self.get_retrospective_buffer(
                        state.patient_id, state.cursor_idx, steps=12
                    )

                    req = PredictRequest(
                        patient_id=state.patient_id,
                        session_id=session_id,
                        t0=pt["ts"],
                        meal=MealInput(
                            carbs_g=pt["meal"]["carbs_g"],
                            fat_g=pt["meal"]["fat_g"],
                            protein_g=pt["meal"]["protein_g"],
                            fiber_g=pt["meal"]["fiber_g"],
                            amount_pct=pt["meal"]["amount_pct"],
                            meal_type=pt["meal"]["meal_type"],
                        ),
                        degradation=state.degradation,
                        g_t0=pt["glucose"],
                        retrospective_sequence=retrospective_window,
                    )
                    pred_resp = await self.inference_provider.predict(req)
                    state.active_forecast = pred_resp.model_dump()
                    await self.broadcast(
                        session_id,
                        {
                            "type": "FORECAST",
                            "forecast": pred_resp.glucose,
                            "actual": pt.get("actual_curve"),
                            "interval": pred_resp.interval.model_dump(),
                            "metrics": pred_resp.metrics.model_dump(),
                            "reliability": pred_resp.reliability.model_dump(),
                            "personalisation": pred_resp.personalisation.model_dump(),
                        },
                    )
                except Exception as e:
                    logger.error(f"Inference during replay failed: {e}")

    async def _run_loop(self, session_id: str) -> None:
        """Main async tick advancing cursor through real sensor readings."""
        try:
            while True:
                state = self.sessions.get(session_id)
                if not state or state.status != "RUNNING":
                    break

                series = self._load_patient_series(state.patient_id)
                if state.cursor_idx >= len(series):
                    state.status = "STOPPED"
                    await self.broadcast(session_id, {"type": "STATUS", "status": "COMPLETED"})
                    break

                pt = series[state.cursor_idx]
                await self._process_step(session_id, state, pt, series)

                state.cursor_idx += 1
                sleep_duration = max(0.05, 5.0 / state.speed)
                await asyncio.sleep(sleep_duration)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Replay loop encountered error: {e}")
