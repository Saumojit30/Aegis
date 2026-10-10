"""Reference baseline forecasters B0 through B4 for 36-step trajectory prediction."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.multioutput import MultiOutputRegressor

logger = logging.getLogger(__name__)

HORIZON_STEPS = 36


class BaselinePersistenceB0:
    """B0: Floor persistence baseline returning ΔG = 0 across all 36 steps."""

    def __init__(self) -> None:
        pass

    def fit(self, X: Any = None, y: Any = None) -> "BaselinePersistenceB0":
        return self

    def predict(self, n_samples: int = 1) -> np.ndarray:
        return np.zeros((n_samples, HORIZON_STEPS), dtype=np.float32)


class BaselinePopulationMeanB1:
    """B1: Population mean response curve grouped by meal type."""

    def __init__(self) -> None:
        self.global_mean_curve: np.ndarray = np.zeros(HORIZON_STEPS, dtype=np.float32)
        self.meal_type_means: Dict[str, np.ndarray] = {}

    def fit(self, samples: List[Dict[str, Any]]) -> "BaselinePopulationMeanB1":
        curves_by_type: Dict[str, List[np.ndarray]] = {}
        all_curves: List[np.ndarray] = []

        for s in samples:
            deltas = np.array(s["target_deltas"], dtype=np.float32)
            all_curves.append(deltas)

            # Determine meal type
            meal_vec = s["meal"]
            # one-hot is at indices 10..13 (breakfast, lunch, dinner, snack)
            m_types = ["breakfast", "lunch", "dinner", "snack"]
            m_type = "lunch"
            for idx, name in enumerate(m_types):
                if len(meal_vec) > 10 + idx and meal_vec[10 + idx] == 1.0:
                    m_type = name
                    break

            curves_by_type.setdefault(m_type, []).append(deltas)

        if all_curves:
            self.global_mean_curve = np.mean(all_curves, axis=0).astype(np.float32)

        for m_type, c_list in curves_by_type.items():
            self.meal_type_means[m_type] = np.mean(c_list, axis=0).astype(np.float32)

        return self

    def predict_one(self, meal_type: str = "lunch") -> np.ndarray:
        return self.meal_type_means.get(meal_type.lower(), self.global_mean_curve)

    def predict(self, samples: List[Dict[str, Any]]) -> np.ndarray:
        preds = []
        m_types = ["breakfast", "lunch", "dinner", "snack"]
        for s in samples:
            meal_vec = s["meal"]
            m_type = "lunch"
            for idx, name in enumerate(m_types):
                if len(meal_vec) > 10 + idx and meal_vec[10 + idx] == 1.0:
                    m_type = name
                    break
            preds.append(self.predict_one(m_type))
        return np.array(preds, dtype=np.float32)


class BaselineRidgeB2:
    """B2: Multi-output Ridge regression on static, meal, and anchor features."""

    def __init__(self, alpha: float = 1.0) -> None:
        self.model = Ridge(alpha=alpha)
        self.fitted = False

    def _prepare_features(
        self, samples: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        X_list = []
        y_list = []
        for s in samples:
            # Flatten tabular features: static [8] + meal [16] + anchor [4] = 28 dims
            feat = np.concatenate([s["static"], s["meal"], s["anchor"]])
            X_list.append(feat)
            if "target_deltas" in s:
                y_list.append(s["target_deltas"])

        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list, dtype=np.float32) if y_list else None
        return X, y

    def fit(self, samples: List[Dict[str, Any]]) -> "BaselineRidgeB2":
        X, y = self._prepare_features(samples)
        if y is not None:
            self.model.fit(X, y)
            self.fitted = True
        return self

    def predict(self, samples: List[Dict[str, Any]]) -> np.ndarray:
        if not self.fitted:
            return np.zeros((len(samples), HORIZON_STEPS), dtype=np.float32)
        X, _ = self._prepare_features(samples)
        return self.model.predict(X).astype(np.float32)


class BaselineGbdtB3:
    """B3: Strong gradient-boosted trees benchmark (HistGradientBoostingRegressor)."""

    def __init__(self, max_iter: int = 50, random_state: int = 42) -> None:
        base_estimator = HistGradientBoostingRegressor(max_iter=max_iter, random_state=random_state)
        self.model = MultiOutputRegressor(base_estimator)
        self.fitted = False

    def _prepare_features(
        self, samples: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        X_list = []
        y_list = []
        for s in samples:
            feat = np.concatenate([s["static"], s["meal"], s["anchor"]])
            X_list.append(feat)
            if "target_deltas" in s:
                y_list.append(s["target_deltas"])

        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list, dtype=np.float32) if y_list else None
        return X, y

    def fit(self, samples: List[Dict[str, Any]]) -> "BaselineGbdtB3":
        X, y = self._prepare_features(samples)
        if y is not None:
            self.model.fit(X, y)
            self.fitted = True
        return self

    def predict(self, samples: List[Dict[str, Any]]) -> np.ndarray:
        if not self.fitted:
            return np.zeros((len(samples), HORIZON_STEPS), dtype=np.float32)
        X, _ = self._prepare_features(samples)
        return self.model.predict(X).astype(np.float32)


class BaselinePatientMeanB4:
    """B4: Per-patient historical mean response (personalisation baseline)."""

    def __init__(self) -> None:
        self.patient_means: Dict[str, np.ndarray] = {}
        self.population_mean: np.ndarray = np.zeros(HORIZON_STEPS, dtype=np.float32)

    def fit(self, samples: List[Dict[str, Any]]) -> "BaselinePatientMeanB4":
        curves_by_patient: Dict[str, List[np.ndarray]] = {}
        all_curves = []

        for s in samples:
            pid = s["patient_id"]
            deltas = np.array(s["target_deltas"], dtype=np.float32)
            curves_by_patient.setdefault(pid, []).append(deltas)
            all_curves.append(deltas)

        if all_curves:
            self.population_mean = np.mean(all_curves, axis=0).astype(np.float32)

        for pid, c_list in curves_by_patient.items():
            self.patient_means[pid] = np.mean(c_list, axis=0).astype(np.float32)

        return self

    def predict(self, samples: List[Dict[str, Any]]) -> np.ndarray:
        preds = []
        for s in samples:
            pid = s["patient_id"]
            # Return patient's own mean curve, or population fallback
            pred = self.patient_means.get(pid, self.population_mean)
            preds.append(pred)
        return np.array(preds, dtype=np.float32)
