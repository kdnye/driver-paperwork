from dataclasses import dataclass


@dataclass(frozen=True)
class ThresholdStatus:
    name: str
    triggered: bool
    message: str


def evaluate_weight_limit(current_weight_lbs: float, limit_lbs: float = 45000.0) -> ThresholdStatus:
    triggered = current_weight_lbs > limit_lbs
    message = (
        f"Weight exceeds limit by {current_weight_lbs - limit_lbs:.1f} lbs"
        if triggered
        else "Weight is within acceptable range"
    )
    return ThresholdStatus(name="weight", triggered=triggered, message=message)


def evaluate_budget_cap(current_total: float, cap: float) -> ThresholdStatus:
    triggered = current_total > cap
    message = (
        f"Budget cap exceeded by ${current_total - cap:,.2f}"
        if triggered
        else "Budget is within cap"
    )
    return ThresholdStatus(name="budget", triggered=triggered, message=message)
