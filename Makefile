.PHONY: help setup test lint data train up demo clean

help:
	@echo "Aegis Project Automation Targets:"
	@echo "  make setup    - Install dependencies and setup local environment"
	@echo "  make test     - Run pytest test suite"
	@echo "  make lint     - Run ruff linter and code formatting checks"
	@echo "  make data     - Download, verify and process CGMacros dataset"
	@echo "  make train    - Train baseline and candidate forecasting models"
	@echo "  make up       - Start backend, mock/real inference, and dashboard"
	@echo "  make demo     - Run local offline clinician replay demo"
	@echo "  make clean    - Clean python build and test caches"

setup:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check aegis/ services/ tests/
	ruff format --check aegis/ services/ tests/

data:
	python -m aegis.data.download
	python -m aegis.data.clean
	python -m aegis.data.samples

train:
	python -m aegis.training.run_baselines
	python -m aegis.training.train

up:
	python -m uvicorn services.backend.main:app --host 0.0.0.0 --port 8000 --reload

demo:
	python scripts/run_demo.py

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('*.egg-info')]"
