"""Unit tests for MLflow experiment tracking guardrails."""

import pytest

from aegis.common.tracking import (
    get_git_commit,
    start_tracked_run,
    validate_run_metadata,
)


def test_validate_run_metadata_success():
    valid_meta = {
        "git_commit": "abcdef123456",
        "dataset_version": "v1.0.0-hash123",
        "feature_version": "feat-v1",
        "config": "configs/train.yaml",
        "seed": 42,
    }
    # Should not raise
    validate_run_metadata(valid_meta)


def test_validate_run_metadata_missing_field():
    incomplete_meta = {
        "git_commit": "abcdef123456",
        "dataset_version": "v1.0.0-hash123",
        # missing feature_version
        "config": "configs/train.yaml",
        "seed": 42,
    }
    with pytest.raises(ValueError, match="Missing mandatory metadata fields"):
        validate_run_metadata(incomplete_meta)


def test_validate_run_metadata_empty_field():
    empty_meta = {
        "git_commit": "abcdef123456",
        "dataset_version": "",
        "feature_version": "feat-v1",
        "config": "configs/train.yaml",
        "seed": 42,
    }
    with pytest.raises(ValueError, match="Missing mandatory metadata fields"):
        validate_run_metadata(empty_meta)


def test_start_tracked_run_rejects_incomplete():
    with pytest.raises(ValueError):
        with start_tracked_run(metadata={"seed": 42}):
            pass


def test_get_git_commit():
    commit = get_git_commit()
    assert isinstance(commit, str)
    assert len(commit) > 0
