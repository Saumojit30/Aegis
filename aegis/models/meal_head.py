"""Structured fast/slow carbohydrate and fat absorption kinetic head (Candidate S)."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import torch
import torch.nn as nn

from aegis.models.gru_fusion import HORIZON_STEPS, GruFusionEncoder

logger = logging.getLogger(__name__)


class StructuredMealForecasterS(nn.Module):
    """Candidate S: Fusion encoder + fast/slow physiological absorption basis + residual head."""

    def __init__(
        self,
        seq_input_dim: int = 6,
        seq_hidden_dim: int = 32,
        static_dim: int = 8,
        meal_dim: int = 16,
        anchor_dim: int = 4,
        fusion_hidden_dim: int = 32,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()

        self.encoder = GruFusionEncoder(
            seq_input_dim=seq_input_dim,
            seq_hidden_dim=seq_hidden_dim,
            static_dim=static_dim,
            meal_dim=meal_dim,
            anchor_dim=anchor_dim,
            fusion_hidden_dim=fusion_hidden_dim,
            dropout=dropout,
        )

        # 1. Slow pool fraction predictor φ = sigmoid(w·ratios + b)
        # Input ratios from meal tensor: fat_ratio (idx 5), protein_ratio (idx 6), fiber_per_carb (idx 7)
        self.slow_fraction_mlp = nn.Sequential(
            nn.Linear(3, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid(),
        )

        # 2. Patient-specific insulin resistance / gain factor K_p = softplus(f(fusion))
        self.gain_head = nn.Sequential(
            nn.Linear(fusion_hidden_dim, 1),
            nn.Softplus(),
        )

        # 3. Learnable bounded parameters for fast/slow absorption basis curves
        # τ_fast in [20, 60] min (default ~40 min)
        self.raw_tau_fast = nn.Parameter(torch.tensor(0.0))
        # τ_slow in [60, 140] min (default ~90 min)
        self.raw_tau_slow = nn.Parameter(torch.tensor(0.0))
        # delay d0, d1
        self.raw_delay = nn.Parameter(torch.tensor(0.0))

        # 4. Residual MLP head to capture non-kinetic high-order patterns
        self.residual_head = nn.Sequential(
            nn.Linear(fusion_hidden_dim, 16),
            nn.ReLU(),
            nn.Linear(16, HORIZON_STEPS),
        )

        # Time grid: 5 to 180 min (36 steps)
        time_steps = torch.arange(1, HORIZON_STEPS + 1, dtype=torch.float32) * 5.0
        self.register_buffer("time_grid", time_steps)

    @property
    def base_tau_fast(self) -> float:
        """Nominal fast absorption pool time constant in minutes."""
        return float((20.0 + 40.0 * torch.sigmoid(self.raw_tau_fast)).detach().cpu().item())

    @property
    def base_tau_slow(self) -> float:
        """Nominal slow absorption pool time constant in minutes."""
        return float((60.0 + 80.0 * torch.sigmoid(self.raw_tau_slow)).detach().cpu().item())

    @property
    def base_delay(self) -> float:
        """Nominal absorption delay in minutes."""
        return float((5.0 + 35.0 * torch.sigmoid(self.raw_delay)).detach().cpu().item())

    def compute_phi(self, meal: torch.Tensor) -> float:
        """Computes nominal slow pool fraction phi from meal tensor."""
        with torch.no_grad():
            ratios = meal[:, 5:8] if meal.ndim == 2 else meal[5:8].unsqueeze(0)
            return float(self.slow_fraction_mlp(ratios).mean().detach().cpu().item())

    def _compute_basis_curves(
        self,
        batch_size: int,
        device: torch.device,
        tau_fast_override: Optional[float] = None,
        delay_override: Optional[float] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Compute normalized gamma basis curves for fast and slow pools over the 36-step grid.

        Returns:
            B_fast: [B, 36], B_slow: [B, 36]
        """
        # Bounded parameter conversions with optional overrides
        if tau_fast_override is not None:
            tau_fast = torch.as_tensor(tau_fast_override, dtype=torch.float32, device=device)
        else:
            tau_fast = 20.0 + 40.0 * torch.sigmoid(self.raw_tau_fast)  # [20, 60] min

        tau_slow = 60.0 + 80.0 * torch.sigmoid(self.raw_tau_slow)  # [60, 140] min

        if delay_override is not None:
            delay = torch.as_tensor(delay_override, dtype=torch.float32, device=device)
        else:
            delay = 5.0 + 35.0 * torch.sigmoid(self.raw_delay)  # [5, 40] min delay

        t = self.time_grid.unsqueeze(0).expand(batch_size, -1)  # [B, 36]

        # Fast pool gamma curve: B_fast(t) = (t / tau) * exp(1 - t / tau)
        ratio_fast = t / tau_fast
        b_fast = ratio_fast * torch.exp(1.0 - ratio_fast)

        # Slow pool delayed gamma curve
        t_delayed = torch.clamp(t - delay, min=0.0)
        ratio_slow = t_delayed / tau_slow
        b_slow = ratio_slow * torch.exp(1.0 - ratio_slow)

        return b_fast, b_slow

    def forward(
        self,
        seq: torch.Tensor,
        static: torch.Tensor,
        meal: torch.Tensor,
        anchor: torch.Tensor,
        tau_fast_override: Optional[float] = None,
        delay_override: Optional[float] = None,
        phi_override: Optional[float] = None,
        return_components: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor] | Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass.

        Returns:
            trajectory: [B, 36] total predicted delta glucose
            residual_out: [B, 36] residual component (for L2 regularization penalty)
            traj_kinetic (optional): [B, 36] structured physiological kinetic component
        """
        batch_size = seq.shape[0]
        device = seq.device

        fused = self.encoder(seq, static, meal, anchor)

        # 1. Slow fraction φ from meal ratios (indices 5, 6, 7) or explicit override
        if phi_override is not None:
            phi = torch.full(
                (batch_size, 1), float(phi_override), dtype=torch.float32, device=device
            )
        else:
            ratios = meal[:, 5:8]
            phi = self.slow_fraction_mlp(ratios)  # [B, 1]

        # 2. Patient gain K_p
        k_p = self.gain_head(fused)  # [B, 1]

        # 3. Carbs scale factor from meal tensor (index 1 is standardized carbs_g)
        # De-standardize roughly: carbs_g = carbs_z * 25 + 55
        carbs_eff = torch.clamp(meal[:, 1:2] * 25.0 + 55.0, min=5.0)  # [B, 1]

        # 4. Basis curves
        b_fast, b_slow = self._compute_basis_curves(
            batch_size,
            device,
            tau_fast_override=tau_fast_override,
            delay_override=delay_override,
        )  # [B, 36]

        # 5. Structured kinetic excursion
        # Trajectory_kinetic = K_p * (carbs / 50.0) * [(1 - phi) * B_fast + phi * B_slow] * 35.0
        kinetic_shape = (1.0 - phi) * b_fast + phi * b_slow
        traj_kinetic = k_p * (carbs_eff / 50.0) * kinetic_shape * 35.0

        # 6. Residual head
        residual_out = self.residual_head(fused)

        total_traj = traj_kinetic + residual_out
        if return_components:
            return total_traj, residual_out, traj_kinetic
        return total_traj, residual_out
