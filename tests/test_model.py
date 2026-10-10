"""Backtest against the worked example in the Immobilien-Kompass build plan (section 13).

If these numbers drift, the Python port no longer matches ``lib/model.ts``.
"""

import pytest

from dealkit.model import Inputs, assess

EXAMPLE = Inputs(purchase_price=300_000, living_area_m2=60, monthly_rent=1_200)


@pytest.fixture(scope="module")
def result():
    return assess(EXAMPLE)


def test_financing(result):
    f = result.financing
    assert f.total_investment == pytest.approx(324_000)
    assert f.equity_used == pytest.approx(80_000)
    assert f.remaining_liquidity == pytest.approx(15_000)
    assert f.loan == pytest.approx(244_000)
    assert f.monthly_payment == pytest.approx(1_220)
    assert f.ltv == pytest.approx(0.8133, abs=1e-4)


def test_operating(result):
    o = result.operating
    assert o.effective_rent == pytest.approx(1_164)
    assert o.owner_costs == pytest.approx(190)
    assert o.noi == pytest.approx(974)
    assert o.cash_flow == pytest.approx(-246)
    assert o.gross_yield == pytest.approx(0.048)
    assert o.net_yield == pytest.approx(0.0361, abs=1e-4)
    assert o.dscr == pytest.approx(0.80, abs=0.005)


def test_target_price(result):
    t = result.target_price
    assert t.cash_flow_limit == pytest.approx(254_444, abs=1)
    assert t.budget_limit == pytest.approx(285_714, abs=1)
    assert t.yield_limit == pytest.approx(320_000)
    assert t.target == pytest.approx(254_444, abs=1)
    assert t.binding == "cash_flow"


def test_stress(result):
    assert result.stress_cash_flow == pytest.approx(-737, abs=1)


@pytest.mark.parametrize(
    "horizon, value, debt, cum_cf, profit",
    [
        (5, 331_224, 217_038, -13_098, 11_151),
        (10, 365_698, 184_118, -21_870, 68_739),
        (15, 403_761, 162_981, -21_857, 126_809),
    ],
)
def test_base_scenario(result, horizon, value, debt, cum_cf, profit):
    s = next(s for s in result.scenarios if s.name == "basis" and s.horizon_years == horizon)
    assert s.property_value == pytest.approx(value, abs=1)
    assert s.remaining_debt == pytest.approx(debt, abs=1)
    assert s.cumulative_cash_flow == pytest.approx(cum_cf, abs=1)
    assert s.profit == pytest.approx(profit, abs=1)


def test_cash_purchase_has_no_dscr():
    r = assess(Inputs(purchase_price=50_000, living_area_m2=40, monthly_rent=500, equity_available=80_000, liquidity_reserve=10_000))
    assert r.financing.loan == 0
    assert r.operating.dscr is None
    assert r.financing.monthly_payment == 0


def test_full_vacancy_break_even_not_reachable():
    r = assess(Inputs(purchase_price=100_000, living_area_m2=40, monthly_rent=500, vacancy_rate=1.0))
    assert r.operating.break_even_rent is None
