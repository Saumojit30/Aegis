"""Multi-stream GRU fusion encoder and Unstructured Head (Candidate U)."""

from __future__ import annotations

import logging

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

HORIZON_STEPS = 36


class GruFusionEncoder(nn.Module):
    """Encodes sequence, static, meal, and anchor streams into a fused latent representation."""

    def __init__(
        self,
        seq_input_dim: int = 6,
        seq_hidden_dim: int = 32,
        static_dim: int = 8,
        static_hidden_dim: int = 16,
        meal_dim: int = 16,
        meal_hidden_dim: int = 16,
        anchor_dim: int = 4,
        fusion_hidden_dim: int = 32,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()

        # 1. Sequence GRU Encoder
        self.gru = nn.GRU(
            input_size=seq_input_dim,
            hidden_size=seq_hidden_dim,
            num_layers=1,
            batch_first=True,
        )

        # 2. Static Clinical Profile MLP
        self.static_mlp = nn.Sequential(
            nn.Linear(static_dim, static_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # 3. Meal Composition MLP
        self.meal_mlp = nn.Sequential(
            nn.Linear(meal_dim, meal_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # 4. Fusion Layer
        concat_dim = seq_hidden_dim + static_hidden_dim + meal_hidden_dim + anchor_dim
        self.fusion = nn.Sequential(
            nn.Linear(concat_dim, fusion_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

    def forward(
        self,
        seq: torch.Tensor,
        static: torch.Tensor,
        meal: torch.Tensor,
        anchor: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass through encoders.

        Returns:
            fused_features: [B, fusion_hidden_dim]
        """
        # GRU forward
        _, h_n = self.gru(seq)  # h_n: [1, B, seq_hidden_dim]
        h_seq = h_n.squeeze(0)  # [B, seq_hidden_dim]

        # MLPs
        h_static = self.static_mlp(static)
        h_meal = self.meal_mlp(meal)

        # Concat and fuse
        fused_in = torch.cat([h_seq, h_static, h_meal, anchor], dim=-1)
        fused = self.fusion(fused_in)
        return fused


class UnstructuredForecasterU(nn.Module):
    """Candidate U: Multi-stream encoder + direct unstructured MLP output head."""

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
        self.head = nn.Linear(fusion_hidden_dim, HORIZON_STEPS)

    def forward(
        self,
        seq: torch.Tensor,
        static: torch.Tensor,
        meal: torch.Tensor,
        anchor: torch.Tensor,
    ) -> torch.Tensor:
        """Predict 36-step delta trajectory ΔG(1..36)."""
        fused = self.encoder(seq, static, meal, anchor)
        out = self.head(fused)  # [B, 36]
        return out
