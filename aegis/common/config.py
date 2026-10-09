"""Aegis typed configuration system using Pydantic and YAML loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SystemSettings(BaseSettings):
    """System-level runtime configuration and environment variables."""

    environment: Literal["development", "production", "testing"] = "development"
    log_level: str = "INFO"
    seed: int = 42

    # Inference topology: inprocess (D12 default) or standalone HTTP microservice
    inference_mode: Literal["inprocess", "http"] = "inprocess"
    inference_service_url: str = "http://localhost:8001"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    mlflow_tracking_uri: str = "./mlruns"
    mlflow_experiment_name: str = "aegis-t2d-forecast"

    database_url: str = "sqlite+aiosqlite:///./aegis_dev.db"

    # Replay configuration (Decision D13)
    replay_persist_all_observations: bool = False
    replay_tick_seconds: float = 1.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Seed must be a non-negative integer")
        return v


class DataConfig(BaseModel):
    """Data processing and feature extraction parameters."""

    sampling_interval_min: int = 5
    forecast_horizon_min: int = 180
    history_window_min: int = 60
    interpolation_limit_min: int = 15
    glucose_min_valid: float = 20.0
    glucose_max_valid: float = 600.0
    min_meal_separation_min: int = 180
    raw_data_dir: str = "data/raw/cgmacros"
    processed_data_dir: str = "data/processed"
    demo_data_dir: str = "data/demo"


class ModelHyperparameters(BaseModel):
    """Neural network and baseline model architecture settings."""

    model_type: Literal["gru_fusion", "ridge", "gbdt", "baseline_mean"] = "gru_fusion"
    seq_hidden_dim: int = 32
    static_hidden_dim: int = 16
    meal_hidden_dim: int = 16
    fusion_hidden_dim: int = 32
    dropout: float = 0.2
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    batch_size: int = 32
    max_epochs: int = 100
    patience: int = 10


class AssumptionModifier(BaseModel):
    """Configuration for assumption-driven scenario simulation."""

    name: str
    description: str
    source_citation: str
    peak_multiplier: float = 1.0
    time_to_peak_shift_min: int = 0
    delayed_window_multiplier: float = 1.0


class DegradationConfig(BaseModel):
    """Settings for calibrated degradation scenarios D0-D7."""

    scenario_id: str
    description: str
    simulated_dropout_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    cgm_staleness_threshold_min: int = 15
    wearable_missing: bool = False


class AppConfig(BaseModel):
    """Aggregated application and pipeline configuration."""

    system: SystemSettings = Field(default_factory=SystemSettings)
    data: DataConfig = Field(default_factory=DataConfig)
    model: ModelHyperparameters = Field(default_factory=ModelHyperparameters)
    assumptions: Dict[str, AssumptionModifier] = Field(default_factory=dict)
    degradations: Dict[str, DegradationConfig] = Field(default_factory=dict)


def load_yaml_file(file_path: str | Path) -> Dict[str, Any]:
    """Safely load and parse a YAML file."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def load_app_config(
    base_config_path: Optional[str | Path] = None,
    system_env: Optional[SystemSettings] = None,
) -> AppConfig:
    """Load and assemble complete AppConfig from YAML files and environment settings."""
    system = system_env or SystemSettings()

    data_cfg = DataConfig()
    model_cfg = ModelHyperparameters()
    assumptions = {}
    degradations = {}

    if base_config_path:
        raw_dict = load_yaml_file(base_config_path)
        if "data" in raw_dict:
            data_cfg = DataConfig.model_validate(raw_dict["data"])
        if "model" in raw_dict:
            model_cfg = ModelHyperparameters.model_validate(raw_dict["model"])

    return AppConfig(
        system=system,
        data=data_cfg,
        model=model_cfg,
        assumptions=assumptions,
        degradations=degradations,
    )
