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


def test_serve_dashboard(client):
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "Aegis" in res_root.text

    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 200
    assert "Aegis" in res_dash.text


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


def test_replay_jump_to_next_meal_and_real_data(client):
    start_res = client.post("/replay/start?session_id=s_jump&patient_id=P020&speed=10")
    assert start_res.status_code == 200
    assert start_res.json()["total_steps"] == 864  # Real 72 hours of 5-min intervals

    jump_res = client.post("/replay/jump?session_id=s_jump")
    assert jump_res.status_code == 200
    jump_state = jump_res.json()
    assert jump_state["cursor_idx"] > 0
    # Stop session
    client.post("/replay/stop?session_id=s_jump")


def test_predict_with_real_retrospective_sequence(client):
    # Pass 12 real telemetry points
    seq_pts = [
        {"glucose": 138.0 + i * 0.5, "hr": 70.0 + i, "mets": 1.1, "glucose_missing": False}
        for i in range(12)
    ]
    payload = {
        "patient_id": "P020",
        "session_id": "real_seq_test",
        "t0": "2026-10-01T08:00:00Z",
        "g_t0": 144.0,
        "retrospective_sequence": seq_pts,
        "meal": {
            "carbs_g": 65.0,
            "protein_g": 22.0,
            "fat_g": 18.0,
            "fiber_g": 5.0,
            "meal_type": "breakfast",
        },
        "degradation": "D0",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["glucose"]) == 36
    assert data["glucose"][0] > 140.0  # Grounded in g_t0 = 144.0
    assert data["metrics"]["peak"] >= 144.0


def test_patient_ingestion_and_biomarker_derivation(client):
    import uuid

    pid = f"P_INGEST_{uuid.uuid4().hex[:8]}"
    # 1. Create patient with weight and insulin to test 1800-rule and HOMA-IR auto-derivation
    payload = {
        "patient_id": pid,
        "group": "T2D",
        "age": 58.0,
        "sex": "male",
        "weight_kg": 80.0,
        "height_cm": 175.0,
        "fasting_glucose": 135.0,
        "fasting_insulin": 18.0,
        "hba1c": 7.4,
    }
    create_res = client.post("/patients", json=payload)
    assert create_res.status_code == 201
    p_data = create_res.json()
    assert p_data["patient_id"] == pid

    # Check auto-derived parameters
    prof = p_data["profile"]
    assert pytest.approx(prof["homa_ir"], rel=1e-2) == (135.0 * 18.0) / 405.0  # 6.0
    tdd_80 = 0.55 * 80.0
    assert pytest.approx(prof["isf"], rel=1e-2) == 1800.0 / tdd_80  # ~40.91
    assert pytest.approx(prof["cir"], rel=1e-2) == 500.0 / tdd_80  # ~11.36
    assert pytest.approx(prof["bmi"], rel=1e-1) == 80.0 / (1.75**2)  # ~26.1

    # Conflict on duplicate patient
    dup_res = client.post("/patients", json=payload)
    assert dup_res.status_code == 409

    # 2. Update biomarkers and verify recomputed derived parameters
    update_payload = {
        "weight_kg": 70.0,
        "fasting_glucose": 110.0,
        "fasting_insulin": 10.0,
    }
    put_res = client.put(f"/patients/{pid}/biomarkers", json=update_payload)
    assert put_res.status_code == 200
    updated_prof = put_res.json()["profile"]
    assert pytest.approx(updated_prof["homa_ir"], rel=1e-2) == (110.0 * 10.0) / 405.0  # ~2.72
    tdd_70 = 0.55 * 70.0
    assert pytest.approx(updated_prof["isf"], rel=1e-2) == 1800.0 / tdd_70  # ~46.75
    assert pytest.approx(updated_prof["cir"], rel=1e-2) == 500.0 / tdd_70  # ~12.99


def test_telemetry_and_meal_ingestion(client):
    import uuid

    pid = f"P_TEL_{uuid.uuid4().hex[:8]}"
    client.post("/patients", json={"patient_id": pid, "weight_kg": 75.0})

    # Ingest 3 telemetry points as list
    pts = [
        {"ts": "2026-10-20T10:00:00Z", "glucose": 115.0, "hr": 72.0, "mets": 1.0},
        {"ts": "2026-10-20T10:05:00Z", "glucose": 118.0, "hr": 74.0, "mets": 1.1},
        {"ts": "2026-10-20T10:10:00Z", "glucose": 122.0, "hr": 75.0, "mets": 1.2},
    ]
    res_tel = client.post(f"/patients/{pid}/telemetry", json=pts)
    assert res_tel.status_code == 201
    assert res_tel.json()["ingested_points"] == 3

    # Ingest meal
    meal_id = f"meal_{uuid.uuid4().hex[:8]}"
    meal_payload = {
        "meal_id": meal_id,
        "name": "Standard Test Lunch",
        "meal_type": "lunch",
        "carbs_g": 60.0,
        "protein_g": 25.0,
        "fat_g": 15.0,
        "fiber_g": 6.0,
        "amount_pct": 100.0,
    }
    res_meal = client.post(f"/patients/{pid}/meals", json=meal_payload)
    assert res_meal.status_code == 201
    m_data = res_meal.json()
    assert m_data["meal_id"] == meal_id
    # Calories auto-derived: 60*4 + 25*4 + 15*9 = 240 + 100 + 135 = 475
    assert m_data["calories"] == 475.0


def test_predict_with_db_profile_and_insulin(client):
    import uuid

    pid = f"P_PRED_{uuid.uuid4().hex[:8]}"
    client.post(
        "/patients",
        json={"patient_id": pid, "weight_kg": 75.0, "fasting_glucose": 125.0, "age": 60.0},
    )

    # 1. Baseline prediction without insulin
    base_payload = {
        "patient_id": pid,
        "session_id": "s_ins_test",
        "t0": "2026-10-20T12:00:00Z",
        "g_t0": 130.0,
        "meal": {
            "carbs_g": 70.0,
            "protein_g": 20.0,
            "fat_g": 10.0,
            "fiber_g": 4.0,
            "meal_type": "lunch",
        },
        "degradation": "D0",
    }
    res_no_ins = client.post("/predict", json=base_payload)
    assert res_no_ins.status_code == 200
    data_no_ins = res_no_ins.json()
    assert data_no_ins["iob_trajectory"] is None
    peak_no_ins = data_no_ins["metrics"]["peak"]

    # 2. Prediction with 4U rapid-acting bolus (pre-bolus 15 min prior) + basal rate increase
    ins_payload = dict(base_payload)
    ins_payload["insulin"] = {
        "bolus_units": 4.0,
        "bolus_time_min": -15.0,
        "insulin_type": "rapid_acting",
        "basal_rate_diff_u_hr": 0.2,
    }
    res_ins = client.post("/predict", json=ins_payload)
    assert res_ins.status_code == 200
    data_ins = res_ins.json()

    assert data_ins["iob_trajectory"] is not None
    assert len(data_ins["iob_trajectory"]) == 36
    assert data_ins["net_insulin_deflection"] is not None
    assert len(data_ins["net_insulin_deflection"]) == 36
    # Pharmacological insulin blunts glycemic excursion
    assert data_ins["metrics"]["peak"] < peak_no_ins


def test_simulate_with_insulin_scenario(client):
    payload = {
        "patient_id": "P001",
        "session_id": "s_sim_ins",
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
            {
                "type": "insulin",
                "bolus_units": 5.0,
                "bolus_time_min": 0.0,
                "basal_rate_diff_u_hr": 0.0,
            }
        ],
    }
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["scenarios"]) == 1
    sc = data["scenarios"][0]
    assert sc["type"] == "insulin"
    assert sc["origin"] == "model_driven"
    assert sc["delta_vs_baseline"]["delta_peak"] < 0.0


def test_biomarker_update_preserves_custom_priors_and_recomputes_bmi(client):
    import uuid

    pid = f"P_CUSTOM_{uuid.uuid4().hex[:8]}"
    create_res = client.post(
        "/patients",
        json={
            "patient_id": pid,
            "weight_kg": 75.0,
            "height_cm": 170.0,
            "isf": 32.5,
            "cir": 14.2,
            "fasting_glucose": 115.0,
            "fasting_insulin": 12.0,
        },
    )
    assert create_res.status_code == 201
    assert create_res.json()["profile"]["isf"] == 32.5
    assert create_res.json()["profile"]["cir"] == 14.2

    # Update only fasting_glucose — custom isf and cir must NOT be overwritten
    update_res = client.put(f"/patients/{pid}/biomarkers", json={"fasting_glucose": 130.0})
    assert update_res.status_code == 200
    up_prof = update_res.json()["profile"]
    assert up_prof["isf"] == 32.5
    assert up_prof["cir"] == 14.2

    # Update height only — BMI must be recomputed from existing weight and new height
    h_update_res = client.put(f"/patients/{pid}/biomarkers", json={"height_cm": 180.0})
    assert h_update_res.status_code == 200
    h_prof = h_update_res.json()["profile"]
    expected_bmi = round(75.0 / (1.80**2), 1)  # ~23.1
    assert pytest.approx(h_prof["bmi"], rel=1e-1) == expected_bmi


def test_predict_missing_telemetry_resilience(client):
    # Ensure None/missing values in retrospective_sequence do not cause TypeError crashes
    pts = [
        {"ts": f"2026-10-20T10:{i * 5:02d}:00Z", "glucose": None, "hr": None, "mets": None}
        for i in range(12)
    ]
    payload = {
        "patient_id": "P001",
        "session_id": "resilience_test",
        "t0": "2026-10-20T11:00:00Z",
        "g_t0": 125.0,
        "retrospective_sequence": pts,
        "meal": {
            "carbs_g": 45.0,
            "protein_g": 15.0,
            "fat_g": 10.0,
            "fiber_g": 4.0,
        },
        "degradation": "D0",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["glucose"]) == 36
    assert data["glucose"][0] > 120.0


def test_patient_state_and_prediction_with_db_telemetry(client):
    import uuid

    pid = f"P_TEL_STATE_{uuid.uuid4().hex[:8]}"
    client.post("/patients", json={"patient_id": pid, "weight_kg": 72.0})

    # Ingest 3 telemetry observations
    pts = [
        {"ts": "2026-10-25T11:50:00Z", "glucose": 135.0, "hr": 74.0, "mets": 1.1},
        {"ts": "2026-10-25T11:55:00Z", "glucose": 139.0, "hr": 76.0, "mets": 1.2},
        {"ts": "2026-10-25T12:00:00Z", "glucose": 145.0, "hr": 80.0, "mets": 1.4},
    ]
    client.post(f"/patients/{pid}/telemetry", json=pts)

    # 1. State endpoint should show latest observation from DB
    state_res = client.get(f"/patients/{pid}/state")
    assert state_res.status_code == 200
    stream = state_res.json()["stream"]
    assert stream["last_glucose"] == 145.0
    assert stream["hr"] == 80.0
    assert stream["mets"] == 1.4

    # 2. Predict without g_t0 should use latest DB observation glucose (145.0)
    pred_res = client.post(
        "/predict",
        json={
            "patient_id": pid,
            "session_id": "auto_db_seq",
            "t0": "2026-10-25T12:00:00Z",
            "meal": {"carbs_g": 50.0, "protein_g": 20.0, "fat_g": 10.0, "fiber_g": 5.0},
        },
    )
    assert pred_res.status_code == 200
    data = pred_res.json()
    assert data["glucose"][0] > 140.0


def test_simulate_dynamic_walk_glut4_clearance(client):
    payload = {
        "patient_id": "P001",
        "session_id": "walk_dyn_test",
        "t0": "2026-10-15T12:00:00Z",
        "meal": {
            "carbs_g": 70.0,
            "protein_g": 20.0,
            "fat_g": 10.0,
            "meal_type": "lunch",
        },
        "degradation": "D0",
        "scenarios": [
            {"type": "walk", "minutes": 30, "shift_min": 15},
        ],
    }
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    base_g = data["baseline"]["glucose"]
    walk_sc = data["scenarios"][0]
    walk_g = walk_sc["trajectory"]

    # Pre-walk preservation: for t <= t_start (first 3 steps: 5, 10, 15 min), glucose is preserved
    assert walk_g[0] == pytest.approx(base_g[0], abs=1e-2)
    assert walk_g[1] == pytest.approx(base_g[1], abs=1e-2)
    assert walk_g[2] == pytest.approx(base_g[2], abs=1e-2)

    # Post-walk attenuation: peak and late plateau drop significantly
    assert walk_sc["delta_vs_baseline"]["delta_peak"] < -5.0
    assert walk_sc["delta_vs_baseline"]["delta_delayed_mean"] < -5.0

    # Calibrated split-conformal intervals used (not fixed +-15.0)
    interval = walk_sc["interval"]
    widths = [upp - low for upp, low in zip(interval["upper"], interval["lower"])]
    # Conformal widths expand with time horizon
    assert widths[-1] > widths[0]
    assert walk_sc["assumption"]["kappa_exercise"] == 0.38
    assert walk_sc["assumption"]["tau_post_min"] == 25.0


def test_simulate_dynamic_food_sequencing(client):
    payload = {
        "patient_id": "P001",
        "session_id": "seq_dyn_test",
        "t0": "2026-10-15T12:00:00Z",
        "meal": {
            "carbs_g": 65.0,
            "protein_g": 22.0,
            "fat_g": 14.0,
            "fiber_g": 6.0,
            "meal_type": "dinner",
        },
        "degradation": "D0",
        "scenarios": [
            {"type": "sequencing"},
        ],
    }
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    base_g = data["baseline"]["glucose"]
    seq_sc = data["scenarios"][0]
    seq_g = seq_sc["trajectory"]
    assert seq_sc["type"] == "sequencing"
    assert seq_sc["origin"] == "model_driven"
    # GLP-1/PYY delayed gastric emptying via Candidate S overrides delays peak and blunts early excursion
    assert seq_sc["delta_vs_baseline"]["delta_time_to_peak"] >= 20
    # At 45 min post-meal (step 9), sequenced trajectory is substantially lower than baseline
    assert seq_g[8] < base_g[8] - 10.0
    assert abs(seq_sc["delta_vs_baseline"]["delta_peak"]) <= 3.0
    assert "GLP-1/PYY" in seq_sc["notes"]
    assert "delay_override" in seq_sc["assumption"]


def test_predict_with_portion_uncertainty_bounds(client):
    # Predict with 30% carbohydrate portion uncertainty
    payload = {
        "patient_id": "P001",
        "session_id": "portion_unc_test",
        "t0": "2026-10-15T12:00:00Z",
        "g_t0": 120.0,
        "portion_uncertainty_pct": 30.0,
        "meal": {
            "carbs_g": 60.0,
            "protein_g": 20.0,
            "fat_g": 12.0,
            "fiber_g": 5.0,
            "meal_type": "lunch",
        },
        "degradation": "D0",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    interval = data["interval"]
    assert interval["lower_bound_robust"] is not None
    assert interval["upper_bound_robust"] is not None
    assert len(interval["lower_bound_robust"]) == 36
    assert len(interval["upper_bound_robust"]) == 36

    # Robust bounds must envelop the standard conformal bounds
    for l_rob, l_std, u_std, u_rob in zip(
        interval["lower_bound_robust"],
        interval["lower"],
        interval["upper"],
        interval["upper_bound_robust"],
    ):
        assert l_rob <= l_std + 1e-4
        assert u_rob >= u_std - 1e-4

    # Peak interval width under portion uncertainty is wider
    rob_width = [
        upp - low
        for upp, low in zip(interval["upper_bound_robust"], interval["lower_bound_robust"])
    ]
    std_width = [upp - low for upp, low in zip(interval["upper"], interval["lower"])]
    assert max(rob_width) > max(std_width)


def test_standalone_inference_microservice_routes():
    from services.inference.main import app as inf_app

    with TestClient(inf_app) as inf_client:
        # 1. Health check
        h_res = inf_client.get("/health")
        assert h_res.status_code == 200
        assert h_res.json()["service"] == "aegis-inference"

        # 2. Predict endpoint
        pred_payload = {
            "patient_id": "P001",
            "session_id": "inf_micro_pred",
            "t0": "2026-10-15T12:00:00Z",
            "meal": {"carbs_g": 50.0, "meal_type": "lunch"},
        }
        p_res = inf_client.post("/predict", json=pred_payload)
        assert p_res.status_code == 200
        p_data = p_res.json()
        assert len(p_data["glucose"]) == 36

        # 3. Simulate endpoint (resolved 404 parity with backend)
        sim_payload = {
            "patient_id": "P001",
            "session_id": "inf_micro_sim",
            "t0": "2026-10-15T12:00:00Z",
            "meal": {"carbs_g": 50.0, "meal_type": "lunch"},
            "scenarios": [
                {"type": "portion", "amount_pct": 80.0},
                {"type": "walk", "minutes": 15},
            ],
        }
        s_res = inf_client.post("/simulate", json=sim_payload)
        assert s_res.status_code == 200
        s_data = s_res.json()
        assert "baseline" in s_data
        assert len(s_data["scenarios"]) == 2


@pytest.mark.asyncio
async def test_http_inference_provider_delegation():
    import httpx

    from services.backend.inference.provider import HttpInferenceProvider
    from services.common.contracts import (
        MealInput,
        PredictRequest,
        ScenarioModifier,
        SimulateRequest,
    )
    from services.inference.main import app as inf_app

    transport = httpx.ASGITransport(app=inf_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        http_prov = HttpInferenceProvider(service_url="http://testserver", client=client)

        # 1. Test predict delegation
        pred_req = PredictRequest(
            patient_id="P001",
            session_id="http_test",
            t0="2026-10-15T12:00:00Z",
            meal=MealInput(carbs_g=50.0, meal_type="lunch", portion_uncertainty_pct=20.0),
        )
        pred_res = await http_prov.predict(pred_req)
        assert len(pred_res.glucose) == 36
        assert pred_res.interval.lower_bound_robust is not None

        # 2. Test simulate delegation
        sim_req = SimulateRequest(
            patient_id="P001",
            session_id="http_sim_test",
            t0="2026-10-15T12:00:00Z",
            meal=MealInput(carbs_g=50.0, meal_type="lunch"),
            scenarios=[
                ScenarioModifier(type="portion", amount_pct=75.0),
                ScenarioModifier(type="walk", minutes=20, mets=4.0),
            ],
        )
        sim_res = await http_prov.simulate(sim_req)
        assert len(sim_res.scenarios) == 2
        assert sim_res.scenarios[0].type == "portion"
        assert sim_res.scenarios[1].type == "walk"


@pytest.mark.asyncio
async def test_mock_inference_provider_all_scenarios():
    from services.backend.inference.provider import MockInferenceProvider
    from services.common.contracts import MealInput, ScenarioModifier, SimulateRequest

    mock_prov = MockInferenceProvider()
    req = SimulateRequest(
        patient_id="P_MOCK",
        session_id="mock_sim",
        t0="2026-10-15T12:00:00Z",
        meal=MealInput(carbs_g=60.0, fat_g=15.0, protein_g=20.0, portion_uncertainty_pct=25.0),
        scenarios=[
            ScenarioModifier(type="portion", amount_pct=80.0),
            ScenarioModifier(type="walk", minutes=20, shift_min=10, mets=3.5),
            ScenarioModifier(type="sequencing"),
            ScenarioModifier(type="fat", delta_g=10.0),
            ScenarioModifier(type="insulin", bolus_units=3.0),
        ],
    )
    sim_res = await mock_prov.simulate(req)
    assert len(sim_res.scenarios) == 5

    # Check walk clearance
    walk_sc = sim_res.scenarios[1]
    assert walk_sc.delta_vs_baseline.delta_peak < 0.0
    assert walk_sc.interval.lower_bound_robust is not None

    # Check sequencing delayed peak
    seq_sc = sim_res.scenarios[2]
    assert seq_sc.delta_vs_baseline.delta_time_to_peak >= 0

    # Check insulin deflection
    ins_sc = sim_res.scenarios[4]
    assert ins_sc.delta_vs_baseline.delta_peak < 0.0


def test_simulate_walk_with_robust_bounds_and_zero_minutes(client):
    payload = {
        "patient_id": "P001",
        "session_id": "walk_bounds_test",
        "t0": "2026-10-15T12:00:00Z",
        "meal": {
            "carbs_g": 60.0,
            "protein_g": 20.0,
            "fat_g": 10.0,
            "portion_uncertainty_pct": 20.0,
        },
        "scenarios": [
            {"type": "walk", "minutes": 20, "shift_min": 15, "mets": 3.8},
            {"type": "walk", "minutes": 0},
        ],
    }
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    # 1. 20-min walk with robust bounds preserved
    w20 = data["scenarios"][0]
    assert w20["interval"]["lower_bound_robust"] is not None
    assert w20["interval"]["upper_bound_robust"] is not None
    assert len(w20["interval"]["lower_bound_robust"]) == 36
    # Robust lower bound should be <= standard lower bound
    assert w20["interval"]["lower_bound_robust"][10] <= w20["interval"]["lower"][10]

    # 2. 0-min walk preserves baseline exactly
    w0 = data["scenarios"][1]
    assert w0["delta_vs_baseline"]["delta_peak"] == 0.0
    assert w0["delta_vs_baseline"]["delta_time_to_peak"] == 0
