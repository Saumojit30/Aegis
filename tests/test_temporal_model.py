"""Unit tests for PyTorch dataset, GRU fusion encoder, and loss functions."""

import torch

from aegis.models.dataset import MealForecastingDataset, collate_meal_batch
from aegis.models.gru_fusion import UnstructuredForecasterU
from aegis.training.train import masked_weighted_huber_loss


def _make_dummy_sample():
    return {
        "seq": [[0.1 * k for k in range(6)] for _ in range(12)],
        "static": [0.1 * k for k in range(8)],
        "meal": [0.2 * k for k in range(16)],
        "anchor": [1.0, 0.5, 0.2, 0.1],
        "target_deltas": [float(k) for k in range(36)],
        "target_mask": [1.0] * 36,
        "g_t0": 110.0,
        "patient_id": "P001",
        "meal_id": "M001",
    }


def test_dataset_and_collate():
    samples = [_make_dummy_sample() for _ in range(4)]
    dataset = MealForecastingDataset(samples)
    assert len(dataset) == 4

    batch = collate_meal_batch([dataset[0], dataset[1]])
    assert batch["seq"].shape == (2, 12, 6)
    assert batch["static"].shape == (2, 8)
    assert batch["meal"].shape == (2, 16)
    assert batch["anchor"].shape == (2, 4)
    assert batch["target"].shape == (2, 36)
    assert batch["target_mask"].shape == (2, 36)


def test_unstructured_forecaster_forward():
    model = UnstructuredForecasterU()
    seq = torch.randn(3, 12, 6)
    static = torch.randn(3, 8)
    meal = torch.randn(3, 16)
    anchor = torch.randn(3, 4)

    out = model(seq, static, meal, anchor)
    assert out.shape == (3, 36)
    assert not torch.isnan(out).any()


def test_masked_weighted_huber_loss():
    pred = torch.tensor([10.0, 20.0, 30.0], dtype=torch.float32)
    target = torch.tensor([10.0, 20.0, 30.0], dtype=torch.float32)
    mask = torch.tensor([1.0, 1.0, 0.0], dtype=torch.float32)

    loss_zero = masked_weighted_huber_loss(pred, target, mask)
    assert loss_zero.item() == 0.0

    # With under-prediction on high excursion
    pred_under = torch.tensor([10.0, 20.0, 20.0], dtype=torch.float32)
    target_high = torch.tensor([10.0, 20.0, 60.0], dtype=torch.float32)
    mask_all = torch.tensor([1.0, 1.0, 1.0], dtype=torch.float32)

    loss_high = masked_weighted_huber_loss(pred_under, target_high, mask_all)
    assert loss_high.item() > 0.0
