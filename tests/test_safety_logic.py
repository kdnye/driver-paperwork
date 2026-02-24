import pytest
from app.services.thresholds import LogisticsThresholds, ThresholdStatus
from app.models import User, UserRole

def test_weight_thresholds():
    """Verify LTL weight limits and warning buffers."""
    # Test SAFE
    assert LogisticsThresholds.validate_shipment_weight(5000).status == ThresholdStatus.SAFE
    
    # Test WARNING (9000 lbs is 90% of 10k)
    warning_res = LogisticsThresholds.validate_shipment_weight(9500)
    assert warning_res.status == ThresholdStatus.WARNING
    assert "nearing maximum" in warning_res.message
    
    # Test BLOCKED
    blocked_res = LogisticsThresholds.validate_shipment_weight(11000)
    assert blocked_res.status == ThresholdStatus.BLOCKED

def test_budget_rbac_scaling():
    """Ensure supervisors have higher spending authority than employees."""
    emp_amount = 6000.00
    
    # Employee should be blocked at 6k
    emp_res = LogisticsThresholds.validate_budget(emp_amount, "EMPLOYEE")
    assert emp_res.status == ThresholdStatus.BLOCKED
    
    # Supervisor should be safe at 6k (limit is 10k)
    sup_res = LogisticsThresholds.validate_budget(emp_amount, "SUPERVISOR")
    assert sup_res.status == ThresholdStatus.SAFE
