"""Pytest session configuration and fixtures."""

from pathlib import Path

import pytest

from scripts.run_pipeline import run_pipeline
from services.backend.db import init_db, seed_database_if_empty


@pytest.fixture(scope="session", autouse=True)
def prepare_demo_data():
    """Ensure data/processed and demo database are present for tests."""
    proc = Path("data/processed")
    if not (proc / "patients.parquet").exists() or not (proc / "sensor_5min.parquet").exists():
        demo_dir = Path("data/demo")
        if (demo_dir / "bio.csv").exists():
            run_pipeline(data_dir="data/demo", output_dir="data/processed")
    init_db()
    seed_database_if_empty(processed_dir="data/processed")
