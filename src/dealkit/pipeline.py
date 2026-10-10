"""Glue: listing + mandate -> assessment document (schema: assessment)."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime

from . import __version__
from .model import assess
from .profiles import get_profile
from .redflags import evaluate as evaluate_red_flags
from .rules import recommend
from .schema import lint_listing, validate


def screen(listing: dict, mandate: dict) -> dict:
    errors = validate(listing, "listing") + [f"mandate: {e}" for e in validate(mandate, "mandate")]
    if errors:
        raise ValueError("validation failed:\n  " + "\n  ".join(errors))

    market = listing["market"]
    allowed = {m["code"] for m in mandate["markets"]}
    profile = get_profile(market)
    inputs = profile.build_inputs(listing, mandate, profile)
    result = assess(inputs, horizons=tuple(sorted({5, 10, 15, mandate.get("strategy", {}).get("horizon_years", 10)})))
    flags = evaluate_red_flags(listing)
    rec = recommend(result, listing, mandate, flags)
    lints = lint_listing(listing)
    if market not in allowed:
        rec.reasons.append(f"Markt {market} ist nicht im Mandat ({sorted(allowed)}).")
        if rec.outcome == "pruefen":
            rec.outcome = "beobachten"

    return {
        "dealkit_version": __version__,
        "assessed_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "listing_id": listing["id"],
        "market": market,
        "profile": profile.name,
        "mandate": mandate["name"],
        "outcome": rec.outcome,
        "score": rec.score,
        "reasons": rec.reasons,
        "watch_triggers": rec.watch_triggers,
        "data_quality": asdict(rec.data_quality),
        "lints": lints,
        "red_flags": flags,
        "financing": asdict(result.financing),
        "operating": asdict(result.operating),
        "target_price": asdict(result.target_price),
        "stress_cash_flow": result.stress_cash_flow,
        "scenarios": [asdict(s) for s in result.scenarios],
        "inputs": asdict(result.inputs),
        "profile_notes": list(profile.notes),
    }


def render_markdown(doc: dict) -> str:
    f, o, t = doc["financing"], doc["operating"], doc["target_price"]
    cur = "EUR" if doc["market"] != "CH" else "CHF"
    lines = [
        f"# Screening {doc['listing_id']} – **{doc['outcome'].upper()}** (Score {doc['score']})",
        "",
        f"Markt: {doc['profile']} · Mandat: {doc['mandate']} · Datenqualität: {doc['data_quality']['weakest_status']}",
        "",
        "## Begründung",
        *[f"- {r}" for r in doc["reasons"]],
        "",
        "## Kennzahlen",
        "| Kennzahl | Wert |",
        "|---|---:|",
        f"| Gesamtinvestition | {f['total_investment']:,.0f} {cur} |",
        f"| Eigenkapital eingesetzt / Darlehen | {f['equity_used']:,.0f} / {f['loan']:,.0f} |",
        f"| Rate monatlich | {f['monthly_payment']:,.0f} |",
        f"| Beleihung | {f['ltv']:.1%} |",
        f"| Cashflow monatlich | **{o['cash_flow']:,.0f}** |",
        f"| Stress-Cashflow | {doc['stress_cash_flow']:,.0f} |",
        f"| Bruttorendite / Nettorendite | {o['gross_yield']:.2%} / {o['net_yield']:.2%} |",
        f"| DSCR | {o['dscr']:.2f} |" if o["dscr"] is not None else "| DSCR | – (kein Darlehen) |",
        f"| Zielpreis ({t['binding']}) | **{t['target']:,.0f}** |",
        "",
        "## Szenarien (Gewinn bei Verkauf, nominal, vor Steuern)",
        "| Szenario | 5 J | 10 J | 15 J |",
        "|---|---:|---:|---:|",
    ]
    by = {}
    for s in doc["scenarios"]:
        by.setdefault(s["name"], {})[s["horizon_years"]] = s["profit"]
    for name, vals in by.items():
        lines.append(f"| {name} | " + " | ".join(f"{vals.get(h, float('nan')):,.0f}" for h in (5, 10, 15)) + " |")
    if doc["watch_triggers"]:
        lines += ["", "## Beobachten – Trigger", *[f"- {k}: {v}" for k, v in doc["watch_triggers"].items()]]
    rf = doc["red_flags"]
    if rf["risks"]:
        lines += ["", "## Festgestellte Risiken", *[f"- **{r['severity']}** {r['id']}: {r['finding']}" for r in rf["risks"]]]
    if rf["open"]:
        lines += ["", "## Offene Prüfpunkte (vom Menschen zu beantworten)", *[f"- [{o['severity_if_risk']}] {o['question']}" for o in rf["open"]]]
    if doc["lints"]:
        lines += ["", "## Plausibilitätshinweise", *[f"- {w}" for w in doc["lints"]]]
    lines += ["", "## Hinweise Marktprofil", *[f"- {n}" for n in doc["profile_notes"]]]
    return "\n".join(lines) + "\n"
