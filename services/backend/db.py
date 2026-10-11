"""Database session management and initial data seeder."""

from __future__ import annotations

import datetime
import logging
import os
from pathlib import Path
from typing import Generator

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.backend.models import Base, MealModel, PatientModel

logger = logging.getLogger(__name__)

# Default to SQLite for zero-configuration local runs, or PostgreSQL if configured
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aegis.db")
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize schema tables."""
    Base.metadata.create_all(bind=engine)
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
        existing_count = db.query(PatientModel).count()
        if existing_count > 0:
            logger.info(f"Database already seeded with {existing_count} patients.")
            return

        logger.info("Seeding database with demo digital twin records...")
        proc_p = Path(processed_dir)

        # 1. Load profiles and synthetic EHR from processed parquets
        patients_p = proc_p / "patients.parquet"
        ehr_p = proc_p / "ehr_profiles.parquet"

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
                patient = PatientModel(
                    patient_id=pid,
                    group=str(row.get("group", "T2D")),
                    age=float(row.get("age", 55)),
                    sex=str(row.get("sex", "female")),
                    bmi=float(row.get("bmi", 28.5)),
                    hba1c=float(row.get("hba1c", 6.8)),
                    fasting_glucose=float(row.get("fasting_glucose", 118.0)),
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
