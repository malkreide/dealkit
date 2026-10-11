"""Extraction scaffold and eval (stage 1). All data under tests/data/ is synthetic."""

import copy
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from dealkit.cli import main
from dealkit.extraction import (
    CORE_FIELDS,
    EvalReport,
    compare,
    evaluate_dir,
    market_from_filename,
    normalize,
    numbers_in,
    quote_in_source,
    read_source_text,
    scaffold,
    within_tolerance,
)
from dealkit.redflags import checklist
from dealkit.schema import validate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "data" / "extraction"
SCRIPT = ROOT / "scripts" / "eval_extraction.py"

SOURCE = "SYNTHETISCH\nKaufpreis: 175.000 EUR\nWohnfläche: ca. 58,5 m²\nNettokaltmiete: 600 EUR\nBaujahr 1912\n"


def ev(value, status="belegt", quote=None, kind="portal"):
    src = {"kind": kind}
    if quote is not None:
        src["quote"] = quote
    return {"value": value, "status": status, "source": src}


@pytest.fixture
def gold():
    return {
        "id": "de-synth",
        "market": "DE",
        "captured_at": "2026-10-11T08:00:00Z",
        "source": {"kind": "portal"},
        "core": {
            "purchase_price": ev(175000, quote="Kaufpreis: 175.000 EUR"),
            "living_area_m2": ev(58.5, quote="Wohnfläche: ca. 58,5 m²"),
            "monthly_rent": ev(600, quote="Nettokaltmiete: 600 EUR"),
        },
    }


@pytest.fixture
def pred(gold):
    return copy.deepcopy(gold)


def classes(result, severity=None):
    return sorted(f.klass for f in result.findings if severity is None or f.severity == severity)


# --- text helpers -----------------------------------------------------------


def test_normalize_collapses_whitespace_and_nbsp():
    assert normalize("Kaufpreis:  175.000\n\tEUR ") == "Kaufpreis: 175.000 EUR"
    assert normalize("Woh­nfläche") == "Wohnfläche"


def test_quote_in_source_is_whitespace_tolerant_but_verbatim():
    assert quote_in_source("Kaufpreis: 175.000 EUR", SOURCE)
    assert quote_in_source("Kaufpreis:\n175.000   EUR", SOURCE)
    assert not quote_in_source("Kaufpreis: 175000 EUR", SOURCE)  # reformatted number
    assert not quote_in_source("Preis: 175.000 EUR", SOURCE)  # paraphrased
    assert not quote_in_source("", SOURCE)
    assert not quote_in_source("   ", SOURCE)
    assert not quote_in_source(None, SOURCE)


@pytest.mark.parametrize(
    "quote,value",
    [
        ("Kaufpreis: 175.000 EUR", 175000),
        ("Wohnfläche: ca. 58,5 m²", 58.5),
        ("CHF 1'250'000.–", 1250000),
        ("Çmimi: 52 000 €", 52000),
        ("€ 85,000", 85000),
        ("Preis 1,25 Mio. CHF", 1250000),
        ("3 Zimmer 175.000", 175000),
    ],
)
def test_numbers_in_reads_common_formats(quote, value):
    assert any(within_tolerance(n, value) for n in numbers_in(quote))


def test_within_tolerance_is_one_percent():
    assert within_tolerance(1010, 1000)
    assert within_tolerance(990, 1000)
    assert not within_tolerance(1011, 1000)
    assert within_tolerance(0, 0) and not within_tolerance(1, 0)


# --- field comparison -------------------------------------------------------


def test_identical_is_correct(gold, pred):
    r = compare("x", gold, pred, SOURCE)
    assert r.correct and r.gate_ok and classes(r) == []


def test_value_within_tolerance_is_correct(gold, pred):
    pred["core"]["purchase_price"]["value"] = 176000  # +0.57 %
    assert compare("x", gold, pred, SOURCE).correct


def test_value_outside_tolerance(gold, pred):
    pred["core"]["purchase_price"]["value"] = 178000  # +1.7 %
    r = compare("x", gold, pred, SOURCE)
    assert not r.correct and not r.fields["purchase_price"]
    assert classes(r, "fehler") == ["wert_abweichung"]


@pytest.mark.parametrize(
    "field,value,klass",
    [("monthly_rent", 7200, "faktor_12"), ("purchase_price", 175, "faktor_1000"), ("living_area_m2", 585, "faktor_10")],
)
def test_deviation_factor_classes(gold, pred, field, value, klass):
    pred["core"][field]["value"] = value
    assert klass in classes(compare("x", gold, pred, SOURCE))


def test_status_must_match_exactly(gold, pred):
    pred["core"]["monthly_rent"]["status"] = "geschaetzt"
    r = compare("x", gold, pred, SOURCE)
    assert not r.fields["monthly_rent"] and classes(r) == ["status_abweichung"]


def test_conflict_ignored_when_gold_is_missing(gold, pred):
    gold["core"]["monthly_rent"] = ev(None, "fehlend", kind="portal")
    r = compare("x", gold, pred, SOURCE)
    assert not r.fields["monthly_rent"] and classes(r) == ["konflikt_uebergangen"]


def test_both_missing_is_correct(gold, pred):
    gold["core"]["monthly_rent"] = pred["core"]["monthly_rent"] = ev(None, "fehlend")
    assert compare("x", gold, pred, SOURCE).correct


def test_currency_must_match(gold, pred):
    gold["core"]["currency"] = "BAM"
    gold["core"]["monthly_rent"] = pred["core"]["monthly_rent"] = ev(None, "fehlend")
    r = compare("x", gold, pred, SOURCE)  # pred currency defaults to EUR
    assert classes(r) == ["waehrung_abweichung"]
    assert not r.fields["purchase_price"] and r.fields["monthly_rent"] and r.fields["living_area_m2"]


def test_value_missed(gold, pred):
    pred["core"]["living_area_m2"] = ev(None, "fehlend")
    assert classes(compare("x", gold, pred, SOURCE)) == ["wert_verpasst"]


def test_missing_prediction_fails_every_field(gold):
    r = compare("x", gold, None, SOURCE)
    assert not r.correct and not any(r.fields.values()) and classes(r) == ["pred_fehlt"]


def test_string_value_is_a_type_error(gold, pred):
    pred["core"]["monthly_rent"]["value"] = "600"  # schema allows strings, the eval does not
    r = compare("x", gold, pred, SOURCE)
    assert r.schema_ok and classes(r) == ["wert_typ"] and not r.correct


def test_schema_invalid_prediction_is_not_correct(gold, pred):
    pred["market"] = "FR"
    r = compare("x", gold, pred, SOURCE)
    assert all(r.fields.values()) and not r.schema_ok and not r.correct
    assert classes(r) == ["schema_ungueltig"]


# --- hard gate --------------------------------------------------------------


def test_gate_quote_not_in_source(gold, pred):
    pred["core"]["purchase_price"]["source"]["quote"] = "Preis: 175.000 EUR"
    r = compare("x", gold, pred, SOURCE)
    assert classes(r, "gate") == ["zitat_nicht_gefunden"]
    assert all(r.fields.values()) and not r.correct  # values right, but not trustworthy


def test_gate_belegt_without_quote(gold, pred):
    del pred["core"]["monthly_rent"]["source"]["quote"]
    r = compare("x", gold, pred, SOURCE)
    assert "zitat_fehlt" in classes(r, "gate") and not r.schema_ok


def test_gate_applies_to_non_core_values(gold, pred):
    pred["object"] = {"year_built": ev(1921, quote="Baujahr 1921")}
    r = compare("x", gold, pred, SOURCE)
    assert [f.path for f in r.findings if f.severity == "gate"] == ["object.year_built"]


def test_non_belegt_quotes_are_not_gated(gold, pred):
    pred["core"]["monthly_rent"] = ev(650, "geschaetzt", quote="erzielbare Miete 650 EUR")
    gold["core"]["monthly_rent"] = ev(650, "geschaetzt")
    assert compare("x", gold, pred, SOURCE).gate_ok


def test_value_not_in_quote_is_a_warning_only(gold, pred):
    pred["core"]["monthly_rent"]["source"]["quote"] = "Kaufpreis: 175.000 EUR"
    r = compare("x", gold, pred, SOURCE)
    assert classes(r) == ["wert_nicht_im_zitat"] and r.correct


def test_broken_gold_is_a_setup_error(gold, pred):
    gold["core"]["purchase_price"]["source"]["quote"] = "Kaufpreis 175000"
    r = compare("x", gold, pred, SOURCE)
    assert classes(r, "setup") == ["gold_zitat_nicht_gefunden"]
    assert EvalReport("d", [r]).exit_code() == 2


def test_pii_in_gold_is_flagged(gold, pred):
    gold["notes"] = "Verkäuferin erreichbar unter 044 123 45 67"
    assert "pii_verdacht" in classes(compare("x", gold, pred, SOURCE), "warnung")


def test_prices_and_postcodes_are_not_pii(gold, pred):
    gold["address"] = {"postal_code": "04317", "city": "Leipzig"}
    gold["notes"] = "Kaufpreis 1 250 000, Baujahr 2021-2022"
    assert "pii_verdacht" not in classes(compare("x", gold, pred, SOURCE))


# --- directory run and exit codes --------------------------------------------


def test_evaluate_dir_pass():
    rep = evaluate_dir(DATA / "pass")
    assert [r.name for r in rep.results] == ["al-synth-marreveshje", "de-synth-korrekt"]
    assert rep.fixture_rate == 1.0 and rep.exit_code() == 0 and rep.exit_code(0.9) == 0


def test_evaluate_dir_mixed():
    rep = evaluate_dir(DATA / "mixed")
    by_name = {r.name: r for r in rep.results}
    assert set(by_name) == {"al-synth-uebersetzt", "de-synth-jahresmiete", "de-synth-ohne-pred"}
    assert rep.skipped == [("ch-synth-ohne-gold", "kein Gold (.gold.json)")]
    assert classes(by_name["al-synth-uebersetzt"], "gate") == ["zitat_nicht_gefunden"]
    assert classes(by_name["de-synth-jahresmiete"]) == ["konflikt_uebergangen", "wert_nicht_im_zitat"]
    assert classes(by_name["de-synth-ohne-pred"]) == ["pred_fehlt"]
    assert rep.fixture_rate == 0.0 and rep.exit_code() == 1


def test_exit_code_min_rate():
    rep = evaluate_dir(DATA / "pass")
    rep.results[0].fields["purchase_price"] = False
    assert rep.exit_code() == 0 and rep.exit_code(0.9) == 1


def test_empty_directory_exits_2(tmp_path):
    assert evaluate_dir(tmp_path).exit_code() == 2


@pytest.mark.parametrize("subdir,code", [("pass", 0), ("mixed", 1)])
def test_script_exit_codes(subdir, code):
    proc = subprocess.run([sys.executable, str(SCRIPT), str(DATA / subdir)], capture_output=True, text=True)
    assert proc.returncode == code, proc.stdout + proc.stderr
    assert "Gesamtquote" in proc.stdout and "Hartes Gate" in proc.stdout


def test_script_json_output():
    proc = subprocess.run([sys.executable, str(SCRIPT), str(DATA / "mixed"), "--json"], capture_output=True, text=True)
    doc = json.loads(proc.stdout)
    assert doc["gate_ok"] is False and len(doc["fixtures"]) == 3


# --- PDF sources ---------------------------------------------------------------


def _minimal_pdf(lines: list[str]) -> bytes:
    """A one-page PDF with a text layer (Helvetica, ASCII only)."""
    text = " T* ".join(f"({line})Tj" for line in lines)
    stream = f"BT /F1 12 Tf 14 TL 72 720 Td {text} ET".encode()
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


def test_pdf_source_is_read(tmp_path):
    pytest.importorskip("pypdf")
    pdf = tmp_path / "de-synth-pdf.pdf"
    pdf.write_bytes(_minimal_pdf(["SYNTHETISCH", "Kaufpreis: 175.000 EUR"]))
    assert quote_in_source("Kaufpreis: 175.000 EUR", read_source_text(pdf))


def test_txt_wins_over_pdf(tmp_path, gold):
    pytest.importorskip("pypdf")
    (tmp_path / "de-synth.pdf").write_bytes(_minimal_pdf(["nichts"]))
    (tmp_path / "de-synth.txt").write_text(SOURCE, encoding="utf-8")
    (tmp_path / "de-synth.gold.json").write_text(json.dumps(gold), encoding="utf-8")
    (tmp_path / "de-synth.pred.json").write_text(json.dumps(gold), encoding="utf-8")
    assert evaluate_dir(tmp_path).exit_code() == 0


# --- scaffold ------------------------------------------------------------------

NOW = datetime(2026, 10, 11, 9, 30, tzinfo=UTC)


@pytest.mark.parametrize(
    "name,market",
    [("de-leipzig-01.txt", "DE"), ("AL-vlore-02.pdf", "AL"), ("ch-zh-03.txt", "CH"), ("at-graz-07.txt", "AT"), ("bg-plovdiv-18.txt", "BG"), ("leipzig.txt", None), ("deu-x.txt", None)],
)
def test_market_from_filename(name, market):
    assert market_from_filename(name) == market


def test_scaffold_is_valid_and_complete():
    doc = scaffold("fixtures/listings/de-leipzig-reudnitz-01.txt", object_type="wohnung", now=NOW)
    assert validate(doc, "listing") == []
    assert doc["id"] == "de-leipzig-reudnitz-01" and doc["market"] == "DE"
    assert doc["captured_at"] == "2026-10-11T09:30:00Z"
    assert doc["source"]["documents"] == ["de-leipzig-reudnitz-01.txt"]
    assert all(doc["core"][k]["status"] == "fehlend" and doc["core"][k]["value"] is None for k in CORE_FIELDS)
    assert doc["object"]["type"] == "wohnung" and doc["object"]["year_built"]["status"] == "fehlend"
    assert [rf["id"] for rf in doc["red_flags"]] == [c.id for c in checklist("DE", "wohnung")]
    assert {rf["state"] for rf in doc["red_flags"]} == {"offen"}


def test_scaffold_currency_and_market_override():
    assert scaffold("ch-zh-01.txt", now=NOW)["core"]["currency"] == "CHF"
    assert scaffold("whatever.txt", market="AL", now=NOW)["market"] == "AL"
    with pytest.raises(ValueError, match="Präfix"):
        scaffold("whatever.txt", now=NOW)


def test_scaffold_never_violates_the_gate(gold):
    gold["core"]["monthly_rent"] = ev(None, "fehlend")
    r = compare("x", gold, scaffold("de-x.txt", now=NOW), SOURCE)
    assert r.gate_ok and r.fields["monthly_rent"] and not r.fields["purchase_price"]


def test_cli_extract(tmp_path):
    src = tmp_path / "al-vlore-01.txt"
    src.write_text("SYNTHETISCH", encoding="utf-8")
    out = tmp_path / "al-vlore-01.pred.json"
    runner = CliRunner()
    res = runner.invoke(main, ["extract", str(src), "--out", str(out), "--type", "wohnung", "--source-kind", "makler"])
    assert res.exit_code == 0, res.output
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["market"] == "AL" and doc["core"]["purchase_price"]["source"]["kind"] == "makler"
    assert runner.invoke(main, ["extract", str(src), "--out", str(out)]).exit_code != 0  # no silent overwrite
    assert runner.invoke(main, ["extract", str(src), "--out", str(out), "--force"]).exit_code == 0


def test_cli_extract_unknown_prefix(tmp_path):
    src = tmp_path / "inserat.txt"
    src.write_text("SYNTHETISCH", encoding="utf-8")
    res = CliRunner().invoke(main, ["extract", str(src)])
    assert res.exit_code == 2 and "Präfix" in res.output


# --- extraction-only markets ---------------------------------------------------


@pytest.mark.parametrize("name,market,currency", [("at-graz-07.txt", "AT", "EUR"), ("ba-sarajevo-16.txt", "BA", "BAM"), ("mk-skopje-12.txt", "MK", "EUR")])
def test_extraction_only_market_scaffold_validates(name, market, currency):
    doc = scaffold(name, now=NOW)
    assert doc["market"] == market and doc["core"]["currency"] == currency
    assert validate(doc, "listing") == []
    assert [rf["id"] for rf in doc["red_flags"]] == [c.id for c in checklist(market)]  # common checks only


def test_screen_refuses_extraction_only_market(tmp_path, gold):
    from dealkit.pipeline import screen
    from dealkit.schema import load

    gold["market"] = "AT"
    mandate = load(ROOT / "examples" / "mandate.example.yaml")
    with pytest.raises(ValueError, match="extraction-only"):
        screen(gold, mandate)
    path = tmp_path / "at.json"
    path.write_text(json.dumps(gold), encoding="utf-8")
    res = CliRunner().invoke(main, ["screen", str(path), "-m", str(ROOT / "examples" / "mandate.example.yaml")])
    assert res.exit_code == 1 and "extraction-only" in res.output
