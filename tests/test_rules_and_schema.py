import copy
from pathlib import Path

import pytest

from dealkit.model import Inputs, assess
from dealkit.pipeline import screen
from dealkit.redflags import checklist, evaluate
from dealkit.rules import kompass_decision, kompass_score
from dealkit.schema import lint_listing, load, validate

EX = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def mandate():
    return load(EX / "mandate.example.yaml")


@pytest.fixture
def leipzig():
    return load(EX / "listing.leipzig.json")


@pytest.fixture
def vlore():
    return load(EX / "listing.vlore.json")


# --- schema ---------------------------------------------------------------


def test_examples_validate(mandate, leipzig, vlore):
    assert validate(mandate, "mandate") == []
    assert validate(leipzig, "listing") == []
    assert validate(vlore, "listing") == []


def test_belegt_requires_quote(leipzig):
    bad = copy.deepcopy(leipzig)
    del bad["core"]["purchase_price"]["source"]["quote"]
    assert any("quote" in e for e in validate(bad, "listing"))


def test_fehlend_requires_null_value(leipzig):
    bad = copy.deepcopy(leipzig)
    bad["core"]["monthly_rent"]["status"] = "fehlend"
    assert validate(bad, "listing")  # value 600 with status fehlend is invalid


def test_lint_flags_yearly_rent(leipzig):
    bad = copy.deepcopy(leipzig)
    bad["core"]["monthly_rent"]["value"] = 7200
    assert any("Miete/m²" in w for w in lint_listing(bad))


# --- kompass v1 backtest ----------------------------------------------------


def test_kompass_example_decision():
    a = assess(Inputs(purchase_price=300_000, living_area_m2=60, monthly_rent=1_200))
    score = kompass_score(a, confirmed_checks=5)
    # LTV 81.3 % > 80 % → 'zu diesem Preis nicht passend' once everything is confirmed
    assert kompass_decision(a, core_confirmed=True, confirmed_checks=5, score=score) == "zu_diesem_preis_nicht_passend"
    assert kompass_decision(a, core_confirmed=False, confirmed_checks=5, score=score) == "weitere_pruefung_noetig"


def test_kompass_score_components():
    a = assess(Inputs(purchase_price=180_000, living_area_m2=60, monthly_rent=1_200))
    # positive cash flow and stress cash flow, yield 8 %, LTV within limit → all finance points
    assert kompass_score(a, confirmed_checks=0) == 80
    assert kompass_score(a, confirmed_checks=5) == 100


# --- dealkit v1 -------------------------------------------------------------


def test_missing_core_blocks(leipzig, mandate):
    bad = copy.deepcopy(leipzig)
    bad["core"]["monthly_rent"] = {"value": None, "status": "fehlend", "source": {"kind": "annahme"}}
    assert screen(bad, mandate)["outcome"] == "daten_vervollstaendigen"


def test_blocker_overrides_finance(leipzig, mandate):
    bad = copy.deepcopy(leipzig)
    bad["core"]["purchase_price"]["value"] = 120_000  # would be 'pruefen' financially
    bad["red_flags"].append({"id": "title", "state": "geprueft_risiko", "severity": "blocker", "finding": "Vorkaufsrecht Gemeinde"})
    doc = screen(bad, mandate)
    assert doc["outcome"] == "verwerfen"
    assert any("Blocker" in r for r in doc["reasons"])


def test_watch_has_price_trigger(leipzig, mandate):
    doc = screen(leipzig, mandate)
    assert doc["outcome"] == "beobachten"
    assert doc["watch_triggers"]["price_at_or_below"] == round(doc["target_price"]["target"])
    assert doc["watch_triggers"]["price_drop_pct"] == 0.05


def test_hopeless_gap_discards(leipzig, mandate):
    bad = copy.deepcopy(leipzig)
    bad["core"]["purchase_price"]["value"] = 260_000
    assert screen(bad, mandate)["outcome"] == "verwerfen"


def test_cash_str_profile(vlore, mandate):
    doc = screen(vlore, mandate)
    assert doc["financing"]["loan"] == 0
    assert doc["operating"]["dscr"] is None
    assert doc["data_quality"]["weakest_status"] == "angenommen"
    assert "monthly_rent" in doc["data_quality"]["critical_assumed"]
    assert doc["red_flags"]["open_blockers"]  # ownership + legalisation still open


def test_market_outside_mandate_is_never_pruefen(leipzig, mandate):
    m = copy.deepcopy(mandate)
    m["markets"] = [x for x in m["markets"] if x["code"] != "DE"]
    lst = copy.deepcopy(leipzig)
    lst["core"]["purchase_price"]["value"] = 120_000
    doc = screen(lst, m)
    assert doc["outcome"] != "pruefen"


# --- red flags --------------------------------------------------------------


def test_checklist_filters_by_type():
    ids = {c.id for c in checklist("DE", "wohnung")}
    assert "weg_minutes" in ids and "new_build" not in ids
    assert "new_build" in {c.id for c in checklist("DE", "neubau_projekt")}


def test_evaluate_reports_max_severity(vlore):
    v = copy.deepcopy(vlore)
    v["red_flags"].append({"id": "str_permit", "state": "geprueft_risiko", "severity": "hoch", "finding": "keine Registrierung"})
    r = evaluate(v)
    assert r["max_risk_severity"] == "hoch"
    assert "ownership_certificate" in r["open_blockers"]
