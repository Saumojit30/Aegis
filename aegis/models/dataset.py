"""PyTorch dataset and data loader for meal forecasting."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import torch
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


class MealForecastingDataset(Dataset):
    """PyTorch Dataset yielding formatted tensors for multi-stream trajectory forecasting."""

    def __init__(self, samples: List[Dict[str, Any]]) -> None:
        self.samples = samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        s = self.samples[idx]

        seq = torch.tensor(s["seq"], dtype=torch.float32)  # [12, 6]
        static = torch.tensor(s["static"], dtype=torch.float32)  # [8]
        meal = torch.tensor(s["meal"], dtype=torch.float32)  # [16]
        anchor = torch.tensor(s["anchor"], dtype=torch.float32)  # [4]

        target = torch.tensor(s.get("target_deltas", [0.0] * 36), dtype=torch.float32)  # [36]
        target_mask = torch.tensor(s.get("target_mask", [1.0] * 36), dtype=torch.float32)  # [36]
        g_t0 = torch.tensor(s.get("g_t0", 120.0), dtype=torch.float32)

        return {
            "seq": seq,
            "static": static,
            "meal": meal,
            "anchor": anchor,
            "target": target,
            "target_mask": target_mask,
            "g_t0": g_t0,
            "patient_id": s.get("patient_id", ""),
            "meal_id": s.get("meal_id", ""),
        }


def collate_meal_batch(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Collate list of samples into batched tensors."""
    return {
        "seq": torch.stack([item["seq"] for item in batch]),  # [B, 12, 6]
        "static": torch.stack([item["static"] for item in batch]),  # [B, 8]
        "meal": torch.stack([item["meal"] for item in batch]),  # [B, 16]
        "anchor": torch.stack([item["anchor"] for item in batch]),  # [B, 4]
        "target": torch.stack([item["target"] for item in batch]),  # [B, 36]
        "target_mask": torch.stack([item["target_mask"] for item in batch]),  # [B, 36]
        "g_t0": torch.stack([item["g_t0"] for item in batch]),  # [B]
        "patient_ids": [item["patient_id"] for item in batch],
        "meal_ids": [item["meal_id"] for item in batch],
    }
