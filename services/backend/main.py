import datetime
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import Body, Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from aegis.features.extract import extract_static_features
from aegis.models.pharmacology import estimate_cir, estimate_homa_ir, estimate_isf
from aegis.personalisation.similarity import compute_patient_similarity_prior
from services.backend.db import get_db, init_db, seed_database_if_empty
from services.backend.inference.provider import (
    HttpInferenceProvider,
    InferenceProvider,
    InProcessInferenceProvider,
    MockInferenceProvider,
)
from services.backend.models import MealModel, ObservationModel, PatientModel
from services.backend.replay.engine import ReplayEngine
from services.common.contracts import (
    CLINICAL_DISCLAIMER,
    BiomarkerUpdateInput,
    MealCreateInput,
    PatientCreateInput,
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


# --- Patient Twins & Ingestion ---


@app.get("/patients")
def list_patients(db: Session = Depends(get_db)):
    patients = db.query(PatientModel).all()
    return [p.to_dict() for p in patients]


@app.post("/patients", status_code=201)
def create_patient(payload: PatientCreateInput, db: Session = Depends(get_db)):
    existing = db.query(PatientModel).filter(PatientModel.patient_id == payload.patient_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Patient {payload.patient_id} already exists.")

    fg = payload.fasting_glucose
    fi = payload.fasting_insulin
    homa_val = estimate_homa_ir(fg, fi)
    homa_ir = round(homa_val, 2) if homa_val is not None else None

    w_kg = payload.weight_kg
    h_cm = payload.height_cm
    bmi = payload.bmi
    if bmi is None and w_kg and h_cm:
        h_m = h_cm / 100.0
        if h_m > 0:
            bmi = round(w_kg / (h_m * h_m), 1)

    isf = payload.isf
    cir = payload.cir
    if w_kg and w_kg > 0:
        if isf is None:
            isf = round(estimate_isf(w_kg), 2)
        if cir is None:
            cir = round(estimate_cir(w_kg), 2)

    summary = (
        payload.summary
        or f"Clinical Twin {payload.patient_id}: {payload.group} diagnosis, HbA1c {payload.hba1c}%"
    )

    new_patient = PatientModel(
        patient_id=payload.patient_id,
        group=payload.group or "T2D",
        age=payload.age if payload.age is not None else 55.0,
        sex=payload.sex or "female",
        bmi=bmi if bmi is not None else 28.5,
        hba1c=payload.hba1c if payload.hba1c is not None else 6.5,
        fasting_glucose=fg if fg is not None else 115.0,
        weight_kg=w_kg,
        height_cm=h_cm,
        fasting_insulin=fi,
        triglycerides=payload.triglycerides,
        hdl=payload.hdl,
        ldl=payload.ldl,
        homa_ir=homa_ir,
        isf=isf,
        cir=cir,
        summary=summary,
        ehr_extras=payload.ehr_extras or {},
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient.to_dict()


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(PatientModel).filter(PatientModel.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")
    return p.to_dict()


@app.put("/patients/{patient_id}/biomarkers")
def update_patient_biomarkers(
    patient_id: str,
    payload: BiomarkerUpdateInput,
    db: Session = Depends(get_db),
):
    p = db.query(PatientModel).filter(PatientModel.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")

    if payload.fasting_glucose is not None:
        p.fasting_glucose = payload.fasting_glucose
    if payload.fasting_insulin is not None:
        p.fasting_insulin = payload.fasting_insulin
    if payload.hba1c is not None:
        p.hba1c = payload.hba1c
    if payload.weight_kg is not None:
        p.weight_kg = payload.weight_kg
    if payload.height_cm is not None:
        p.height_cm = payload.height_cm
    if payload.bmi is not None:
        p.bmi = payload.bmi
    elif (
        (payload.weight_kg is not None or payload.height_cm is not None)
        and p.weight_kg
        and p.height_cm
    ):
        h_m = p.height_cm / 100.0
        if h_m > 0:
            p.bmi = round(p.weight_kg / (h_m * h_m), 1)

    if payload.triglycerides is not None:
        p.triglycerides = payload.triglycerides
    if payload.hdl is not None:
        p.hdl = payload.hdl
    if payload.ldl is not None:
        p.ldl = payload.ldl

    # Recompute derived parameters
    homa_val = estimate_homa_ir(p.fasting_glucose, p.fasting_insulin)
    p.homa_ir = round(homa_val, 2) if homa_val is not None else None

    if payload.isf is not None:
        p.isf = payload.isf
    elif payload.weight_kg is not None and p.weight_kg and p.weight_kg > 0:
        p.isf = round(estimate_isf(p.weight_kg), 2)
    elif p.isf is None and p.weight_kg and p.weight_kg > 0:
        p.isf = round(estimate_isf(p.weight_kg), 2)

    if payload.cir is not None:
        p.cir = payload.cir
    elif payload.weight_kg is not None and p.weight_kg and p.weight_kg > 0:
        p.cir = round(estimate_cir(p.weight_kg), 2)
    elif p.cir is None and p.weight_kg and p.weight_kg > 0:
        p.cir = round(estimate_cir(p.weight_kg), 2)

    db.commit()
    db.refresh(p)
    return p.to_dict()


@app.post("/patients/{patient_id}/telemetry", status_code=201)
def ingest_telemetry(
    patient_id: str,
    payload: Any = Body(...),
    db: Session = Depends(get_db),
):
    p = db.query(PatientModel).filter(PatientModel.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")

    raw_points = []
    if isinstance(payload, list):
        raw_points = payload
    elif isinstance(payload, dict):
        if "points" in payload and isinstance(payload["points"], list):
            raw_points = payload["points"]
        else:
            raw_points = [payload]
    elif hasattr(payload, "points") and payload.points:
        raw_points = [pt.model_dump() if hasattr(pt, "model_dump") else pt for pt in payload.points]
    else:
        raw_points = [payload.model_dump() if hasattr(payload, "model_dump") else payload]

    ingested_count = 0
    for pt in raw_points:
        if isinstance(pt, BaseModel):
            pt = pt.model_dump()
        ts_val = pt.get("ts")
        if ts_val:
            try:
                ts_dt = datetime.datetime.fromisoformat(str(ts_val).replace("Z", "+00:00"))
            except Exception:
                ts_dt = datetime.datetime.now(datetime.timezone.utc)
        else:
            ts_dt = datetime.datetime.now(datetime.timezone.utc)

        obs = ObservationModel(
            patient_id=patient_id,
            ts=ts_dt,
            glucose=pt.get("glucose"),
            hr=pt.get("hr"),
            mets=pt.get("mets"),
            glucose_mask=float(
                pt.get("glucose_mask", 1.0) if pt.get("glucose_mask") is not None else 1.0
            ),
            hr_mask=float(pt.get("hr_mask", 1.0) if pt.get("hr_mask") is not None else 1.0),
            mets_mask=float(pt.get("mets_mask", 1.0) if pt.get("mets_mask") is not None else 1.0),
        )
        db.add(obs)
        ingested_count += 1

    db.commit()
    return {"status": "success", "patient_id": patient_id, "ingested_points": ingested_count}


@app.post("/patients/{patient_id}/meals", status_code=201)
def ingest_meal(
    patient_id: str,
    payload: MealCreateInput,
    db: Session = Depends(get_db),
):
    p = db.query(PatientModel).filter(PatientModel.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")

    meal_id = payload.meal_id or f"meal_{uuid.uuid4().hex[:10]}"
    if payload.ts_start:
        try:
            ts_dt = datetime.datetime.fromisoformat(payload.ts_start.replace("Z", "+00:00"))
        except Exception:
            ts_dt = datetime.datetime.now(datetime.timezone.utc)
    else:
        ts_dt = datetime.datetime.now(datetime.timezone.utc)

    calories = payload.calories
    if calories is None:
        calories = round(
            (payload.carbs_g * 4.0 + payload.protein_g * 4.0 + payload.fat_g * 9.0)
            * (payload.amount_pct / 100.0),
            1,
        )

    meal = MealModel(
        meal_id=meal_id,
        patient_id=patient_id,
        ts_start=ts_dt,
        name=payload.name or "Meal",
        meal_type=payload.meal_type or "lunch",
        carbs_g=payload.carbs_g,
        protein_g=payload.protein_g,
        fat_g=payload.fat_g,
        fiber_g=payload.fiber_g,
        calories=calories,
        amount_pct=payload.amount_pct,
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal.to_dict()


@app.get("/patients/{patient_id}/state")
def get_patient_state(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(PatientModel).filter(PatientModel.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")

    meal_count = db.query(MealModel).filter(MealModel.patient_id == patient_id).count()

    # Retrieve real telemetry from ingested observations, series, or active session
    curr_g, curr_hr, curr_mets = 120.0, 72.0, 1.0
    last_obs = (
        db.query(ObservationModel)
        .filter(ObservationModel.patient_id == patient_id)
        .order_by(ObservationModel.ts.desc())
        .first()
    )
    if last_obs:
        if last_obs.glucose is not None:
            curr_g = last_obs.glucose
        if last_obs.hr is not None:
            curr_hr = last_obs.hr
        if last_obs.mets is not None:
            curr_mets = last_obs.mets
    else:
        series = replay_engine.get_patient_series(patient_id)
        if series:
            curr_g = series[0]["glucose"]
            curr_hr = series[0]["hr"]
            curr_mets = series[0]["mets"]

    # Check if active session overrides
    for state in replay_engine.sessions.values():
        if state.patient_id == patient_id:
            curr_g = state.current_glucose
            curr_hr = state.current_hr
            curr_mets = state.current_mets
            break

    return {
        "patient_id": patient_id,
        "profile": p.to_dict()["profile"],
        "stream": {
            "last_glucose": curr_g,
            "hr": curr_hr,
            "mets": curr_mets,
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
    if not all_p:
        return []

    target_static = extract_static_features(target.to_dict()["profile"])
    ref_profiles = {p.patient_id: extract_static_features(p.to_dict()["profile"]) for p in all_p}

    bundle_alphas = {}
    if (
        hasattr(inference_provider, "bundle")
        and inference_provider.bundle
        and inference_provider.bundle.reference_alphas
    ):
        bundle_alphas = inference_provider.bundle.reference_alphas

    ref_alphas = {
        p.patient_id: bundle_alphas.get(p.patient_id, np.zeros(3, dtype=np.float32)) for p in all_p
    }

    _, neighbors = compute_patient_similarity_prior(
        target_pid=patient_id,
        target_static=target_static,
        reference_static_profiles=ref_profiles,
        reference_alphas=ref_alphas,
        k_neighbors=k,
        gamma=0.5,
    )

    p_map = {p.patient_id: p for p in all_p}
    results = []
    for n in neighbors:
        other = p_map.get(n["patient_id"])
        if other:
            results.append(
                {
                    "patient_id": n["patient_id"],
                    "distance": round(float(n["distance"]), 2),
                    "similarity_score": round(float(n["similarity"]), 3),
                    "normalized_weight": round(float(n.get("normalized_weight", 0.0)), 3),
                    "profile": other.to_dict()["profile"],
                }
            )
    return results


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


@app.post("/replay/jump")
async def jump_replay(session_id: str = "default"):
    state = replay_engine.jump_to_next_meal(session_id)
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
