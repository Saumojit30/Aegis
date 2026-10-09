"""Experiment tracking guardrails enforcing reproducible MLflow metadata.

Every model training or evaluation run must record:
- git_commit
- dataset_version
- feature_version
- config (or config_name)
- seed
Missing any required field raises a ValueError to prevent untracked numbers.
"""

from __future__ import annotations

import logging
import os
import subprocess
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

try:
    import mlflow
    from mlflow.entities import Run
except ImportError:
    mlflow = None  # type: ignore
    Run = Any  # type: ignore

logger = logging.getLogger(__name__)

REQUIRED_METADATA_KEYS = {
    "git_commit",
    "dataset_version",
    "feature_version",
    "config",
    "seed",
}


def get_git_commit(cwd: Optional[str] = None) -> str:
    """Retrieve the current git commit hash, or return a placeholder if not in git."""
    try:
        commit = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=cwd or os.path.dirname(__file__),
                stderr=subprocess.DEVNULL,
            )
            .decode("ascii")
            .strip()
        )
        return commit
    except Exception:
        return os.environ.get("GIT_COMMIT", "uncommitted_workspace")


def validate_run_metadata(metadata: Dict[str, Any]) -> None:
    """Validate that all mandatory tracking metadata keys are present and non-empty.

    Raises:
        ValueError: If any required key is missing or None.
    """
    missing = [
        key
        for key in REQUIRED_METADATA_KEYS
        if key not in metadata or metadata[key] is None or str(metadata[key]).strip() == ""
    ]
    if missing:
        raise ValueError(
            f"Cannot start untracked run. Missing mandatory metadata fields: {missing}. "
            f"All experiments must record: {sorted(REQUIRED_METADATA_KEYS)}."
        )


@contextmanager
def start_tracked_run(
    metadata: Dict[str, Any],
    experiment_name: Optional[str] = None,
    run_name: Optional[str] = None,
    tracking_uri: Optional[str] = None,
    **kwargs: Any,
) -> Generator[Optional[Run], None, None]:
    """Context manager for an MLflow run with strictly enforced reproducibility metadata.

    Args:
        metadata: Dictionary containing git_commit, dataset_version, feature_version, config, seed.
        experiment_name: Optional MLflow experiment name.
        run_name: Optional name for this specific run.
        tracking_uri: Optional MLflow tracking URI override.

    Yields:
        Active MLflow Run object.

    Raises:
        ValueError: If metadata is incomplete.
    """
    validate_run_metadata(metadata)

    if mlflow is None:
        logger.warning("MLflow is not installed. Running in mock tracking mode.")
        yield None
        return

    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    if experiment_name:
        mlflow.set_experiment(experiment_name)

    # Convert metadata to tags
    tags = {f"aegis.{k}": str(v) for k, v in metadata.items()}
    if "tags" in kwargs:
        tags.update(kwargs.pop("tags"))

    with mlflow.start_run(run_name=run_name, tags=tags, **kwargs) as active_run:
        # Also log seed and config as params
        mlflow.log_param("seed", metadata["seed"])
        mlflow.log_param("config", metadata["config"])
        mlflow.log_param("dataset_version", metadata["dataset_version"])
        mlflow.log_param("feature_version", metadata["feature_version"])
        yield active_run
