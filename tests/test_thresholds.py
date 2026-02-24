from services.thresholds import evaluate_budget_cap, evaluate_weight_limit


def test_weight_limit_not_triggered():
    status = evaluate_weight_limit(current_weight_lbs=38000, limit_lbs=45000)
    assert status.name == "weight"
    assert status.triggered is False


def test_budget_cap_triggered():
    status = evaluate_budget_cap(current_total=12000, cap=10000)
    assert status.name == "budget"
    assert status.triggered is True
    assert "exceeded" in status.message
