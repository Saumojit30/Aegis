"""Clinical reliability assessment rules and clinician-facing explanations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Union

from aegis.degradation.scenarios import DegradationScenario


class ReliabilityLevel(str, Enum):
    """Clinician-facing confidence levels."""

    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


@dataclass
class ReliabilityAssessment:
    """Detailed reliability outcome with explanatory rationale."""

    level: ReliabilityLevel
    score: float  # [0.0, 1.0] confidence score
    reasons: List[str]
    clinician_message: str
    scenario: str
    mean_interval_width: float
    is_safe_for_decision: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "score": round(self.score, 3),
            "reasons": self.reasons,
            "clinician_message": self.clinician_message,
            "scenario": self.scenario,
            "mean_interval_width": round(self.mean_interval_width, 1),
            "is_safe_for_decision": self.is_safe_for_decision,
        }


def assess_reliability(
    scenario: Union[DegradationScenario, str],
    mean_interval_width: float,
    k_personal_meals: int = 5,
    support_score: float = 1.0,
    has_wearables: bool = True,
    anchor_age_min: float = 0.0,
) -> ReliabilityAssessment:
    """Determines clinical reliability level and actionable explanation.

    Args:
        scenario: active degradation scenario ID (e.g. D0, D1_30m, D4).
        mean_interval_width: average 180-min conformal band width in mg/dL.
        k_personal_meals: count of observed meals for target patient.
        support_score: meal distribution support score (1.0 = nominal, <0.3 = OOD).
        has_wearables: whether HR and METs sensors are streaming.
        anchor_age_min: age of latest CGM observation in minutes.

    Returns:
        ReliabilityAssessment dataclass.
    """
    sc_str = scenario.value if isinstance(scenario, DegradationScenario) else str(scenario)
    reasons: List[str] = []

    # Check for hard LOW triggers
    is_reduced_sensor = sc_str == "D4" or anchor_age_min >= 60.0
    is_severe_dropout = "D1_60m" in sc_str or anchor_age_min >= 45.0
    is_out_of_support = sc_str == "D7" or support_score < 0.25
    is_excessive_width = mean_interval_width > 80.0
    is_cold_start = sc_str == "D6" or k_personal_meals == 0

    if is_reduced_sensor:
        reasons.append("Reduced-sensor mode: No historical CGM in window.")
    if is_severe_dropout:
        reasons.append(f"Severe CGM dropout (anchor age {anchor_age_min:.0f}m).")
    if is_out_of_support:
        reasons.append(f"Out of distribution meal (support score {support_score:.2f}).")
    if is_excessive_width:
        reasons.append(f"Large prediction uncertainty (width {mean_interval_width:.1f} mg/dL).")
    if is_cold_start:
        reasons.append("New patient cold-start (0 prior meals available).")

    if is_reduced_sensor:
        return ReliabilityAssessment(
            level=ReliabilityLevel.LOW,
            score=0.25,
            reasons=reasons,
            clinician_message="Estimate based on wearables and profile only - not suitable for treatment decisions.",
            scenario=sc_str,
            mean_interval_width=mean_interval_width,
            is_safe_for_decision=False,
        )

    if is_severe_dropout or is_out_of_support or is_excessive_width:
        return ReliabilityAssessment(
            level=ReliabilityLevel.LOW,
            score=0.35,
            reasons=reasons,
            clinician_message="Low confidence: High trajectory uncertainty or abnormal input. Use clinical judgment.",
            scenario=sc_str,
            mean_interval_width=mean_interval_width,
            is_safe_for_decision=False,
        )

    # Check for MODERATE triggers
    is_moderate_dropout = "D1" in sc_str or (10.0 < anchor_age_min < 45.0)
    is_gaps = "D2" in sc_str
    is_missing_wearables = sc_str == "D3" or not has_wearables
    is_few_meals = 1 <= k_personal_meals < 3
    is_moderate_width = 65.0 < mean_interval_width <= 80.0
    is_incomplete_meal = sc_str == "D5"

    if is_moderate_dropout:
        reasons.append(f"Stale CGM anchor ({anchor_age_min:.0f}m old).")
    if is_gaps:
        reasons.append("Intermittent CGM communication gaps observed.")
    if is_missing_wearables:
        reasons.append("Wearable telemetry (HR/METs) absent.")
    if is_few_meals:
        reasons.append(f"Limited personalisation history ({k_personal_meals} meal(s)).")
    if is_moderate_width:
        reasons.append(f"Moderate uncertainty envelope ({mean_interval_width:.1f} mg/dL).")
    if is_incomplete_meal:
        reasons.append("Meal macros estimated from population medians.")

    if len(reasons) > 0:
        return ReliabilityAssessment(
            level=ReliabilityLevel.MODERATE,
            score=0.68,
            reasons=reasons,
            clinician_message="Moderate confidence: Trajectory is reliable for trends, but caution advised for peak timing.",
            scenario=sc_str,
            mean_interval_width=mean_interval_width,
            is_safe_for_decision=True,
        )

    # Nominal HIGH confidence
    return ReliabilityAssessment(
        level=ReliabilityLevel.HIGH,
        score=0.92,
        reasons=["Active CGM stream", "Complete biometric sensors", f"Personalised on {k_personal_meals} meals"],
        clinician_message="High confidence: Calibrated trajectory backed by active sensors and clinical twin personalisation.",
        scenario=sc_str,
        mean_interval_width=mean_interval_width,
        is_safe_for_decision=True,
    )
