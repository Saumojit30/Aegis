"""Asynchronous in-memory replay engine with WebSocket broadcast (Decision D13)."""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set

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
    """Manages playback, time advancement, degradation injection, and WebSocket events."""

    def __init__(self, inference_provider: Optional[InferenceProvider] = None) -> None:
        self.inference_provider = inference_provider
        self.sessions: Dict[str, ReplayState] = {}
        self.listeners: Dict[str, Set[WebSocket]] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self._mock_data: Dict[str, List[Dict[str, Any]]] = {}

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

    def _get_or_create_series(self, patient_id: str) -> List[Dict[str, Any]]:
        """Generates continuous 5-minute replay points if not already cached."""
        if patient_id in self._mock_data:
            return self._mock_data[patient_id]

        points = []
        base_t = datetime.datetime.now(datetime.timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0)
        curr_g = 115.0

        for step in range(144):  # 12 hours of 5-min intervals
            ts = base_t + datetime.timedelta(minutes=step * 5)
            # Meal at step 24 (10:00) and step 72 (14:00)
            is_meal = step in [24, 72]
            meal_info = None

            if step == 24:
                curr_g += 55.0
                meal_info = {"meal_id": f"M_{patient_id}_1", "carbs_g": 60.0, "fat_g": 18.0, "calories": 450.0}
            elif step == 72:
                curr_g += 65.0
                meal_info = {"meal_id": f"M_{patient_id}_2", "carbs_g": 75.0, "fat_g": 22.0, "calories": 580.0}
            else:
                # Gradual return to baseline
                curr_g = curr_g + (115.0 - curr_g) * 0.05 + float(step % 3 - 1)

            points.append({
                "step": step,
                "ts": ts.isoformat(),
                "glucose": round(curr_g, 1),
                "hr": round(72.0 + (step % 7), 1),
                "mets": round(1.1 + (step % 4) * 0.1, 2),
                "is_meal": is_meal,
                "meal": meal_info,
            })

        self._mock_data[patient_id] = points
        return points

    def start_session(
        self,
        session_id: str,
        patient_id: str = "P001",
        speed: int = 10,
        degradation: str = "D0",
    ) -> ReplayState:
        series = self._get_or_create_series(patient_id)

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
            current_glucose=series[0]["glucose"],
            current_hr=series[0]["hr"],
            current_mets=series[0]["mets"],
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

    async def _run_loop(self, session_id: str) -> None:
        """Main async tick advancing cursor and triggering events."""
        try:
            while True:
                state = self.sessions.get(session_id)
                if not state or state.status != "RUNNING":
                    break

                series = self._get_or_create_series(state.patient_id)
                if state.cursor_idx >= len(series):
                    state.status = "STOPPED"
                    await self.broadcast(session_id, {"type": "STATUS", "status": "COMPLETED"})
                    break

                pt = series[state.cursor_idx]
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
                        "degradation": state.degradation,
                        "progress_pct": round((state.cursor_idx / state.total_steps) * 100, 1),
                    },
                )

                # 2. Check for MEAL_EVENT
                if pt.get("is_meal"):
                    await self.broadcast(
                        session_id,
                        {
                            "type": "MEAL_EVENT",
                            "meal": pt["meal"],
                            "timestamp": pt["ts"],
                        },
                    )

                    # Trigger automatic forecast
                    if self.inference_provider is not None:
                        try:
                            from services.common.contracts import MealInput, PredictRequest
                            req = PredictRequest(
                                patient_id=state.patient_id,
                                session_id=session_id,
                                t0=pt["ts"],
                                meal=MealInput(
                                    carbs_g=pt["meal"]["carbs_g"],
                                    fat_g=pt["meal"]["fat_g"],
                                ),
                                degradation=state.degradation,
                            )
                            pred_resp = await self.inference_provider.predict(req)
                            state.active_forecast = pred_resp.model_dump()
                            await self.broadcast(
                                session_id,
                                {
                                    "type": "FORECAST",
                                    "forecast": pred_resp.glucose,
                                    "interval": pred_resp.interval.model_dump(),
                                    "metrics": pred_resp.metrics.model_dump(),
                                    "reliability": pred_resp.reliability.model_dump(),
                                },
                            )
                        except Exception as e:
                            logger.error(f"Inference during replay failed: {e}")

                state.cursor_idx += 1
                # Sleep interval based on speed: 10x means 0.5s per step
                sleep_duration = max(0.05, 5.0 / state.speed)
                await asyncio.sleep(sleep_duration)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in replay loop {session_id}: {e}")
