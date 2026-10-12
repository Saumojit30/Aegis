"""FastAPI backend service and clinician digital twin replay server."""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from services.backend.db import get_db, init_db, seed_database_if_empty
from services.backend.inference.provider import (
    HttpInferenceProvider,
    InferenceProvider,
    InProcessInferenceProvider,
    MockInferenceProvider,
)
from services.backend.models import MealModel, PatientModel
from services.backend.replay.engine import ReplayEngine
from services.common.contracts import (
    CLINICAL_DISCLAIMER,
    PredictRequest,
    PredictResponse,
    SimulateRequest,
    SimulateResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aegis.backend")


# Select inference provider based on environment / config (Decision D12)
def create_inference_provider() -> InferenceProvider:
    mode = os.getenv("INFERENCE_MODE", "inprocess").lower()
    if mode == "http":
        url = os.getenv("INFERENCE_URL", "http://127.0.0.1:8001")
        logger.info(f"Using HttpInferenceProvider targeting {url}")
        return HttpInferenceProvider(service_url=url)
    elif mode == "mock":
        logger.info("Using MockInferenceProvider")
        return MockInferenceProvider()
    else:
        logger.info("Using InProcessInferenceProvider (Candidate S bundle)")
        return InProcessInferenceProvider("artifacts/bundle")


inference_provider = create_inference_provider()
replay_engine = ReplayEngine(inference_provider=inference_provider)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database and seed
    init_db()
    seed_database_if_empty()
    yield
    # Shutdown logic if any


app = FastAPI(
    title="Aegis Digital Twin Backend API",
    description="Clinician digital twin API for 180-min glucose trajectory forecasting, degradation resilience, and what-if simulation.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
@app.get("/dashboard", include_in_schema=False)
def serve_dashboard():
    index_file = Path(__file__).parent / "static" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Aegis Backend API is running. Visit /docs for Swagger UI."}


# --- System & Model Metadata ---

@app.get("/health")
def health_endpoint(db: Session = Depends(get_db)):
    patient_count = db.query(PatientModel).count()
    return {
        "status": "healthy",
        "service": "aegis-backend",
        "inference_mode": inference_provider.__class__.__name__,
        "database_patients": patient_count,
        "disclaimer": CLINICAL_DISCLAIMER,
    }


@app.get("/model/info")
def model_info_endpoint():
    info = {
        "model_architecture": "StructuredMealForecasterS",
        "version": "1.0.0",
        "dataset_version": "v1.0.0-c0425ca91dfa9819",
        "feature_version": "v1.0-deep",
        "lineage": "CGMacros + Synthetic Clinical EHR (Decision D14)",
        "intended_use": "Clinician postprandial glycemic trajectory replay and what-if dietary simulation.",
        "limitations": "Research prototype; not intended for insulin dose titrations or autonomous medical decisions.",
        "disclaimer": CLINICAL_DISCLAIMER,
    }
    if hasattr(inference_provider, "bundle") and inference_provider.bundle:
        info.update(inference_provider.bundle.metadata)
    return info


# --- Patient Twins ---

@app.get("/patients")
def list_patients(db: Session = Depends(get_db)):
    patients = db.query(PatientModel).all()
    return [p.to_dict() for p in patients]


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(PatientModel).filter(PatientModel.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")
    return p.to_dict()


@app.get("/patients/{patient_id}/state")
def get_patient_state(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(PatientModel).filter(PatientModel.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")

    meal_count = db.query(MealModel).filter(MealModel.patient_id == patient_id).count()

    return {
        "patient_id": patient_id,
        "profile": p.to_dict()["profile"],
        "stream": {
            "last_glucose": 124.0,
            "hr": 74.0,
            "mets": 1.15,
            "anchor_age_min": 0.0,
        },
        "personalisation": {
            "n_personal_meals": meal_count,
            "method": "residual_pca_ridge",
            "prior": "similarity",
        },
        "data_quality": {
            "active_degradation": "D0",
            "cgm_missing": False,
            "wearables_missing": False,
        },
        "reliability": "HIGH",
    }


@app.get("/patients/{patient_id}/similar")
def get_similar_patients(
    patient_id: str,
    k: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
):
    target = db.query(PatientModel).filter(PatientModel.patient_id == patient_id).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")

    all_p = db.query(PatientModel).filter(PatientModel.patient_id != patient_id).all()
    results = []
    for other in all_p:
        # Euclidean distance on age, bmi, hba1c
        d = (
            ((target.age - other.age) / 14.0) ** 2
            + ((target.bmi - other.bmi) / 5.5) ** 2
            + ((target.hba1c - other.hba1c) / 1.2) ** 2
        ) ** 0.5
        sim = float(1.0 / (1.0 + d))
        results.append({
            "patient_id": other.patient_id,
            "distance": round(float(d), 2),
            "similarity_score": round(sim, 3),
            "profile": other.to_dict()["profile"],
        })

    results.sort(key=lambda x: x["distance"])
    return results[:k]


# --- Meal Presets ---

@app.get("/meal-presets")
def get_meal_presets():
    """Returns curated Indian and reference meal presets with composition and support scores."""
    return [
        {
            "preset_id": "roti_dal_sabzi",
            "name": "2 Rotis with Dal & Mixed Veg Sabzi",
            "cuisine": "North Indian",
            "carbs_g": 48.0,
            "protein_g": 16.0,
            "fat_g": 12.0,
            "fiber_g": 8.0,
            "calories": 380.0,
            "meal_type": "lunch",
            "support_score": 0.95,
            "source": "ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
        },
        {
            "preset_id": "idli_sambar",
            "name": "3 Idlis with Sambar & Coconut Chutney",
            "cuisine": "South Indian",
            "carbs_g": 55.0,
            "protein_g": 12.0,
            "fat_g": 8.0,
            "fiber_g": 6.0,
            "calories": 340.0,
            "meal_type": "breakfast",
            "support_score": 0.92,
            "source": "IFCT 2017",
        },
        {
            "preset_id": "chicken_biryani",
            "name": "Chicken Biryani (Standard Plate)",
            "cuisine": "Hyderabadi / Mughlai",
            "carbs_g": 68.0,
            "protein_g": 32.0,
            "fat_g": 22.0,
            "fiber_g": 4.0,
            "calories": 620.0,
            "meal_type": "dinner",
            "support_score": 0.88,
            "source": "IFCT 2017",
        },
        {
            "preset_id": "masala_dosa",
            "name": "Masala Dosa with Sambar",
            "cuisine": "South Indian",
            "carbs_g": 62.0,
            "protein_g": 10.0,
            "fat_g": 18.0,
            "fiber_g": 5.0,
            "calories": 460.0,
            "meal_type": "breakfast",
            "support_score": 0.89,
            "source": "IFCT 2017",
        },
        {
            "preset_id": "rajma_chawal",
            "name": "Rajma Chawal (Kidney Beans with Rice)",
            "cuisine": "North Indian",
            "carbs_g": 72.0,
            "protein_g": 20.0,
            "fat_g": 14.0,
            "fiber_g": 12.0,
            "calories": 510.0,
            "meal_type": "lunch",
            "support_score": 0.86,
            "source": "IFCT 2017",
        },
        {
            "preset_id": "continental_salad",
            "name": "Grilled Chicken with Quinoa Salad",
            "cuisine": "Continental",
            "carbs_g": 35.0,
            "protein_g": 35.0,
            "fat_g": 14.0,
            "fiber_g": 7.0,
            "calories": 410.0,
            "meal_type": "dinner",
            "support_score": 0.96,
            "source": "USDA FoodData Central",
        },
    ]


# --- Forecasting & Simulation ---

@app.post("/predict", response_model=PredictResponse)
async def predict_endpoint(request: PredictRequest):
    return await inference_provider.predict(request)


@app.post("/simulate", response_model=SimulateResponse)
async def simulate_endpoint(request: SimulateRequest):
    return await inference_provider.simulate(request)


# --- Clinician Replay Controls ---

@app.post("/replay/start")
async def start_replay(
    session_id: str = "default",
    patient_id: str = "P001",
    speed: int = 10,
    degradation: str = "D0",
):
    state = replay_engine.start_session(
        session_id=session_id,
        patient_id=patient_id,
        speed=speed,
        degradation=degradation,
    )
    return state.to_dict()


@app.post("/replay/pause")
async def pause_replay(session_id: str = "default"):
    state = replay_engine.pause_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state.to_dict()


@app.post("/replay/resume")
async def resume_replay(session_id: str = "default"):
    state = replay_engine.resume_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state.to_dict()


@app.post("/replay/stop")
async def stop_replay(session_id: str = "default"):
    state = replay_engine.stop_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state.to_dict()


@app.post("/replay/degrade")
async def degrade_replay(session_id: str = "default", degradation: str = "D1_30m"):
    state = replay_engine.set_degradation(session_id, degradation)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state.to_dict()


# --- WebSocket Streaming ---

@app.websocket("/ws/replay/{session_id}")
async def replay_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    replay_engine.register_client(session_id, websocket)
    try:
        # Send initial status
        state = replay_engine.sessions.get(session_id)
        if state:
            await websocket.send_json({"type": "INIT", "state": state.to_dict()})
        while True:
            # Keep socket alive and accept client control messages
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                if action == "pause":
                    replay_engine.pause_session(session_id)
                elif action == "resume":
                    replay_engine.resume_session(session_id)
                elif action == "stop":
                    replay_engine.stop_session(session_id)
                elif action == "degrade":
                    replay_engine.set_degradation(session_id, msg.get("degradation", "D0"))
            except Exception as e:
                logger.error(f"WebSocket parse error: {e}")
    except WebSocketDisconnect:
        replay_engine.unregister_client(session_id, websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("services.backend.main:app", host="0.0.0.0", port=8000, reload=False)
