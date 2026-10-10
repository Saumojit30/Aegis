"""Run 5-fold cross-validation evaluation for baseline models B0-B4."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from aegis.common.tracking import get_git_commit, start_tracked_run

# Reconfigure stdout to utf-8 if possible
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from aegis.evaluation.metrics import (
    compute_patient_bootstrap_ci,
    compute_trajectory_metrics,
)
from aegis.models.baselines import (
    BaselineGbdtB3,
    BaselinePatientMeanB4,
    BaselinePersistenceB0,
    BaselinePopulationMeanB1,
    BaselineRidgeB2,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aegis.baselines")


def run_baseline_evaluation(
    processed_dir: Path | str = "data/processed",
    reports_dir: Path | str = "reports",
    seed: int = 42,
) -> Dict[str, Any]:
    src = Path(processed_dir)
    rep = Path(reports_dir)
    rep.mkdir(parents=True, exist_ok=True)

    # 1. Load samples, splits, and manifest
    with open(src / "samples.json", "r", encoding="utf-8") as f:
        samples: List[Dict[str, Any]] = json.load(f)

    with open(src / "splits.json", "r", encoding="utf-8") as f:
        splits: Dict[str, Any] = json.load(f)

    with open(src / "MANIFEST.json", "r", encoding="utf-8") as f:
        manifest: Dict[str, Any] = json.load(f)

    dataset_ver = manifest.get("dataset_version", "v1.0.0-unknown")
    git_hash = get_git_commit()

    tracking_meta = {
        "git_commit": git_hash,
        "dataset_version": dataset_ver,
        "feature_version": "v1.0-tabular",
        "config": "configs/base.yaml",
        "seed": seed,
    }

    baseline_names = ["B0_persistence", "B1_pop_mean", "B2_ridge", "B3_gbdt", "B4_patient_mean"]
    results_by_model: Dict[str, Dict[str, List[float]]] = {name: {} for name in baseline_names}
    patient_errors_by_model: Dict[str, Dict[str, List[float]]] = {
        name: {} for name in baseline_names
    }

    logger.info("Evaluating B0-B4 baselines across %d folds...", len(splits["folds"]))

    with start_tracked_run(
        metadata=tracking_meta, experiment_name="aegis-baselines", run_name="baselines-5fold"
    ):
        for fold in splits["folds"]:
            fold_idx = fold["fold"]
            logger.debug("Processing fold %d", fold_idx)
            train_pids = set(fold["train_patients"])
            test_pids = set(fold["test_patients"])

            train_samples = [s for s in samples if s["patient_id"] in train_pids]
            test_samples = [s for s in samples if s["patient_id"] in test_pids]

            if not test_samples:
                continue

            # Instantiate and fit baselines
            models = {
                "B0_persistence": BaselinePersistenceB0().fit(),
                "B1_pop_mean": BaselinePopulationMeanB1().fit(train_samples),
                "B2_ridge": BaselineRidgeB2(alpha=1.0).fit(train_samples),
                "B3_gbdt": BaselineGbdtB3(max_iter=30, random_state=seed).fit(train_samples),
                "B4_patient_mean": BaselinePatientMeanB4().fit(train_samples),
            }

            for name, model in models.items():
                if name == "B0_persistence":
                    preds = model.predict(len(test_samples))
                else:
                    preds = model.predict(test_samples)

                for s_idx, s in enumerate(test_samples):
                    pid = s["patient_id"]
                    t_metrics = compute_trajectory_metrics(
                        pred_delta=preds[s_idx],
                        true_delta=s["target_deltas"],
                        mask=s["target_mask"],
                    )

                    for m_key, val in t_metrics.items():
                        results_by_model[name].setdefault(m_key, []).append(val)

                    # Track primary 0-120 MAE per patient for paired bootstrap
                    patient_errors_by_model[name].setdefault(pid, []).append(t_metrics["mae_0_120"])

    # 2. Compute aggregate summary and bootstrap CIs
    summary_report = [
        "# Aegis Baselines Evaluation Summary (Phase A3)",
        "",
        f"- **Dataset Version:** `{dataset_ver}`",
        f"- **Git Commit:** `{git_hash}`",
        "- **Evaluation Scheme:** 5-fold grouped cross-validation stratified at patient level",
        f"- **Sample Count:** {len(samples)} meals",
        "",
        "## Overall Held-Out Performance (Primary Window: 0–120 min)",
        "",
        "| Baseline ID | Description | MAE (0–120) [95% CI] | RMSE (0–120) | MAE (120–180) | Peak Error (mg/dL) |",
        "|---|---|---|---|---|---|",
    ]

    summary_data = {}
    for name in baseline_names:
        metrics = results_by_model[name]
        mean_mae_120, ci_low, ci_high = compute_patient_bootstrap_ci(
            patient_errors_by_model[name], seed=seed
        )
        mean_rmse_120 = round(float(np.mean(metrics.get("rmse_0_120", [0]))), 2)
        mean_mae_delayed = round(float(np.mean(metrics.get("mae_120_180", [0]))), 2)
        mean_peak_err = round(float(np.mean(metrics.get("peak_error", [0]))), 2)

        summary_data[name] = {
            "mae_0_120_mean": mean_mae_120,
            "mae_0_120_ci_lower": ci_low,
            "mae_0_120_ci_upper": ci_high,
            "rmse_0_120": mean_rmse_120,
            "mae_120_180": mean_mae_delayed,
            "peak_error": mean_peak_err,
        }

        desc_map = {
            "B0_persistence": "Persistence Floor (ΔG = 0)",
            "B1_pop_mean": "Population Meal Mean Curve",
            "B2_ridge": "Multi-Output Ridge Regression",
            "B3_gbdt": "Gradient Boosted Trees (HistGBDT)",
            "B4_patient_mean": "Per-Patient Historical Mean",
        }

        row = (
            f"| `{name}` | {desc_map[name]} | "
            f"**{mean_mae_120:.2f}** [{ci_low:.2f}, {ci_high:.2f}] | "
            f"{mean_rmse_120:.2f} | {mean_mae_delayed:.2f} | {mean_peak_err:.2f} |"
        )
        summary_report.append(row)

    report_text = "\n".join(summary_report) + "\n"
    out_file = rep / "baselines_summary.md"
    out_file.write_text(report_text, encoding="utf-8")
    logger.info("Baselines summary report generated at %s", out_file)
    print(report_text)

    return summary_data


if __name__ == "__main__":
    run_baseline_evaluation()
