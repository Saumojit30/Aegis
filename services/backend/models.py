"""SQLAlchemy database models for Aegis digital twin platform."""

from __future__ import annotations

import datetime
from typing import Any, Dict

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class PatientModel(Base):
    """Clinical digital twin patient entity."""

    __tablename__ = "patients"

    patient_id = Column(String(32), primary_key=True)
    group = Column(String(32), default="T2D")
    age = Column(Float, default=55.0)
    sex = Column(String(16), default="female")
    bmi = Column(Float, default=28.5)
    hba1c = Column(Float, default=6.5)
    fasting_glucose = Column(Float, default=115.0)
    summary = Column(Text, nullable=True)
    ehr_extras = Column(JSON, default=dict)  # synthetic comorbidities, medications, BP history

    observations = relationship("ObservationModel", back_populates="patient", cascade="all, delete-orphan")
    meals = relationship("MealModel", back_populates="patient", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "group": self.group,
            "profile": {
                "age": self.age,
                "sex": self.sex,
                "bmi": self.bmi,
                "hba1c": self.hba1c,
                "fasting_glucose": self.fasting_glucose,
            },
            "summary": self.summary,
            "ehr_extras": self.ehr_extras or {},
        }


class ObservationModel(Base):
    """5-minute wearable biometric observation."""

    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(32), ForeignKey("patients.patient_id"), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    glucose = Column(Float, nullable=True)
    hr = Column(Float, nullable=True)
    mets = Column(Float, nullable=True)
    glucose_mask = Column(Float, default=1.0)
    hr_mask = Column(Float, default=1.0)
    mets_mask = Column(Float, default=1.0)

    patient = relationship("PatientModel", back_populates="observations")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "ts": self.ts.isoformat() if self.ts else None,
            "glucose": self.glucose,
            "hr": self.hr,
            "mets": self.mets,
            "glucose_mask": self.glucose_mask,
            "hr_mask": self.hr_mask,
            "mets_mask": self.mets_mask,
        }


class MealModel(Base):
    """Meal event with nutritional composition."""

    __tablename__ = "meals"

    meal_id = Column(String(64), primary_key=True)
    patient_id = Column(String(32), ForeignKey("patients.patient_id"), nullable=False, index=True)
    ts_start = Column(DateTime, nullable=False, index=True)
    name = Column(String(128), default="Meal")
    meal_type = Column(String(32), default="lunch")
    carbs_g = Column(Float, default=50.0)
    protein_g = Column(Float, default=20.0)
    fat_g = Column(Float, default=15.0)
    fiber_g = Column(Float, default=5.0)
    calories = Column(Float, default=400.0)
    amount_pct = Column(Float, default=100.0)

    patient = relationship("PatientModel", back_populates="meals")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meal_id": self.meal_id,
            "patient_id": self.patient_id,
            "ts_start": self.ts_start.isoformat() if self.ts_start else None,
            "name": self.name,
            "meal_type": self.meal_type,
            "carbs_g": self.carbs_g,
            "protein_g": self.protein_g,
            "fat_g": self.fat_g,
            "fiber_g": self.fiber_g,
            "calories": self.calories,
            "amount_pct": self.amount_pct,
        }


class ReplaySessionModel(Base):
    """Interactive clinician replay session."""

    __tablename__ = "replay_sessions"

    session_id = Column(String(64), primary_key=True)
    patient_id = Column(String(32), nullable=False)
    status = Column(String(32), default="IDLE")  # IDLE, RUNNING, PAUSED, STOPPED
    speed = Column(Integer, default=5)
    active_degradation = Column(String(32), default="D0")
    cursor_idx = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "status": self.status,
            "speed": self.speed,
            "active_degradation": self.active_degradation,
            "cursor_idx": self.cursor_idx,
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }


class PredictionLogModel(Base):
    """Audit log of generated forecasts and what-if simulations."""

    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=True, index=True)
    patient_id = Column(String(32), nullable=False, index=True)
    t0 = Column(DateTime, nullable=False)
    meal_id = Column(String(64), nullable=True)
    model_version = Column(String(64), default="Candidate_S")
    degradation = Column(String(32), default="D0")
    reliability = Column(String(32), default="HIGH")
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
