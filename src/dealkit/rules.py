"""Scoring and recommendation rules.

Two rule sets live side by side:

* ``kompass_v1`` – the original Kompass score (0–100) and five-step decision
  table, kept for backtesting against the TypeScript implementation.
* ``dealkit_v1`` – the reframed rules: *pruefen* / *beobachten* / *verwerfen*
  (never "kaufen"), with three hard overrides from the Kompass extension plan:

  1. missing critical data blocks a positive outcome,
  2. severe object/legal risks override a good financial score,
  3. every market statement is either sourced or flagged as an assumption
     (enforced upstream by the evidence schema; surfaced here as data quality).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .model import Assessment

DEFAULT_WEIGHTS = {"cash_flow": 25, "gross_yield": 20, "ltv": 20, "stress_cash_flow": 15, "checks": 20}


@dataclass
class DataQuality:
    critical_missing: list[str] = field(default_factory=list)
    critical_assumed: list[str] = field(default_factory=list)
    critical_estimated: list[str] = field(default_factory=list)
    weakest_status: str = "belegt"


STATUS_RANK = {"belegt": 0, "geschaetzt": 1, "angenommen": 2, "fehlend": 3}


def data_quality(listing: dict) -> DataQuality:
    core = listing.get("core", {})
    dq = DataQuality()
    worst = 0
    str_block = (listing.get("operating") or {}).get("short_term_rental") or {}
    for key in ("purchase_price", "living_area_m2", "monthly_rent"):
        node = core.get(key)
        status = (node or {}).get("status", "fehlend")
        value = (node or {}).get("value")
        if key == "monthly_rent" and value in (None, 0) and str_block.get("average_daily_rate", {}).get("value"):
            # Rent is derived from short-term-rental inputs: inherit their weakest status.
            statuses = [n.get("status", "angenommen") for n in str_block.values() if isinstance(n, dict)]
            status = max(statuses, key=lambda s: STATUS_RANK[s])
            value = str_block["average_daily_rate"]["value"]
        if status == "fehlend" or value in (None, 0):
            dq.critical_missing.append(key)
            status = "fehlend"
        elif status == "angenommen":
            dq.critical_assumed.append(key)
        elif status == "geschaetzt":
            dq.critical_estimated.append(key)
        worst = max(worst, STATUS_RANK[status])
    dq.weakest_status = next(k for k, v in STATUS_RANK.items() if v == worst)
    return dq


# ---------------------------------------------------------------------------
# Kompass v1 (section 11 + 12) – kept verbatim for backtests
# ---------------------------------------------------------------------------


def kompass_score(a: Assessment, confirmed_checks: int, weights: dict | None = None, max_ltv: float | None = None) -> int:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    x, f, o = a.inputs, a.financing, a.operating
    ltv_limit = max_ltv if max_ltv is not None else x.max_ltv
    cf_pts = max(0.0, w["cash_flow"] + min(0.0, o.cash_flow) / 20)
    yield_pts = w["gross_yield"] * min(1.0, o.gross_yield / x.target_gross_yield) if x.target_gross_yield > 0 else 0
    over_pp = max(0.0, (f.ltv - ltv_limit) * 100)
    ltv_pts = max(0.0, w["ltv"] - over_pp)
    stress_pts = max(0.0, w["stress_cash_flow"] + min(0.0, a.stress_cash_flow) / 30)
    check_pts = min(w["checks"], confirmed_checks * (w["checks"] / 5))
    return int(round(min(100, max(0, cf_pts + yield_pts + ltv_pts + stress_pts + check_pts))))


def kompass_decision(a: Assessment, core_confirmed: bool, confirmed_checks: int, score: int) -> str:
    x, f, o = a.inputs, a.financing, a.operating
    valid = (
        x.purchase_price > 0
        and x.living_area_m2 > 0
        and x.monthly_rent > 0
        and x.liquidity_reserve <= x.equity_available
        and (x.interest_rate + x.initial_amortisation) > 0
    )
    if not valid:
        return "daten_vervollstaendigen"
    if not core_confirmed or confirmed_checks < 5:
        return "weitere_pruefung_noetig"
    if f.ltv > x.max_ltv or o.cash_flow < -250:
        return "zu_diesem_preis_nicht_passend"
    if o.cash_flow >= 0 and a.stress_cash_flow >= -100 and score >= 70:
        return "vertieft_pruefen"
    return "preis_nachverhandeln"


# ---------------------------------------------------------------------------
# dealkit v1 – reframed
# ---------------------------------------------------------------------------

OUTCOMES = ("pruefen", "beobachten", "verwerfen", "daten_vervollstaendigen")


@dataclass
class Recommendation:
    outcome: str
    score: int
    reasons: list[str]
    watch_triggers: dict
    data_quality: DataQuality
    red_flags: dict


def recommend(a: Assessment, listing: dict, mandate: dict, red_flags: dict) -> Recommendation:
    limits = mandate.get("limits", {})
    strategy = mandate.get("strategy", {})
    weights = strategy.get("score_weights")
    min_cf = limits.get("min_cash_flow_monthly", -250)
    min_stress = limits.get("min_stress_cash_flow_monthly", -100)
    min_score = limits.get("min_score_for_review", 70)
    min_dscr = limits.get("min_dscr")
    triggers = mandate.get("watch_triggers", {})

    dq = data_quality(listing)
    f, o, t = a.financing, a.operating, a.target_price
    reasons: list[str] = []

    # Checks count only when *ok*; risks never earn points.
    ok_checks = len(red_flags.get("ok", []))
    total_checks = ok_checks + len(red_flags.get("open", [])) + len(red_flags.get("risks", []))
    confirmed_equiv = round(5 * ok_checks / total_checks) if total_checks else 0
    score = kompass_score(a, confirmed_equiv, weights, limits.get("max_ltv"))

    # Rule 1 – missing critical data
    if dq.critical_missing:
        reasons.append(f"Kritische Angaben fehlen: {', '.join(dq.critical_missing)}.")
        return Recommendation("daten_vervollstaendigen", score, reasons, {}, dq, red_flags)

    # Rule 2 – severe risks override finance
    sev = red_flags.get("max_risk_severity")
    if sev == "blocker":
        reasons.append("Blocker-Risiko festgestellt: " + "; ".join(r["id"] for r in red_flags["risks"] if r["severity"] == "blocker"))
        return Recommendation("verwerfen", score, reasons, {}, dq, red_flags)

    # Financial hard limits → watch instead of discard, with explicit triggers
    watch: dict = {}
    fails = []
    if f.ltv > a.inputs.max_ltv:
        fails.append(f"Beleihung {f.ltv:.1%} über Limit {a.inputs.max_ltv:.0%}")
    if o.cash_flow < min_cf:
        fails.append(f"Cashflow {o.cash_flow:,.0f}/Monat unter Limit {min_cf:,.0f}")
    if min_dscr is not None and o.dscr is not None and o.dscr < min_dscr:
        fails.append(f"DSCR {o.dscr:.2f} unter {min_dscr:.2f}")
    if fails:
        reasons.extend(fails)
        gap = a.inputs.purchase_price - t.target
        if t.target > 0 and gap > 0:
            watch["price_at_or_below"] = round(t.target)
            reasons.append(f"Zielpreis {t.target:,.0f} ({t.binding}); Angebot liegt {gap:,.0f} ({gap / a.inputs.purchase_price:.1%}) darüber.")
        if triggers.get("price_drop_pct"):
            watch["price_drop_pct"] = triggers["price_drop_pct"]
        if triggers.get("days_on_market_min"):
            watch["days_on_market_min"] = triggers["days_on_market_min"]
        # Discard when the gap is hopeless (> 25 %) – configurable later.
        if t.target > 0 and gap / a.inputs.purchase_price > 0.25:
            reasons.append("Abstand zum Zielpreis > 25 %: Nachverhandlung unrealistisch.")
            return Recommendation("verwerfen", score, reasons, {}, dq, red_flags)
        return Recommendation("beobachten", score, reasons, watch, dq, red_flags)

    # High risks (not blockers) or open blockers → review with conditions
    if sev == "hoch":
        reasons.append("Hohes Risiko offen: " + "; ".join(r["id"] for r in red_flags["risks"] if r["severity"] == "hoch"))
    if red_flags.get("open_blockers"):
        reasons.append("Blocker-Checks noch offen: " + ", ".join(red_flags["open_blockers"]))
    if dq.critical_assumed:
        reasons.append("Kernwerte nur angenommen: " + ", ".join(dq.critical_assumed))

    if o.cash_flow >= 0 and a.stress_cash_flow >= min_stress and score >= min_score:
        reasons.insert(0, f"Cashflow {o.cash_flow:,.0f}, Stress {a.stress_cash_flow:,.0f}, Score {score}: finanziell passend.")
        return Recommendation("pruefen", score, reasons, {}, dq, red_flags)

    reasons.insert(0, f"Finanziell grenzwertig (CF {o.cash_flow:,.0f}, Stress {a.stress_cash_flow:,.0f}, Score {score}).")
    if t.target > 0 and t.target < a.inputs.purchase_price:
        watch["price_at_or_below"] = round(t.target)
    return Recommendation("beobachten", score, reasons, watch, dq, red_flags)
