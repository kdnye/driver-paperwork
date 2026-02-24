from services.thresholds import evaluate_budget_cap, evaluate_weight_limit


def test_weight_limit_below_buffer_is_ok():
    status = evaluate_weight_limit(current_weight_lbs=38000, limit_lbs=45000)
    assert status.name == "weight"
    assert status.state == "ok"
    assert status.triggered is False


def test_weight_limit_in_buffer_is_warning():
    status = evaluate_weight_limit(current_weight_lbs=43000, limit_lbs=45000)
    assert status.name == "weight"
    assert status.state == "warning"
    assert status.triggered is False
    assert "approaching" in status.message


def test_weight_limit_over_limit_is_blocked():
    status = evaluate_weight_limit(current_weight_lbs=46000, limit_lbs=45000)
    assert status.name == "weight"
    assert status.state == "blocked"
    assert status.triggered is True
    assert "exceeds" in status.message


def test_budget_cap_below_buffer_is_ok():
    status = evaluate_budget_cap(current_total=8000, cap=10000)
    assert status.name == "budget"
    assert status.state == "ok"
    assert status.triggered is False


def test_budget_cap_in_buffer_is_warning():
    status = evaluate_budget_cap(current_total=9500, cap=10000)
    assert status.name == "budget"
    assert status.state == "warning"
    assert status.triggered is False
    assert "nearing" in status.message


def test_budget_cap_over_limit_is_blocked():
    status = evaluate_budget_cap(current_total=12000, cap=10000)
    assert status.name == "budget"
    assert status.state == "blocked"
    assert status.triggered is True
    assert "exceeded" in status.message
