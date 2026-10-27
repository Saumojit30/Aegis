"""Standalone FastAPI inference microservice for decoupled container deployment."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from services.backend.inference.provider import InProcessInferenceProvider, MockInferenceProvider
from services.common.contracts import (
    PredictRequest,
    PredictResponse,
    SimulateRequest,
    SimulateResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aegis.inference")

app = FastAPI(
    title="Aegis Inference Microservice",
    description="Dedicated model forecasting service running Candidate S runtime bundle.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bundle_path = Path("artifacts/bundle")
if bundle_path.exists():
    provider = InProcessInferenceProvider(bundle_path)
    logger.info("Initialized InProcessInferenceProvider with artifacts/bundle")
else:
    provider = MockInferenceProvider()
    logger.warning("artifacts/bundle not found; falling back to MockInferenceProvider")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "aegis-inference",
        "provider": provider.__class__.__name__,
    }


@app.get("/info")
def model_info():
    if hasattr(provider, "bundle") and provider.bundle is not None:
        return provider.bundle.metadata
    return {"model": "mock", "version": "v0"}


@app.post("/predict", response_model=PredictResponse)
async def predict_endpoint(request: PredictRequest):
    try:
        return await provider.predict(request)
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate", response_model=SimulateResponse)
async def simulate_endpoint(request: SimulateRequest):
    try:
        return await provider.simulate(request)
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("services.inference.main:app", host="0.0.0.0", port=8001, reload=False)
