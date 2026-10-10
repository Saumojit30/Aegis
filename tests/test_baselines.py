"""Unit tests for baseline forecasters B0 through B4."""

import numpy as np

from aegis.models.baselines import (
    BaselineGbdtB3,
    BaselinePatientMeanB4,
    BaselinePersistenceB0,
    BaselinePopulationMeanB1,
    BaselineRidgeB2,
)


def _make_dummy_samples(n: int = 10):
    samples = []
    for i in range(n):
        pid = f"P{i % 3 + 1}"
        static = [0.1 * k for k in range(8)]
        meal = [0.2 * k for k in range(16)]
        meal[10 + (i % 4)] = 1.0  # one-hot meal type
        anchor = [1.0, 0.5, 0.2, 0.1]
        target = [float(k) + i for k in range(36)]
        samples.append(
            {
                "patient_id": pid,
                "static": static,
                "meal": meal,
                "anchor": anchor,
                "target_deltas": target,
                "target_mask": [1.0] * 36,
            }
        )
    return samples


def test_b0_persistence():
    b0 = BaselinePersistenceB0().fit()
    preds = b0.predict(n_samples=5)
    assert preds.shape == (5, 36)
    assert (preds == 0.0).all()


def test_b1_population_mean():
    samples = _make_dummy_samples(8)
    b1 = BaselinePopulationMeanB1().fit(samples)
    preds = b1.predict(samples[:2])
    assert preds.shape == (2, 36)
    assert not np.isnan(preds).any()


def test_b2_ridge():
    samples = _make_dummy_samples(12)
    b2 = BaselineRidgeB2().fit(samples)
    preds = b2.predict(samples[:3])
    assert preds.shape == (3, 36)
    assert not np.isnan(preds).any()


def test_b3_gbdt():
    samples = _make_dummy_samples(12)
    b3 = BaselineGbdtB3(max_iter=10).fit(samples)
    preds = b3.predict(samples[:3])
    assert preds.shape == (3, 36)
    assert not np.isnan(preds).any()


def test_b4_patient_mean():
    samples = _make_dummy_samples(10)
    b4 = BaselinePatientMeanB4().fit(samples)
    preds = b4.predict(samples[:2])
    assert preds.shape == (2, 36)
    assert not np.isnan(preds).any()
