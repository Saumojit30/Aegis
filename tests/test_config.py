"""Unit tests for Aegis configuration parsing and validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from aegis.common.config import (
    AppConfig,
    DataConfig,
    SystemSettings,
    load_app_config,
    load_yaml_file,
)


def test_system_settings_defaults():
    settings = SystemSettings()
    assert settings.environment == "development"
    assert settings.inference_mode == "inprocess"
    assert settings.seed == 42
    assert settings.backend_port == 8000


def test_system_settings_negative_seed_fails():
    with pytest.raises(ValidationError):
        SystemSettings(seed=-1)


def test_system_settings_invalid_inference_mode_fails():
    with pytest.raises(ValidationError):
        SystemSettings(inference_mode="invalid_mode")  # type: ignore


def test_data_config_defaults():
    cfg = DataConfig()
    assert cfg.sampling_interval_min == 5
    assert cfg.forecast_horizon_min == 180
    assert cfg.history_window_min == 60


def test_load_yaml_file(tmp_path: Path):
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("data:\n  sampling_interval_min: 10\n", encoding="utf-8")
    loaded = load_yaml_file(yaml_file)
    assert loaded["data"]["sampling_interval_min"] == 10


def test_load_yaml_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_yaml_file("non_existent_file.yaml")


def test_load_app_config_with_base_yaml():
    base_yaml = Path(__file__).parent.parent / "configs" / "base.yaml"
    assert base_yaml.exists()
    app_cfg = load_app_config(base_yaml)
    assert isinstance(app_cfg, AppConfig)
    assert app_cfg.data.sampling_interval_min == 5
    assert app_cfg.model.model_type == "gru_fusion"
    assert app_cfg.system.inference_mode in ["inprocess", "http"]
