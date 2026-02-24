from dataclasses import dataclass
from typing import Literal


ThresholdState = Literal["ok", "warning", "blocked"]


@dataclass(frozen=True)
class ThresholdStatus:
    name: str
    state: ThresholdState
    message: str

    @property
    def triggered(self) -> bool:
        """Backward-compatible flag for blocked outcomes."""
        return self.state == "blocked"


def evaluate_weight_limit(
    current_weight_lbs: float,
    limit_lbs: float = 45000.0,
    warning_buffer_pct: float = 0.9,
) -> ThresholdStatus:
    if current_weight_lbs > limit_lbs:
        return ThresholdStatus(
            name="weight",
            state="blocked",
            message=f"Weight exceeds limit by {current_weight_lbs - limit_lbs:.1f} lbs",
        )

    warning_threshold = limit_lbs * warning_buffer_pct
    if current_weight_lbs >= warning_threshold:
        return ThresholdStatus(
            name="weight",
            state="warning",
            message=(
                f"Weight is approaching the {limit_lbs:.1f} lbs limit "
                f"({current_weight_lbs:.1f} lbs currently)."
            ),
        )

    return ThresholdStatus(
        name="weight",
        state="ok",
        message="Weight is within acceptable range",
    )


def evaluate_budget_cap(
    current_total: float,
    cap: float,
    warning_buffer_pct: float = 0.9,
) -> ThresholdStatus:
    if current_total > cap:
        return ThresholdStatus(
            name="budget",
            state="blocked",
            message=f"Budget cap exceeded by ${current_total - cap:,.2f}",
        )

    warning_threshold = cap * warning_buffer_pct
    if current_total >= warning_threshold:
        return ThresholdStatus(
            name="budget",
            state="warning",
            message=(
                f"Budget is nearing cap of ${cap:,.2f} "
                f"(${current_total:,.2f} currently)."
            ),
        )

    return ThresholdStatus(
        name="budget",
        state="ok",
        message="Budget is within cap",
    )
