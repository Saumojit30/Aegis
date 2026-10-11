"""Single source of truth degradation scenarios (D0-D7)."""

from aegis.degradation.scenarios import (
    ALL_SCENARIOS,
    DegradationScenario,
    apply_degradation,
)

__all__ = [
    "ALL_SCENARIOS",
    "DegradationScenario",
    "apply_degradation",
]
