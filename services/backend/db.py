"""Database session management and initial data seeder."""

from __future__ import annotations

import datetime
import logging
import os
from pathlib import Path
from typing import Generator

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from aegis.models.pharmacology import estimate_cir, estimate_homa_ir, estimate_isf
from services.backend.models import Base, MealModel, PatientModel

logger = logging.getLogger(__name__)

# Default to SQLite for zero-configuration local runs, or PostgreSQL if configured
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aegis.db")
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize schema tables and perform lightweight column migrations if needed."""
    Base.metadata.create_all(bind=engine)
    # Ensure all clinical biomarker columns exist in SQLite/PostgreSQL
    try:
        with engine.connect() as conn:
            cols = []
            if "sqlite" in DATABASE_URL:
                res = conn.execute(text("PRAGMA table_info(patients)")).fetchall()
                cols = [r[1] for r in res]
            else:
                from sqlalchemy import inspect

                inspector = inspect(engine)
                cols = [c["name"] for c in inspector.get_columns("patients")]

            new_columns = [
                ("weight_kg", "FLOAT"),
                ("height_cm", "FLOAT"),
                ("fasting_insulin", "FLOAT"),
                ("triglycerides", "FLOAT"),
                ("hdl", "FLOAT"),
                ("ldl", "FLOAT"),
                ("homa_ir", "FLOAT"),
                ("isf", "FLOAT"),
                ("cir", "FLOAT"),
            ]
            for col_name, col_type in new_columns:
                if col_name not in cols:
                    conn.execute(text(f"ALTER TABLE patients ADD COLUMN {col_name} {col_type}"))
            conn.commit()
    except Exception as e:
        logger.warning(f"Schema column check: {e}")

    logger.info(f"Initialized database schema with URL: {DATABASE_URL}")


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_database_if_empty(
    processed_dir: Path | str = "data/processed",
) -> None:
    """Populates database with demo patients, observations, meals, and synthetic EHR extras."""
    db = SessionLocal()
    try:
        proc_p = Path(processed_dir)
        patients_p = proc_p / "patients.parquet"
        ehr_p = proc_p / "ehr_profiles.parquet"

        existing_patients = db.query(PatientModel).all()
        if existing_patients:
            # Backfill any missing biomarker columns for existing records
            if patients_p.exists():
                patients_df = pd.read_parquet(patients_p).set_index("patient_id")
                updated = False
                for ep in existing_patients:
                    if (
                        ep.weight_kg is None
                        or ep.isf is None
                        or ep.cir is None
                        or ep.homa_ir is None
                    ) and ep.patient_id in patients_df.index:
                        row = patients_df.loc[ep.patient_id]
                        if ep.weight_kg is None:
                            ep.weight_kg = (
                                float(row["weight_kg"]) if pd.notna(row.get("weight_kg")) else None
                            )
                        if ep.height_cm is None:
                            ep.height_cm = (
                                float(row["height_cm"]) if pd.notna(row.get("height_cm")) else None
                            )
                        if ep.fasting_insulin is None:
                            ep.fasting_insulin = (
                                float(row["fasting_insulin"])
                                if pd.notna(row.get("fasting_insulin"))
                                else None
                            )
                        if ep.triglycerides is None:
                            ep.triglycerides = (
                                float(row["triglycerides"])
                                if pd.notna(row.get("triglycerides"))
                                else None
                            )
                        if ep.hdl is None:
                            ep.hdl = float(row["hdl"]) if pd.notna(row.get("hdl")) else None
                        if ep.ldl is None:
                            ep.ldl = float(row["ldl"]) if pd.notna(row.get("ldl")) else None

                        if ep.homa_ir is None and ep.fasting_glucose and ep.fasting_insulin:
                            homa_val = estimate_homa_ir(ep.fasting_glucose, ep.fasting_insulin)
                            ep.homa_ir = round(homa_val, 2) if homa_val is not None else None
                        if ep.weight_kg and ep.weight_kg > 0:
                            if ep.isf is None:
                                ep.isf = round(estimate_isf(ep.weight_kg), 2)
                            if ep.cir is None:
                                ep.cir = round(estimate_cir(ep.weight_kg), 2)
                        updated = True
                if updated:
                    db.commit()
                    logger.info(
                        "Backfilled biomarker fields and clinical priors for existing patients."
                    )
            logger.info(f"Database already seeded with {len(existing_patients)} patients.")
            return

        logger.info("Seeding database with demo digital twin records...")

        # 1. Load profiles and synthetic EHR from processed parquets
        ehr_dict = {}
        if ehr_p.exists():
            ehr_df = pd.read_parquet(ehr_p)
            for _, r in ehr_df.iterrows():
                ehr_dict[str(r["patient_id"])] = {
                    "synthetic_pairing": bool(r.get("synthetic_pairing", True)),
                    "synthea_patient_id": str(r.get("synthea_patient_id", "")),
                    "diagnoses": r.get("diagnoses", []),
                    "medications": r.get("medications", []),
                    "pairing_distance": float(r.get("pairing_distance", 0.0)),
                }

        if patients_p.exists():
            patients_df = pd.read_parquet(patients_p)
            for _, row in patients_df.iterrows():
                pid = str(row["patient_id"])
                p_ehr = ehr_dict.get(pid, {})
                fg = (
                    float(row.get("fasting_glucose", 118.0))
                    if pd.notna(row.get("fasting_glucose"))
                    else 118.0
                )
                fi = (
                    float(row.get("fasting_insulin"))
                    if pd.notna(row.get("fasting_insulin"))
                    else None
                )
                w_kg = float(row.get("weight_kg")) if pd.notna(row.get("weight_kg")) else None
                h_cm = float(row.get("height_cm")) if pd.notna(row.get("height_cm")) else None
                tg = float(row.get("triglycerides")) if pd.notna(row.get("triglycerides")) else None
                hdl = float(row.get("hdl")) if pd.notna(row.get("hdl")) else None
                ldl = float(row.get("ldl")) if pd.notna(row.get("ldl")) else None

                homa_val = estimate_homa_ir(fg, fi)
                homa = round(homa_val, 2) if homa_val is not None else None
                isf_val = round(estimate_isf(w_kg), 2) if (w_kg and w_kg > 0) else None
                cir_val = round(estimate_cir(w_kg), 2) if (w_kg and w_kg > 0) else None

                patient = PatientModel(
                    patient_id=pid,
                    group=str(row.get("group", "T2D")),
                    age=float(row.get("age", 55)),
                    sex=str(row.get("sex", "female")),
                    bmi=float(row.get("bmi", 28.5)),
                    hba1c=float(row.get("hba1c", 6.8)),
                    fasting_glucose=fg,
                    weight_kg=w_kg,
                    height_cm=h_cm,
                    fasting_insulin=fi,
                    triglycerides=tg,
                    hdl=hdl,
                    ldl=ldl,
                    homa_ir=homa,
                    isf=isf_val,
                    cir=cir_val,
                    summary=f"Clinical Twin {pid}: {row.get('group', 'T2D')} diagnosis, HbA1c {row.get('hba1c', 6.8)}%",
                    ehr_extras=p_ehr,
                )
                db.add(patient)

        # 2. Load meals from meals.parquet
        meals_p = proc_p / "meals.parquet"
        if meals_p.exists():
            meals_df = pd.read_parquet(meals_p)
            for _, r in meals_df.iterrows():
                ts_val = r["ts_start"]
                ts_dt = (
                    pd.to_datetime(ts_val).to_pydatetime()
                    if pd.notna(ts_val)
                    else datetime.datetime.now(datetime.timezone.utc)
                )

                meal = MealModel(
                    meal_id=str(r["meal_id"]),
                    patient_id=str(r["patient_id"]),
                    ts_start=ts_dt,
                    name=f"Meal {r['meal_id']}",
                    meal_type=str(r.get("meal_type", "lunch")),
                    carbs_g=float(r.get("carbs_g", 50.0)),
                    protein_g=float(r.get("protein_g", 20.0)),
                    fat_g=float(r.get("fat_g", 15.0)),
                    fiber_g=float(r.get("fiber_g", 5.0)),
                    calories=float(r.get("calories", 400.0)),
                    amount_pct=float(r.get("amount_consumed_pct", 100.0)),
                )
                db.add(meal)

        db.commit()
        logger.info(
            f"Database successfully seeded with {db.query(PatientModel).count()} patients "
            f"and {db.query(MealModel).count()} meals."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed database: {e}")
    finally:
        db.close()
