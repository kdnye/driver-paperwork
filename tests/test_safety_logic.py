from app.services.thresholds import LogisticsThresholds, ThresholdStatus


def test_weight_thresholds_follow_warning_buffer_boundaries():
    warning_point = LogisticsThresholds.MAX_LTL_WEIGHT * LogisticsThresholds.WARNING_BUFFER

    assert LogisticsThresholds.validate_shipment_weight(warning_point - 1).status == ThresholdStatus.SAFE
    assert LogisticsThresholds.validate_shipment_weight(warning_point).status == ThresholdStatus.WARNING
    assert LogisticsThresholds.validate_shipment_weight(LogisticsThresholds.MAX_LTL_WEIGHT).status == ThresholdStatus.BLOCKED


def test_budget_role_scaling_and_blocked_thresholds():
    employee_limit = LogisticsThresholds.MAX_EXPENDITURE_LIMIT
    supervisor_limit = employee_limit * 2

    assert LogisticsThresholds.validate_budget(employee_limit, "EMPLOYEE").status == ThresholdStatus.SAFE
    assert LogisticsThresholds.validate_budget(employee_limit + 0.01, "EMPLOYEE").status == ThresholdStatus.BLOCKED

    assert LogisticsThresholds.validate_budget(supervisor_limit, "SUPERVISOR").status == ThresholdStatus.SAFE
    assert LogisticsThresholds.validate_budget(supervisor_limit + 0.01, "SUPERVISOR").status == ThresholdStatus.BLOCKED
