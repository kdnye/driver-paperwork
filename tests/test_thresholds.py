import pytest

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


@pytest.mark.parametrize(
    "current,limit,buff,state",
    [
        (90, 100, 0.9, "warning"),
        (89.99, 100, 0.9, "ok"),
        (95, 100, 0.95, "warning"),
        (94.99, 100, 0.95, "ok"),
    ],
)
def test_weight_warning_buffer_boundaries(current, limit, buff, state):
    result = evaluate_weight_limit(current_weight_lbs=current, limit_lbs=limit, warning_buffer_pct=buff)
    assert result.state == state


@pytest.mark.parametrize(
    "current,cap,buff,state",
    [
        (900, 1000, 0.9, "warning"),
        (899.99, 1000, 0.9, "ok"),
        (975, 1000, 0.975, "warning"),
        (974.99, 1000, 0.975, "ok"),
    ],
)
def test_budget_warning_buffer_boundaries(current, cap, buff, state):
    result = evaluate_budget_cap(current_total=current, cap=cap, warning_buffer_pct=buff)
    assert result.state == state
