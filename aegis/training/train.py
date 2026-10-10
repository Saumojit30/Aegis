"""PyTorch training routine with masked weighted Huber loss and early stopping."""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from aegis.models.dataset import MealForecastingDataset, collate_meal_batch
from aegis.models.meal_head import StructuredMealForecasterS

logger = logging.getLogger(__name__)


def masked_weighted_huber_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor,
    delta: float = 10.0,
    underpredict_penalty: float = 1.5,
    high_excursion_threshold: float = 40.0,
) -> torch.Tensor:
    """Masked Huber loss with asymmetric penalty for under-predicting high post-prandial excursions."""
    diff = pred - target
    abs_diff = torch.abs(diff)

    # Standard Huber loss
    is_linear = abs_diff > delta
    huber = torch.where(
        is_linear,
        delta * (abs_diff - 0.5 * delta),
        0.5 * (diff**2),
    )

    # Asymmetric weighting: under-predicting when target excursion is high
    is_underpredict = (diff < 0.0) & (target > high_excursion_threshold)
    weights = torch.where(is_underpredict, underpredict_penalty, 1.0)

    # Apply valid target mask
    masked_loss = huber * weights * mask
    total_valid = torch.sum(mask) + 1e-6
    return torch.sum(masked_loss) / total_valid


def train_model(
    model: nn.Module,
    train_samples: List[Dict[str, Any]],
    val_samples: List[Dict[str, Any]],
    batch_size: int = 16,
    max_epochs: int = 50,
    lr: float = 0.001,
    weight_decay: float = 1e-4,
    patience: int = 10,
    residual_penalty_weight: float = 0.05,
    device: Optional[torch.device] = None,
) -> Tuple[nn.Module, Dict[str, List[float]]]:
    """Train temporal forecasting model with early stopping."""
    dev = device or torch.device("cpu")
    model = model.to(dev)

    train_loader = DataLoader(
        MealForecastingDataset(train_samples),
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_meal_batch,
    )
    val_loader = DataLoader(
        MealForecastingDataset(val_samples),
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate_meal_batch,
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5
    )

    history: Dict[str, List[float]] = {"train_loss": [], "val_loss": []}
    best_val_loss = float("inf")
    best_weights = copy.deepcopy(model.state_dict())
    patience_counter = 0

    for epoch in range(max_epochs):
        model.train()
        train_loss_total = 0.0
        n_batches = 0

        for batch in train_loader:
            seq = batch["seq"].to(dev)
            static = batch["static"].to(dev)
            meal = batch["meal"].to(dev)
            anchor = batch["anchor"].to(dev)
            target = batch["target"].to(dev)
            mask = batch["target_mask"].to(dev)

            optimizer.zero_grad()

            if isinstance(model, StructuredMealForecasterS):
                pred, residual_out = model(seq, static, meal, anchor)
                loss = masked_weighted_huber_loss(pred, target, mask)
                # L2 penalty on residual output
                res_loss = torch.mean(residual_out**2)
                total_loss = loss + (residual_penalty_weight * res_loss)
            else:
                pred = model(seq, static, meal, anchor)
                total_loss = masked_weighted_huber_loss(pred, target, mask)

            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            train_loss_total += float(total_loss.item())
            n_batches += 1

        avg_train = train_loss_total / max(1, n_batches)
        history["train_loss"].append(avg_train)

        # Validation
        model.eval()
        val_loss_total = 0.0
        n_val_batches = 0

        with torch.no_grad():
            for batch in val_loader:
                seq = batch["seq"].to(dev)
                static = batch["static"].to(dev)
                meal = batch["meal"].to(dev)
                anchor = batch["anchor"].to(dev)
                target = batch["target"].to(dev)
                mask = batch["target_mask"].to(dev)

                if isinstance(model, StructuredMealForecasterS):
                    pred, _ = model(seq, static, meal, anchor)
                else:
                    pred = model(seq, static, meal, anchor)

                v_loss = masked_weighted_huber_loss(pred, target, mask)
                val_loss_total += float(v_loss.item())
                n_val_batches += 1

        avg_val = val_loss_total / max(1, n_val_batches)
        history["val_loss"].append(avg_val)
        scheduler.step(avg_val)

        if avg_val < best_val_loss:
            best_val_loss = avg_val
            best_weights = copy.deepcopy(model.state_dict())
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.debug("Early stopping triggered at epoch %d", epoch + 1)
                break

    model.load_state_dict(best_weights)
    model.eval()
    return model, history
