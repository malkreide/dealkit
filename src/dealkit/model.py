"""Deterministic financing, cash-flow and scenario engine.

Port of the Immobilien-Kompass model (``lib/model.ts``) to Python. Every
formula is documented with the symbol used in the Kompass build plan so the
two implementations can be cross-checked line by line.

The engine is intentionally free of any I/O, LLM or network dependency:
given the same inputs it always returns the same numbers. Percentages are
passed as decimals (4 % -> 0.04).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Inputs:
    """All inputs of the financing model (section 3 of the Kompass plan)."""

    purchase_price: float  # P
    living_area_m2: float  # A
    monthly_rent: float  # M (net cold rent)
    equity_available: float = 95_000.0  # E
    liquidity_reserve: float = 15_000.0  # R
    transfer_tax: float = 0.06  # part of N
    notary_land_registry: float = 0.02  # part of N
    buyer_commission: float = 0.0  # part of N
    renovation_one_off: float = 0.0  # U
    interest_rate: float = 0.04  # i
    initial_amortisation: float = 0.02  # t
    fixed_rate_years: int = 10
    follow_up_interest_rate: float = 0.055
    non_recoverable_costs_monthly: float = 100.0  # C
    maintenance_per_m2_monthly: float = 1.5  # h
    vacancy_rate: float = 0.03  # v
    value_growth: float = 0.02  # g_V
    rent_growth: float = 0.015  # g_M
    cost_growth: float = 0.02  # g_K
    selling_costs: float = 0.03  # k_sale
    max_ltv: float = 0.80  # l
    target_gross_yield: float = 0.045  # configurable (was hard-coded 4.5 %)

    @property
    def acquisition_cost_rate(self) -> float:
        """N = transfer tax + notary/land registry + commission."""
        return self.transfer_tax + self.notary_land_registry + self.buyer_commission


@dataclass(frozen=True)
class Financing:
    total_investment: float  # I
    equity_used: float  # E_ein
    loan: float  # D
    monthly_payment: float  # Q
    ltv: float  # D / P
    remaining_liquidity: float  # L


@dataclass(frozen=True)
class Operating:
    effective_rent: float  # M_eff
    owner_costs: float  # K
    noi: float  # NOI (monthly)
    cash_flow: float  # CF (monthly)
    gross_yield: float  # Y_brutto
    net_yield: float  # Y_netto on total investment
    dscr: float | None  # NOI / Q, None for cash purchase
    break_even_rent: float | None  # M_null, None if vacancy == 100 %


@dataclass(frozen=True)
class TargetPrice:
    cash_flow_limit: float  # P_CF
    budget_limit: float  # P_Budget
    yield_limit: float  # P_Rendite
    target: float  # P_Ziel
    binding: str  # which limit binds


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    horizon_years: int
    property_value: float  # V_T
    remaining_debt: float  # D_T
    cumulative_cash_flow: float  # sum CF_m
    net_sale_proceeds: float  # S_T
    profit: float  # G_T (nominal, pre-tax)


@dataclass(frozen=True)
class Assessment:
    inputs: Inputs
    financing: Financing
    operating: Operating
    target_price: TargetPrice
    stress_cash_flow: float
    scenarios: list[ScenarioResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Section 6 – financing
# ---------------------------------------------------------------------------


def financing(x: Inputs) -> Financing:
    n = x.acquisition_cost_rate
    total = x.purchase_price * (1 + n) + x.renovation_one_off  # I
    equity_used = min(max(0.0, x.equity_available - x.liquidity_reserve), total)  # E_ein
    loan = max(0.0, total - equity_used)  # D
    payment = loan * (x.interest_rate + x.initial_amortisation) / 12  # Q
    ltv = loan / x.purchase_price if x.purchase_price > 0 else 0.0
    return Financing(
        total_investment=total,
        equity_used=equity_used,
        loan=loan,
        monthly_payment=payment,
        ltv=ltv,
        remaining_liquidity=x.equity_available - equity_used,
    )


# ---------------------------------------------------------------------------
# Section 7 – yield and cash flow
# ---------------------------------------------------------------------------


def operating(x: Inputs, fin: Financing) -> Operating:
    m_eff = x.monthly_rent * (1 - x.vacancy_rate)
    k = x.non_recoverable_costs_monthly + x.maintenance_per_m2_monthly * x.living_area_m2
    noi = m_eff - k
    cf = noi - fin.monthly_payment
    gross = 12 * x.monthly_rent / x.purchase_price if x.purchase_price > 0 else 0.0
    net = 12 * noi / fin.total_investment if fin.total_investment > 0 else 0.0
    dscr = noi / fin.monthly_payment if fin.monthly_payment > 0 else None
    # Kompass used a technical fallback denominator at 100 % vacancy; we report
    # "not reachable" (None) instead, as its known-limits table recommends.
    break_even = (k + fin.monthly_payment) / (1 - x.vacancy_rate) if x.vacancy_rate < 1 else None
    return Operating(
        effective_rent=m_eff,
        owner_costs=k,
        noi=noi,
        cash_flow=cf,
        gross_yield=gross,
        net_yield=net,
        dscr=dscr,
        break_even_rent=break_even,
    )


# ---------------------------------------------------------------------------
# Section 8 – target purchase price
# ---------------------------------------------------------------------------


def target_price(x: Inputs, fin: Financing, op: Operating) -> TargetPrice:
    n = x.acquisition_cost_rate
    a = (x.interest_rate + x.initial_amortisation) / 12
    p_cf = (op.noi / a + fin.equity_used - x.renovation_one_off) / (1 + n) if a > 0 else float("inf")
    denom = 1 + n - x.max_ltv
    p_budget = (fin.equity_used - x.renovation_one_off) / denom if denom > 0 else float("inf")
    p_yield = 12 * x.monthly_rent / x.target_gross_yield if x.target_gross_yield > 0 else float("inf")
    limits = {"cash_flow": p_cf, "budget": p_budget, "yield": p_yield}
    binding = min(limits, key=limits.get)
    target = max(0.0, limits[binding])
    return TargetPrice(
        cash_flow_limit=p_cf,
        budget_limit=p_budget,
        yield_limit=p_yield,
        target=target,
        binding=binding,
    )


# ---------------------------------------------------------------------------
# Section 9 – immediate stress test
# ---------------------------------------------------------------------------


def stress_cash_flow(x: Inputs, fin: Financing, op: Operating) -> float:
    """CF_stress = 0.9 M - K - D (i + 0.02 + t) / 12."""
    return (
        0.9 * x.monthly_rent
        - op.owner_costs
        - fin.loan * (x.interest_rate + 0.02 + x.initial_amortisation) / 12
    )


# ---------------------------------------------------------------------------
# Section 10 – 5/10/15-year scenarios
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScenarioParams:
    name: str
    value_growth: float
    rent_growth: float
    vacancy_rate: float
    follow_up_interest_rate: float


def scenario_set(x: Inputs) -> list[ScenarioParams]:
    """Kompass scenario matrix: cautious / base / positive."""
    return [
        ScenarioParams("vorsichtig", -0.01, 0.0, 0.10, x.follow_up_interest_rate + 0.02),
        ScenarioParams("basis", x.value_growth, x.rent_growth, x.vacancy_rate, x.follow_up_interest_rate),
        ScenarioParams("positiv", x.value_growth + 0.02, x.rent_growth + 0.01, x.vacancy_rate, x.follow_up_interest_rate),
    ]


def simulate(x: Inputs, fin: Financing, op: Operating, sp: ScenarioParams, horizon_years: int) -> ScenarioResult:
    months = horizon_years * 12
    fixation_months = x.fixed_rate_years * 12
    debt = fin.loan
    payment = fin.monthly_payment
    rate_m = x.interest_rate / 12
    cum_cf = 0.0
    k0 = op.owner_costs
    for m in range(months):
        year = m // 12
        if m == fixation_months and debt > 0:
            rate_m = sp.follow_up_interest_rate / 12
            payment = debt * (sp.follow_up_interest_rate + x.initial_amortisation) / 12  # Q_neu
        rent_y = x.monthly_rent * (1 + sp.rent_growth) ** year
        cost_y = k0 * (1 + x.cost_growth) ** year
        if debt > 0:
            accrued = debt * (1 + rate_m)
            pay = min(payment, accrued)
            debt = max(0.0, accrued - pay)
        else:
            pay = 0.0
        cum_cf += rent_y * (1 - sp.vacancy_rate) - cost_y - pay
    value = x.purchase_price * (1 + sp.value_growth) ** horizon_years
    proceeds = value * (1 - x.selling_costs) - debt
    profit = proceeds + cum_cf - fin.equity_used
    return ScenarioResult(
        name=sp.name,
        horizon_years=horizon_years,
        property_value=value,
        remaining_debt=debt,
        cumulative_cash_flow=cum_cf,
        net_sale_proceeds=proceeds,
        profit=profit,
    )


def assess(x: Inputs, horizons: tuple[int, ...] = (5, 10, 15)) -> Assessment:
    fin = financing(x)
    op = operating(x, fin)
    tp = target_price(x, fin, op)
    stress = stress_cash_flow(x, fin, op)
    scenarios = [simulate(x, fin, op, sp, h) for sp in scenario_set(x) for h in horizons]
    return Assessment(inputs=x, financing=fin, operating=op, target_price=tp, stress_cash_flow=stress, scenarios=scenarios)
