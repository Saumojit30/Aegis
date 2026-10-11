"""Integration tests for FastAPI backend API, inference provider, and replay controls."""

import pytest
from fastapi.testclient import TestClient

from services.backend.main import app
from services.common.contracts import CLINICAL_DISCLAIMER


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_patients"] > 0
    assert data["disclaimer"] == CLINICAL_DISCLAIMER


def test_model_info_endpoint(client):
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "model_architecture" in data
    assert "disclaimer" in data


def test_list_and_get_patients(client):
    res_list = client.get("/patients")
    assert res_list.status_code == 200
    patients = res_list.json()
    assert len(patients) > 0

    first_pid = patients[0]["patient_id"]
    res_single = client.get(f"/patients/{first_pid}")
    assert res_single.status_code == 200
    p_data = res_single.json()
    assert p_data["patient_id"] == first_pid
    assert "profile" in p_data
    assert "ehr_extras" in p_data


def test_patient_state_and_similar(client):
    res = client.get("/patients/P001/state")
    assert res.status_code == 200
    state = res.json()
    assert state["patient_id"] == "P001"
    assert "stream" in state
    assert "personalisation" in state

    res_sim = client.get("/patients/P001/similar?k=2")
    assert res_sim.status_code == 200
    similar = res_sim.json()
    assert len(similar) <= 2
    for s in similar:
        assert s["patient_id"] != "P001"
        assert "similarity_score" in s


def test_meal_presets_endpoint(client):
    res = client.get("/meal-presets")
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) >= 4
    # Check Indian preset presence
    roti = next((p for p in presets if p["preset_id"] == "roti_dal_sabzi"), None)
    assert roti is not None
    assert roti["carbs_g"] == 48.0
    assert roti["support_score"] > 0.8


def test_predict_endpoint(client):
    payload = {
        "patient_id": "P001",
        "session_id": "test_s1",
        "t0": "2026-10-10T12:00:00Z",
        "meal": {
            "carbs_g": 55.0,
            "protein_g": 20.0,
            "fat_g": 12.0,
            "fiber_g": 6.0,
            "meal_type": "lunch",
            "amount_pct": 100.0,
        },
        "degradation": "D0",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["glucose"]) == 36
    assert len(data["horizon_min"]) == 36
    assert "interval" in data
    assert len(data["interval"]["lower"]) == 36
    assert len(data["interval"]["upper"]) == 36
    assert data["metrics"]["peak"] > 100.0
    assert data["reliability"]["label"] in ["high", "moderate", "low"]
    assert data["disclaimer"] == CLINICAL_DISCLAIMER


def test_simulate_endpoint(client):
    payload = {
        "patient_id": "P001",
        "session_id": "test_s1",
        "t0": "2026-10-10T12:00:00Z",
        "meal": {
            "carbs_g": 60.0,
            "protein_g": 18.0,
            "fat_g": 15.0,
            "fiber_g": 5.0,
            "meal_type": "dinner",
        },
        "degradation": "D0",
        "scenarios": [
            {"type": "portion", "amount_pct": 70.0},
            {"type": "walk", "minutes": 20},
            {"type": "sequencing"},
        ],
    }
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "baseline" in data
    assert len(data["scenarios"]) == 3

    # Check portion scenario is model_driven
    portion_sc = data["scenarios"][0]
    assert portion_sc["type"] == "portion"
    assert portion_sc["origin"] == "model_driven"
    assert portion_sc["delta_vs_baseline"]["delta_peak"] <= 0.0

    # Check walk scenario is assumption_driven
    walk_sc = data["scenarios"][1]
    assert walk_sc["type"] == "walk"
    assert walk_sc["origin"] == "assumption_driven"
    assert walk_sc["assumption"] is not None
    assert "Reynolds" in walk_sc["assumption"]["source"]


def test_replay_lifecycle(client):
    start_res = client.post("/replay/start?session_id=s_test&patient_id=P001&speed=20")
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "RUNNING"

    pause_res = client.post("/replay/pause?session_id=s_test")
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"

    resume_res = client.post("/replay/resume?session_id=s_test")
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "RUNNING"

    degrade_res = client.post("/replay/degrade?session_id=s_test&degradation=D1_30m")
    assert degrade_res.status_code == 200
    assert degrade_res.json()["active_degradation"] == "D1_30m"

    stop_res = client.post("/replay/stop?session_id=s_test")
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "STOPPED"
