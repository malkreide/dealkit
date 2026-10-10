"""Market profiles: per-market cost defaults, financing rules and notes.

A profile turns a validated listing plus the mandate into ``model.Inputs``.
DE is the reference implementation (the Kompass model was built for it).
CH and the Balkan profiles are deliberately thin and flagged as such: their
conversion logic is documented, but every default is an *assumption* until a
source is attached in the listing.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .model import Inputs


def _v(listing: dict, *path, default=None):
    """Read an evidenced value: returns .value or default."""
    node = listing
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    if isinstance(node, dict) and "value" in node:
        return node["value"] if node["value"] is not None else default
    return node if node is not None else default


@dataclass(frozen=True)
class MarketProfile:
    code: str
    name: str
    currency: str
    financing: str  # "leveraged" | "cash"
    defaults: dict
    notes: tuple[str, ...]
    build_inputs: Callable[[dict, dict, MarketProfile], Inputs]


def _common(listing: dict, mandate: dict, prof: MarketProfile, rent_override: float | None = None) -> Inputs:
    d = {**prof.defaults, **mandate.get("financing_defaults", {})}
    capital = mandate["capital"]
    strategy = mandate.get("strategy", {})
    limits = mandate.get("limits", {})
    commission = _v(listing, "object", "buyer_commission_rate", default=d.get("buyer_commission", 0.0))
    non_rec = _v(listing, "operating", "non_recoverable_costs_monthly", default=d.get("non_recoverable_costs_monthly", 100.0))
    return Inputs(
        purchase_price=float(_v(listing, "core", "purchase_price", default=0.0)),
        living_area_m2=float(_v(listing, "core", "living_area_m2", default=0.0)),
        monthly_rent=float(rent_override if rent_override is not None else _v(listing, "core", "monthly_rent", default=0.0)),
        equity_available=float(capital["equity_available"]),
        liquidity_reserve=float(capital["liquidity_reserve"]),
        transfer_tax=d.get("transfer_tax", 0.0),
        notary_land_registry=d.get("notary_land_registry", 0.0),
        buyer_commission=float(commission),
        renovation_one_off=float(_v(listing, "object", "renovation_need", default=0.0) or 0.0),
        interest_rate=d.get("interest_rate", 0.04),
        initial_amortisation=d.get("initial_amortisation", 0.02),
        fixed_rate_years=int(d.get("fixed_rate_years", 10)),
        follow_up_interest_rate=d.get("follow_up_interest_rate", 0.055),
        non_recoverable_costs_monthly=float(non_rec),
        maintenance_per_m2_monthly=d.get("maintenance_per_m2_monthly", 1.5),
        vacancy_rate=d.get("vacancy_rate", 0.03),
        value_growth=d.get("value_growth", 0.02),
        rent_growth=d.get("rent_growth", 0.015),
        cost_growth=d.get("cost_growth", 0.02),
        selling_costs=d.get("selling_costs", 0.03),
        max_ltv=limits.get("max_ltv", d.get("max_ltv", 0.8)),
        target_gross_yield=strategy.get("target_gross_yield", d.get("target_gross_yield", 0.045)),
    )


def _build_de(listing, mandate, prof):
    return _common(listing, mandate, prof)


def _build_ch(listing, mandate, prof):
    # CH: 75 % max LTV, mandatory amortisation to 2/3 within 10 years (~1 %/a),
    # banks test affordability at a calculatory 5 % on the full loan. The
    # Kompass annuity model is a simplification of the CH two-tranche system.
    return _common(listing, mandate, prof)


def _build_cash_str(listing, mandate, prof):
    """AL/ME coast: cash purchase, short-term rental converted to a monthly
    long-term equivalent: ADR * occupancy * 30.4 * (1 - mgmt - platform).

    If the listing already carries core.monthly_rent (status geschaetzt),
    that wins; otherwise derive it from operating.short_term_rental.
    """
    rent = _v(listing, "core", "monthly_rent")
    if not rent:
        adr = _v(listing, "operating", "short_term_rental", "average_daily_rate", default=0.0)
        occ = _v(listing, "operating", "short_term_rental", "occupancy_rate", default=0.0)
        mgmt = _v(listing, "operating", "short_term_rental", "management_fee_rate", default=prof.defaults["management_fee_rate"])
        plat = _v(listing, "operating", "short_term_rental", "platform_fee_rate", default=prof.defaults["platform_fee_rate"])
        rent = float(adr) * float(occ) * 30.4 * (1 - float(mgmt) - float(plat))
    # Cash deal: no loan if equity covers the investment; otherwise the engine
    # shows the financing gap, which is itself a finding (no bank will close it).
    return _common(listing, mandate, prof, rent_override=float(rent))


PROFILES: dict[str, MarketProfile] = {
    "DE": MarketProfile(
        code="DE",
        name="Deutschland – fremdfinanziertes Buy-and-hold (Kompass-Referenz)",
        currency="EUR",
        financing="leveraged",
        defaults=dict(
            transfer_tax=0.06,  # varies 3.5–6.5 % by Bundesland; Sachsen 5.5 % since 2023
            notary_land_registry=0.02,
            buyer_commission=0.0,
            interest_rate=0.04,
            initial_amortisation=0.02,
            fixed_rate_years=10,
            follow_up_interest_rate=0.055,
            non_recoverable_costs_monthly=100.0,
            maintenance_per_m2_monthly=1.5,
            vacancy_rate=0.03,
            value_growth=0.02,
            rent_growth=0.015,
            cost_growth=0.02,
            selling_costs=0.03,
            max_ltv=0.80,
            target_gross_yield=0.045,
        ),
        notes=(
            "Grunderwerbsteuer je Bundesland setzen (Sachsen 5.5 %).",
            "Instandhaltungsrücklage der WEG nicht doppelt ansetzen (Hausgeld vs. maintenance_per_m2).",
            "Mietpreisbremse / Kappungsgrenze prüfen, bevor eine Zielmiete angesetzt wird.",
            "EPBD/GEG: Energieklasse F–H als Capex-Risiko in renovation_need abbilden.",
            "Spekulationsfrist 10 Jahre: Verkauf vorher ist steuerpflichtig (Deinvest-Modul).",
            "Doppelter Schuldzinsenabzug CH/DE möglich – steuerlich prüfen lassen.",
        ),
        build_inputs=_build_de,
    ),
    "CH": MarketProfile(
        code="CH",
        name="Schweiz – Stockwerkeigentum/Rendite (STUB: Annahmen, nicht kalibriert)",
        currency="CHF",
        financing="leveraged",
        defaults=dict(
            transfer_tax=0.0,  # Kanton ZH: keine Handänderungssteuer; Notariat/Grundbuch ~0.2–0.3 %
            notary_land_registry=0.003,
            buyer_commission=0.0,
            interest_rate=0.02,
            initial_amortisation=0.01,  # 2/3 Belehnung innert 10 Jahren bei Renditeobjekten
            fixed_rate_years=10,
            follow_up_interest_rate=0.035,
            non_recoverable_costs_monthly=150.0,
            maintenance_per_m2_monthly=1.0,
            vacancy_rate=0.02,
            value_growth=0.015,
            rent_growth=0.01,
            cost_growth=0.015,
            selling_costs=0.02,
            max_ltv=0.75,
            target_gross_yield=0.035,
        ),
        notes=(
            "Banken rechnen Tragbarkeit mit kalkulatorischem Zins 5 % und 15 % Nebenkosten vom Nettomietertrag – nicht im Modell.",
            "2./3. Säule nicht als Eigenkapital für reine Renditeobjekte einsetzbar.",
            "Grundstückgewinnsteuer ZH mit Haltedauer-Rabatt (Deinvest-Modul).",
            "Neubewertung Liegenschaften ZH 2026 → höhere Vermögenssteuer.",
            "Für CH ist DCF (Diskontsatz 3.5–5.5 %) die übliche Bewertung; Annuitätenmodell ist Näherung.",
        ),
        build_inputs=_build_ch,
    ),
    "AL": MarketProfile(
        code="AL",
        name="Albanien – Cash-Kauf, Kurzzeitvermietung Küste (STUB: Annahmen)",
        currency="EUR",
        financing="cash",
        defaults=dict(
            transfer_tax=0.0,  # keine Grunderwerbsteuer auf Gebäude (Käufer); Verkäufer zahlt 15 % Gewinnsteuer
            notary_land_registry=0.02,
            buyer_commission=0.02,
            interest_rate=0.0,
            initial_amortisation=0.0,
            fixed_rate_years=0,
            follow_up_interest_rate=0.0,
            non_recoverable_costs_monthly=80.0,
            maintenance_per_m2_monthly=1.0,
            vacancy_rate=0.0,  # vacancy is inside occupancy_rate for STR
            value_growth=0.03,
            rent_growth=0.02,
            cost_growth=0.03,
            selling_costs=0.03,
            max_ltv=0.0,
            target_gross_yield=0.07,
            management_fee_rate=0.25,
            platform_fee_rate=0.03,
        ),
        notes=(
            "Nur Cash: CH-Banken beleihen keine albanischen Objekte. Lex-Koller-Umgehungsrisiko bei Auslandsfinanzierung > 80 %.",
            "Çertifikata e Pronësisë und Katastereintrag (ASHK) sind Blocker-Checks, keine Score-Punkte.",
            "Erdbebenstandard nach 2019 prüfen (Statik).",
            "Mietsteuer 15 %; Preise in EUR gehandelt, Lek-Risiko bei lokalen Kosten.",
            "GwG: Source-of-Funds-Dossier ab dem ersten Transfer aufbauen (Rückführung nach CH).",
            "Wachstumszahlen aus Makler-/Residency-Quellen sind 'makler', nicht 'amtlich'.",
        ),
        build_inputs=_build_cash_str,
    ),
    "ME": MarketProfile(
        code="ME",
        name="Montenegro – Cash-Kauf, Küste, EUR (STUB: Annahmen)",
        currency="EUR",
        financing="cash",
        defaults=dict(
            transfer_tax=0.03,  # progressiv 3–6 %
            notary_land_registry=0.01,
            buyer_commission=0.03,
            interest_rate=0.0,
            initial_amortisation=0.0,
            fixed_rate_years=0,
            follow_up_interest_rate=0.0,
            non_recoverable_costs_monthly=80.0,
            maintenance_per_m2_monthly=1.0,
            vacancy_rate=0.0,
            value_growth=0.03,
            rent_growth=0.02,
            cost_growth=0.03,
            selling_costs=0.03,
            max_ltv=0.0,
            target_gross_yield=0.06,
            management_fee_rate=0.25,
            platform_fee_rate=0.03,
        ),
        notes=(
            "Flat Tax 15 % auf Mieteinkünfte und Veräusserungsgewinne.",
            "Saisonalität: Auslastung ausserhalb Mai–September gegen null – season_months pflegen.",
            "'EU-Beitritt 2028, +50–70 %' ist eine Makleraussage; als 'annahme' führen.",
        ),
        build_inputs=_build_cash_str,
    ),
    "RS": MarketProfile(
        code="RS",
        name="Serbien – Belgrad, Langzeitvermietung, Cash (STUB: Annahmen)",
        currency="EUR",
        financing="cash",
        defaults=dict(
            transfer_tax=0.025,
            notary_land_registry=0.01,
            buyer_commission=0.02,
            interest_rate=0.0,
            initial_amortisation=0.0,
            fixed_rate_years=0,
            follow_up_interest_rate=0.0,
            non_recoverable_costs_monthly=60.0,
            maintenance_per_m2_monthly=1.0,
            vacancy_rate=0.05,
            value_growth=0.03,
            rent_growth=0.02,
            cost_growth=0.03,
            selling_costs=0.03,
            max_ltv=0.0,
            target_gross_yield=0.05,
        ),
        notes=(
            "Eigentum entsteht erst mit Katastereintrag (RGZ); clausula intabulandi vom Verkäufer nötig.",
            "upotrebna dozvola (Nutzungsbewilligung) und Legalisierung sind Blocker-Checks.",
            "Restitutionsansprüche früherer Eigentümer anwaltlich prüfen.",
            "Vorvertrag (predugovor) + kapara 10 % üblich.",
        ),
        build_inputs=_build_de,
    ),
}


def get_profile(code: str) -> MarketProfile:
    try:
        return PROFILES[code]
    except KeyError as e:
        raise ValueError(f"unknown market profile {code!r}; known: {sorted(PROFILES)}") from e
